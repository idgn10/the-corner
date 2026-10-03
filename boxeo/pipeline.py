"""Pipeline completo: video -> pose -> golpes -> metricas -> puntuacion -> consejos -> salidas.

Lo usan el CLI (scripts/analyze.py) y la app de Streamlit.
"""
import json
from pathlib import Path

import yaml

from boxeo.metrics import add_features, annotate_punches, compute_metrics, guard_timeline
from boxeo.moves import detect_moves, drop_late_dodges, split_straights
from boxeo.pose import extract_landmarks, smooth
from boxeo.punches import detect_punches
from boxeo.quality import assess
from boxeo.render import render_video
from boxeo.scoring import score
from boxeo.tips import make_tips, recording_tips

ROOT = Path(__file__).resolve().parent.parent

# Pasos que ve el usuario y en que tramo de la barra de progreso va cada uno (segun lo que tarda cada fase:
# la deteccion de pose es casi todo el tiempo; ver docs/DECISIONES.md, punto 9)
STEPS = ["Leyendo el vídeo", "Detectando tu postura", "Calculando tu nota", "Preparando el vídeo"]
_SPAN = {STEPS[0]: (0.00, 0.02), STEPS[1]: (0.02, 0.88), STEPS[2]: (0.88, 0.90), STEPS[3]: (0.90, 1.00)}


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
    def report(step, frac=0.0):
        """Avisa del paso actual y del avance total (0-1). Mensaje = nombre del paso."""
        if progress:
            a, b = _SPAN[step]
            progress(a + (b - a) * min(max(frac, 0.0), 1.0), step)

    report(STEPS[0])
    raw, info = extract_landmarks(video_path, cfg, progress=lambda p, msg: report(STEPS[1], p))
    fps = info["fps"]
    report(STEPS[2])
    df = add_features(smooth(raw, fps, cfg), fps, cfg)
    # Curvos y esquivas (beta, no puntuan): un curvo deja de contar como recto y no cuentan como guardia baja
    moves = detect_moves(df, fps, cfg)
    punches, _ = split_straights(detect_punches(df, fps, cfg), moves, fps)
    punches = annotate_punches(df, punches, fps, cfg)
    moves = drop_late_dodges(moves, punches)
    metrics = compute_metrics(df, punches, fps, cfg, moves)
    scores = score(metrics, cfg)
    quality = assess(df, punches, fps, info["size"], cfg)
    # Fiabilidad baja: sin nota total y sin consejos de tecnica (mejor ningun dato que uno falso).
    # Las notas por metrica se guardan igual: la app las ensena como "orientativas".
    reliable = quality["level"] != "baja"
    tips = make_tips(metrics, scores, cfg) if reliable else recording_tips()

    report(STEPS[3])
    render_video(video_path, out_dir / "annotated.mp4", df, punches, info, progress=lambda p: report(STEPS[3], p))
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
        "moves": moves,
        "timeline": guard_timeline(df, punches, fps, cfg, moves),
        "quality": quality,
    }
    with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    if progress:
        progress(1.0, "Listo")
    return result
