"""Control de calidad de la grabacion: fiabilidad del analisis (alta / media / baja).

No cambia ninguna nota: solo dice cuanto fiarse de ellas y como grabar mejor.
"""
import numpy as np
import pandas as pd

from boxeo.metrics import _masks, dist

KEY_POINTS = ["nose", "l_shoulder", "r_shoulder", "l_elbow", "r_elbow", "l_wrist", "r_wrist"]
LEVELS = ["baja", "media", "alta"]

MESSAGES = {
    ("ok", "alta"): "Buena grabación: se te ve bien, de lado y con las manos dentro del encuadre.",
    ("punches", "baja"): ("Hemos detectado muy pocos golpes para darte una nota fiable. Graba al menos 20 segundos "
                          "con jabs y directos, de lado o en diagonal: de frente casi no vemos los golpes."),
    ("curved", "baja"): ("Hemos detectado sobre todo curvos y esquivas. Por ahora The Corner solo puntúa jabs y "
                         "directos: incluye al menos 5 en tu sombra para tener nota."),
    ("visible", "media"): ("A ratos no se te ven bien los brazos. Con más luz y el cuerpo entero dentro del "
                           "encuadre, el análisis será más preciso."),
    ("visible", "baja"): ("Se te ve poco: los brazos o la cara salen tapados o fuera de plano buena parte del vídeo. "
                          "Graba con buena luz y con el cuerpo entero dentro del encuadre."),
    ("wrist_out", "media"): "A veces se te sale la mano del encuadre al golpear: aléjate un paso de la cámara.",
    ("wrist_out", "baja"): "Se te sale la mano del encuadre en muchos golpes: aléjate un par de pasos de la cámara.",
    ("front", "media"): ("Estás casi de frente a la cámara: gírala un poco para que te vea de lado o en diagonal."),
    ("front", "baja"): ("Estás de frente a la cámara: así los golpes van hacia el objetivo y los brazos parecen "
                        "más cortos. Ponte de lado o en diagonal."),
}


def _wrist_out(df, size, edge_margin):
    """Por frame: alguna muneca fuera del encuadre.

    Fuera = la muneca (o, si ha dejado de verse, su ultima posicion vista) esta a menos de `edge_margin`
    anchuras de hombro del borde: el puno sobresale mas o menos eso por delante de la muneca, y cuando sale
    de la imagen MediaPipe suele "pegar" la muneca al borde en vez de perderla. Si deja de verse en el
    centro de la imagen se considera tapada por el cuerpo, no fuera.
    """
    w, h = size
    margin = edge_margin * df["scale"].to_numpy(float)
    out = np.zeros(len(df), bool)
    for s in "lr":
        x, y = df[f"{s}_wrist_x"].to_numpy(float), df[f"{s}_wrist_y"].to_numpy(float)
        seen = df[f"{s}_wrist_v"].notna().to_numpy()
        lx = pd.Series(np.where(seen, x, np.nan)).ffill().to_numpy()
        ly = pd.Series(np.where(seen, y, np.nan)).ffill().to_numpy()
        with np.errstate(invalid="ignore"):
            out |= (lx < margin) | (lx > w - margin) | (ly < margin) | (ly > h - margin)
    return out


def _min_window(active, min_frames):
    """Amplia el tramo activo (centrado) hasta `min_frames`, o a todo el video si dura menos.

    Con pocos golpes el tramo activo son 2-3 s alrededor de ellos y la fiabilidad no ve el resto del video.
    """
    n = len(active)
    need = min(n, min_frames)
    idx = np.flatnonzero(active)
    if len(idx) >= need:
        return active
    start = max(0, min((idx[0] + idx[-1]) // 2 - need // 2, n - need))
    window = np.zeros(n, bool)
    window[start:start + need] = True
    return window


def assess(df, punches, fps, size, cfg, moves=None):
    """Fiabilidad del analisis a partir de lo bien que se ve a la persona en el tramo activo
    (ampliado a un minimo de segundos) y de cuantos golpes rectos se han detectado.

    `moves` (curvos y esquivas, beta) no cambia el nivel: solo el mensaje cuando faltan rectos pero hay
    sobre todo curvos y esquivas, grabando de lado o en diagonal (de frente, un recto hacia la camara
    parece un crochet: ahi se mantiene el mensaje de pocos golpes)."""
    q = cfg["quality"]
    active, _ = _masks(len(df), punches, fps, cfg)
    if not active.any():
        active[:] = True
    active = _min_window(active, int(round(q["min_seconds"] * fps)))

    visible = df[[f"{k}_v" for k in KEY_POINTS]].notna().all(axis=1).to_numpy()
    visible_pct = 100 * float(visible[active].mean())

    person = (df["l_shoulder_v"].notna() & df["r_shoulder_v"].notna()).to_numpy() & active
    wrist_out_pct = 100 * float(_wrist_out(df, size, q["edge_margin"])[person].mean()) if person.any() else 0.0

    with np.errstate(invalid="ignore", divide="ignore"):
        shoulders = dist(df, "l_shoulder", "r_shoulder")
        torso = np.hypot(
            (df["l_shoulder_x"] + df["r_shoulder_x"] - df["l_hip_x"] - df["r_hip_x"]).to_numpy(float) / 2,
            (df["l_shoulder_y"] + df["r_shoulder_y"] - df["l_hip_y"] - df["r_hip_y"]).to_numpy(float) / 2,
        )
        ratios = (shoulders / torso)[active]
    ratio = float(np.nanmedian(ratios)) if np.isfinite(ratios).any() else None

    def level(value, high_ok, medium_ok):
        return 2 if high_ok(value) else 1 if medium_ok(value) else 0

    factors = {  # orden = prioridad del mensaje cuando hay empate
        "punches": 0 if len(punches) < q["min_punches"] else 2,  # con muy pocos golpes los % no dicen nada
        "visible": level(visible_pct, lambda v: v >= q["min_visible_high"], lambda v: v >= q["min_visible_medium"]),
        "wrist_out": level(wrist_out_pct, lambda v: v <= q["max_wrist_out_high"], lambda v: v <= q["max_wrist_out_medium"]),
        "front": 2 if ratio is None else level(ratio, lambda v: v <= q["max_front_high"], lambda v: v <= q["max_front_medium"]),
    }
    worst = min(factors.values())
    reason = "ok" if worst == 2 else next(k for k, v in factors.items() if v == worst)
    n_moves = len(moves or [])
    if reason == "punches" and factors["front"] == 2 and n_moves >= q["min_punches"] and n_moves > len(punches):
        reason = "curved"
    lvl = LEVELS[worst]
    orientation = (None if ratio is None else "de lado o en diagonal" if ratio <= q["max_front_high"]
                   else "casi de frente" if ratio <= q["max_front_medium"] else "de frente")
    return {
        "level": lvl,
        "reason": reason,
        "message": MESSAGES[(reason, lvl)],
        "n_punches": len(punches),
        "n_moves": n_moves,
        "measured_s": round(float(active.sum()) / fps, 1),
        "visible_pct": round(visible_pct, 1),
        "wrist_out_pct": round(wrist_out_pct, 1),
        "orientation_ratio": None if ratio is None else round(ratio, 2),
        "orientation": orientation,
    }
