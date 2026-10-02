"""Pipeline completo: video -> pose -> golpes -> metricas -> puntuacion -> consejos -> salidas.

Lo usan el CLI (scripts/analyze.py) y la app de Streamlit.
"""
import json
from pathlib import Path

import yaml

from boxeo.metrics import add_features, annotate_punches, compute_metrics, guard_timeline
from boxeo.pose import extract_landmarks, smooth
from boxeo.punches import detect_punches
from boxeo.quality import assess
from boxeo.render import render_video
from boxeo.scoring import score
from boxeo.tips import make_tips, recording_tips

ROOT = Path(__file__).resolve().parent.parent


def load_config(path=ROOT / "config.yaml", stance=None):
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if stance:
        cfg["stance"] = stance
    return cfg


def analyze(video_path, out_dir=None, cfg=None, progress=None):
    """Analiza un video y guarda annotated.mp4, metrics.json y landmarks.csv en out_dir.

    `progress(fraccion, mensaje)` es opcional (para barras de progreso).
    Devuelve el diccionario que se guarda en metrics.json.
    """
    video_path = Path(video_path)
    cfg = cfg or load_config()
    out_dir = Path(out_dir or ROOT / "outputs" / video_path.stem)
    out_dir.mkdir(parents=True, exist_ok=True)
    report = progress or (lambda p, msg: None)

    raw, info = extract_landmarks(video_path, cfg, progress=lambda p, msg: report(0.8 * p, msg))
    fps = info["fps"]
    report(0.8, "Calculando métricas")
    df = add_features(smooth(raw, fps, cfg), fps, cfg)
    punches = annotate_punches(df, detect_punches(df, fps, cfg), fps, cfg)
    metrics = compute_metrics(df, punches, fps, cfg)
    scores = score(metrics, cfg)
    quality = assess(df, punches, fps, info["size"], cfg)
    # Fiabilidad baja: sin nota total y sin consejos de tecnica (mejor ningun dato que uno falso).
    # Las notas por metrica se guardan igual: la app las ensena como "orientativas".
    reliable = quality["level"] != "baja"
    tips = make_tips(metrics, scores, cfg) if reliable else recording_tips()

    report(0.85, "Dibujando el vídeo")
    render_video(video_path, out_dir / "annotated.mp4", df, punches, info)
    df.to_csv(out_dir / "landmarks.csv", index=False, float_format="%.3f")

    result = {
        "video": video_path.name,
        "stance": cfg["stance"],
        "fps": round(fps, 2),
        "size": list(info["size"]),
        "total": scores["total"] if reliable else None,
        "subscores": scores["subscores"],
        "metrics": metrics,
        "tips": tips,
        "punches": punches,
        "timeline": guard_timeline(df, punches, fps, cfg),
        "quality": quality,
    }
    with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    report(1.0, "Listo")
    return result
