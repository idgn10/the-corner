"""Descarga el modelo MediaPipe Pose Landmarker en models/.

Uso: python scripts/download_model.py
"""
import sys
import urllib.request
from pathlib import Path

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_full/float16/latest/pose_landmarker_full.task"
)
MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "pose_landmarker_full.task"


def ensure_model(path: Path = MODEL_PATH) -> Path:
    """Descarga el modelo si no existe y devuelve su ruta."""
    if path.exists() and path.stat().st_size > 0:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".part")
    print(f"Descargando modelo en {path} ...")
    urllib.request.urlretrieve(MODEL_URL, tmp)
    tmp.rename(path)
    return path


if __name__ == "__main__":
    p = ensure_model()
    print(f"Modelo listo: {p} ({p.stat().st_size / 1e6:.1f} MB)")
    sys.exit(0)
