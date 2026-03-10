from __future__ import annotations

import json
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Optional

import pretty_midi
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

APP_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = APP_ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AI MIDI MVP", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"ok": True}


def _transcribe_with_basic_pitch(audio_path: Path, midi_out_path: Path) -> dict:
    try:
        from basic_pitch.inference import predict
    except Exception as exc:
        raise RuntimeError(
            "basic-pitch 未安装。请在 requirements 基础上安装 basic-pitch==0.3.0。"
        ) from exc

    model_output, midi_data, note_events = predict(str(audio_path))

    with open(midi_out_path, "wb") as f:
        f.write(midi_data)

    return {
        "raw_notes": len(note_events),
        "model_frames": getattr(model_output, "shape", None),
    }


def _postprocess_midi(
    midi_path: Path,
    profile: str = "balanced",
    snap_grid: Optional[float] = None,
) -> dict:
    midi = pretty_midi.PrettyMIDI(str(midi_path))

    if profile == "conservative":
        min_len = 0.08
        min_vel = 45
    elif profile == "aggressive":
        min_len = 0.03
        min_vel = 20
    else:
        min_len = 0.05
        min_vel = 32

    kept = 0
    removed = 0
    for instrument in midi.instruments:
        new_notes = []
        for n in instrument.notes:
            if (n.end - n.start) < min_len:
                removed += 1
                continue
            if n.velocity < min_vel:
                removed += 1
                continue

            if snap_grid and snap_grid > 0:
                n.start = round(n.start / snap_grid) * snap_grid
                n.end = max(n.start + min_len, round(n.end / snap_grid) * snap_grid)

            new_notes.append(n)
            kept += 1
        instrument.notes = new_notes

    midi.write(str(midi_path))
    return {"kept_notes": kept, "removed_notes": removed, "profile": profile, "snap_grid": snap_grid}


@app.post("/api/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    profile: str = Form("balanced"),
    snap_grid: Optional[float] = Form(None),
):
    if not audio.filename:
        raise HTTPException(status_code=400, detail="audio filename is empty")

    job_id = str(uuid.uuid4())
    safe_name = Path(audio.filename).name

    with tempfile.TemporaryDirectory() as td:
        input_path = Path(td) / safe_name
        with input_path.open("wb") as f:
            shutil.copyfileobj(audio.file, f)

        midi_path = OUTPUT_DIR / f"{job_id}.mid"

        try:
            meta = _transcribe_with_basic_pitch(input_path, midi_path)
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc))

        post_meta = _postprocess_midi(midi_path, profile=profile, snap_grid=snap_grid)

    result = {
        "job_id": job_id,
        "midi_url": f"/api/result/{job_id}",
        "meta": meta,
        "postprocess": post_meta,
    }

    (OUTPUT_DIR / f"{job_id}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return JSONResponse(result)


@app.get("/api/result/{job_id}")
def download_result(job_id: str):
    midi_path = OUTPUT_DIR / f"{job_id}.mid"
    if not midi_path.exists():
        raise HTTPException(status_code=404, detail="result not found")
    return FileResponse(midi_path, filename=f"{job_id}.mid", media_type="audio/midi")
