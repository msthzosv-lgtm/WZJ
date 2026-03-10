from __future__ import annotations

import json
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import librosa
import numpy as np
import pretty_midi
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

APP_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = APP_ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="AI MIDI Local Bundle", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def detect_hardware() -> Dict[str, str]:
    info = {"compute": "cpu", "detail": "Python/NumPy"}
    try:
        import torch  # type: ignore

        if torch.cuda.is_available():
            info["compute"] = "gpu"
            info["detail"] = torch.cuda.get_device_name(0)
        else:
            info["detail"] = "torch installed, CUDA unavailable"
    except Exception:
        pass
    return info


def midi_to_note_json(midi_path: Path) -> List[Dict[str, float]]:
    midi = pretty_midi.PrettyMIDI(str(midi_path))
    notes: List[Dict[str, float]] = []
    for instrument in midi.instruments:
        for n in instrument.notes:
            notes.append(
                {
                    "pitch": int(n.pitch),
                    "start": round(float(n.start), 4),
                    "end": round(float(n.end), 4),
                    "velocity": int(n.velocity),
                }
            )
    notes.sort(key=lambda x: x["start"])
    return notes


def _pyin_notes(
    y: np.ndarray,
    sr: int,
    min_hz: float = 65.4,
    max_hz: float = 1760.0,
) -> List[Tuple[float, float, int, int]]:
    frame_length = 2048
    hop_length = 256
    f0, voiced_flag, _ = librosa.pyin(
        y,
        fmin=min_hz,
        fmax=max_hz,
        sr=sr,
        frame_length=frame_length,
        hop_length=hop_length,
    )

    notes: List[Tuple[float, float, int, int]] = []
    times = librosa.times_like(f0, sr=sr, hop_length=hop_length)

    start_idx = None
    pitches = []
    for i, (f, v) in enumerate(zip(f0, voiced_flag)):
        if v and not np.isnan(f):
            if start_idx is None:
                start_idx = i
                pitches = [f]
            else:
                pitches.append(f)
        else:
            if start_idx is not None and pitches:
                st = float(times[start_idx])
                ed = float(times[i - 1] + hop_length / sr)
                midi_pitch = int(np.clip(np.round(librosa.hz_to_midi(np.median(pitches))), 21, 108))
                velocity = int(min(110, max(45, 45 + len(pitches) // 2)))
                notes.append((st, ed, midi_pitch, velocity))
                start_idx = None
                pitches = []

    if start_idx is not None and pitches:
        st = float(times[start_idx])
        ed = float(times[len(times) - 1] + hop_length / sr)
        midi_pitch = int(np.clip(np.round(librosa.hz_to_midi(np.median(pitches))), 21, 108))
        velocity = int(min(110, max(45, 45 + len(pitches) // 2)))
        notes.append((st, ed, midi_pitch, velocity))

    return notes


def _write_notes_to_midi(notes: List[Tuple[float, float, int, int]], midi_out_path: Path) -> None:
    midi = pretty_midi.PrettyMIDI(initial_tempo=120)
    inst = pretty_midi.Instrument(program=0)
    for st, ed, pitch, vel in notes:
        if ed <= st:
            continue
        inst.notes.append(pretty_midi.Note(velocity=vel, pitch=pitch, start=st, end=ed))
    midi.instruments.append(inst)
    midi.write(str(midi_out_path))


def _transcribe_basic_pitch(audio_path: Path, midi_out_path: Path) -> Dict[str, str]:
    from basic_pitch.inference import predict  # type: ignore

    _, midi_data, note_events = predict(str(audio_path))
    midi_out_path.write_bytes(midi_data)
    return {"engine": "basic_pitch", "raw_notes": str(len(note_events))}


def _transcribe_local_pyin(audio_path: Path, midi_out_path: Path) -> Dict[str, str]:
    y, sr = librosa.load(str(audio_path), sr=22050, mono=True)
    notes = _pyin_notes(y, sr)
    _write_notes_to_midi(notes, midi_out_path)
    return {"engine": "local_pyin", "raw_notes": str(len(notes))}


def _postprocess_midi(midi_path: Path, profile: str, snap_grid: Optional[float]) -> Dict[str, float]:
    midi = pretty_midi.PrettyMIDI(str(midi_path))

    if profile == "clean":
        min_len, min_vel = 0.09, 50
    elif profile == "rich":
        min_len, min_vel = 0.03, 24
    else:
        min_len, min_vel = 0.05, 32

    kept = 0
    removed = 0
    for inst in midi.instruments:
        filtered = []
        for n in inst.notes:
            if (n.end - n.start) < min_len or n.velocity < min_vel:
                removed += 1
                continue
            if snap_grid and snap_grid > 0:
                n.start = max(0.0, round(n.start / snap_grid) * snap_grid)
                n.end = max(n.start + min_len, round(n.end / snap_grid) * snap_grid)
            filtered.append(n)
            kept += 1
        inst.notes = filtered

    midi.write(str(midi_path))
    return {"kept_notes": kept, "removed_notes": removed, "snap_grid": snap_grid or 0.0}


@app.get("/health")
def health() -> Dict[str, Dict[str, str]]:
    engine = "local_pyin"
    try:
        import basic_pitch  # type: ignore  # noqa: F401

        engine = "basic_pitch_or_local_pyin"
    except Exception:
        pass

    return {"ok": {"default_engine": engine, **detect_hardware()}}


@app.post("/api/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    engine: str = Form("auto"),
    profile: str = Form("balanced"),
    snap_grid: Optional[float] = Form(None),
):
    if not audio.filename:
        raise HTTPException(status_code=400, detail="missing filename")

    if profile not in {"clean", "balanced", "rich"}:
        raise HTTPException(status_code=400, detail="profile must be clean|balanced|rich")

    job_id = str(uuid.uuid4())

    with tempfile.TemporaryDirectory() as td:
        in_path = Path(td) / Path(audio.filename).name
        with in_path.open("wb") as f:
            shutil.copyfileobj(audio.file, f)

        midi_path = OUTPUT_DIR / f"{job_id}.mid"
        used_engine = engine

        if engine in {"auto", "basic_pitch"}:
            try:
                meta = _transcribe_basic_pitch(in_path, midi_path)
                used_engine = "basic_pitch"
            except Exception:
                if engine == "basic_pitch":
                    raise HTTPException(status_code=500, detail="basic_pitch unavailable locally")
                meta = _transcribe_local_pyin(in_path, midi_path)
                used_engine = "local_pyin"
        else:
            meta = _transcribe_local_pyin(in_path, midi_path)
            used_engine = "local_pyin"

        pp = _postprocess_midi(midi_path, profile=profile, snap_grid=snap_grid)
        note_json = midi_to_note_json(midi_path)

    result = {
        "job_id": job_id,
        "engine": used_engine,
        "hardware": detect_hardware(),
        "midi_url": f"/api/result/{job_id}",
        "notes": note_json,
        "meta": meta,
        "postprocess": pp,
    }
    (OUTPUT_DIR / f"{job_id}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return JSONResponse(result)


@app.get("/api/result/{job_id}")
def result(job_id: str):
    midi_path = OUTPUT_DIR / f"{job_id}.mid"
    if not midi_path.exists():
        raise HTTPException(status_code=404, detail="job not found")
    return FileResponse(midi_path, filename=f"{job_id}.mid", media_type="audio/midi")
