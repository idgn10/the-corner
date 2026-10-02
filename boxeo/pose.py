"""Extraccion de pose: video -> DataFrame de landmarks por frame (en pixeles), suavizado."""
from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
from mediapipe.tasks.python import BaseOptions, vision

# Landmarks que usamos (indices de MediaPipe Pose). l/r = izquierda/derecha del boxeador.
LANDMARKS = {
    "nose": 0,
    "l_shoulder": 11, "r_shoulder": 12,
    "l_elbow": 13, "r_elbow": 14,
    "l_wrist": 15, "r_wrist": 16,
    "l_hip": 23, "r_hip": 24,
    "l_knee": 25, "r_knee": 26,
    "l_ankle": 27, "r_ankle": 28,
}


def video_info(path, max_height=720, max_seconds=60):
    """fps, tamano de procesado (par, <= max_height) y numero de frames a procesar."""
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError(f"No se puede abrir el video: {path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    if not 1 <= fps <= 240:
        fps = 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    scale = min(1.0, max_height / h) if h else 1.0
    size = (int(w * scale) // 2 * 2, int(h * scale) // 2 * 2)  # H.264 necesita dimensiones pares
    max_frames = int(max_seconds * fps)
    n = min(n, max_frames) if n > 0 else max_frames
    return {"fps": fps, "size": size, "n_frames": n, "max_frames": max_frames}


def iter_frames(path, size, max_frames):
    """Genera frames BGR ya redimensionados a `size`."""
    cap = cv2.VideoCapture(str(path))
    i = 0
    while i < max_frames:
        ok, frame = cap.read()
        if not ok:
            break
        if (frame.shape[1], frame.shape[0]) != size:
            frame = cv2.resize(frame, size, interpolation=cv2.INTER_AREA)
        yield frame
        i += 1
    cap.release()


def extract_landmarks(path, cfg, progress=None):
    """Ejecuta MediaPipe sobre el video. Devuelve (DataFrame crudo, info del video).

    Columnas: frame, t, y para cada landmark <nombre>_x, <nombre>_y (pixeles) y <nombre>_v (visibilidad).
    Puntos con visibilidad baja o frames sin persona quedan como NaN.
    """
    vcfg, pcfg = cfg["video"], cfg["pose"]
    info = video_info(path, vcfg["max_height"], vcfg["max_seconds"])
    fps, (w, h) = info["fps"], info["size"]
    model = Path(pcfg["model"])
    if not model.is_absolute():
        model = Path(__file__).resolve().parent.parent / model
    if not model.exists():
        raise FileNotFoundError(f"Falta el modelo {model}. Ejecuta: python scripts/download_model.py")

    options = vision.PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(model)),
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1,
    )
    rows = []
    with vision.PoseLandmarker.create_from_options(options) as landmarker:
        for i, frame in enumerate(iter_frames(path, info["size"], info["max_frames"])):
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = landmarker.detect_for_video(image, int(i * 1000 / fps))
            row = {"frame": i, "t": i / fps}
            pose = result.pose_landmarks[0] if result.pose_landmarks else None
            for name, idx in LANDMARKS.items():
                if pose is not None and pose[idx].visibility >= pcfg["min_visibility"]:
                    lm = pose[idx]
                    row[f"{name}_x"], row[f"{name}_y"], row[f"{name}_v"] = lm.x * w, lm.y * h, lm.visibility
                else:
                    row[f"{name}_x"] = row[f"{name}_y"] = row[f"{name}_v"] = np.nan
            rows.append(row)
            if progress and i % 10 == 0:
                progress(min(i / max(info["n_frames"], 1), 1.0), "Detectando el esqueleto")
    info["n_frames"] = len(rows)
    return pd.DataFrame(rows), info


def smooth(df, fps, cfg):
    """Rellena huecos cortos interpolando y suaviza con mediana movil."""
    pcfg = cfg["pose"]
    gap = max(1, round(pcfg["max_gap_seconds"] * fps))
    win = max(1, round(pcfg["smooth_seconds"] * fps)) | 1  # ventana impar
    out = df.copy()
    cols = [c for c in df.columns if c.endswith(("_x", "_y"))]
    for c in cols:
        s = out[c].interpolate(limit=gap, limit_area="inside")
        out[c] = s.rolling(win, center=True, min_periods=1).median()
        out.loc[s.isna(), c] = np.nan  # no inventar puntos en huecos largos
    return out
