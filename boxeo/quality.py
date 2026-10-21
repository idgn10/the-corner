"""Control de calidad de la grabacion: fiabilidad del analisis (alta / media / baja).

No cambia ninguna nota: solo dice cuanto fiarse de ellas y como grabar mejor.
"""
import numpy as np
import pandas as pd

from boxeo.metrics import _masks, dist
from boxeo.recording import FRAME, PLACE, profile_advice

KEY_POINTS = ["nose", "l_shoulder", "r_shoulder", "l_elbow", "r_elbow", "l_wrist", "r_wrist"]
LEVELS = ["baja", "media", "alta"]

MESSAGES = {  # mismas palabras que "Como grabar" (boxeo/recording.py)
    ("ok", "alta"): "Buena grabación: se te ve entero, con buen ángulo y con los puños dentro de la imagen.",
    ("punches", "baja"): ("Hemos detectado muy pocos golpes rectos para darte una nota fiable. Graba de 20 a 60 "
                          "segundos de sombra con al menos 5 jabs o directos, con el móvil " + PLACE + "."),
    ("curved", "baja"): ("Hemos detectado sobre todo curvos y esquivas. Por ahora The Corner solo puntúa jabs y "
                         "directos: incluye al menos 5 en tu sombra para tener nota."),
    ("visible", "media"): ("A ratos no se te ven bien los brazos. Graba con buena luz, " + FRAME + "."),
    ("visible", "baja"): ("Se te ve poco: los brazos o la cara salen tapados o fuera de la imagen buena parte del "
                          "vídeo. Graba con buena luz, " + FRAME + "."),
    ("profile", "baja"): ("El móvil te ve casi de perfil: tu brazo de atrás queda tapado por tu cuerpo la mayor "
                          "parte del vídeo. " + profile_advice().replace("\n", " ")),
    ("wrist_out", "media"): ("A veces se te sale el puño de la imagen al golpear: aleja un poco el móvil, hasta "
                             "dejar un palmo de margen por encima de los brazos y por debajo de los pies."),
    ("wrist_out", "baja"): ("Se te sale el puño de la imagen en muchos golpes: aleja el móvil hasta dejar un palmo "
                            "de margen por encima de los brazos y por debajo de los pies."),
    ("front", "media"): "Estás casi de frente a la cámara: pon el móvil " + PLACE + ".",
    ("front", "baja"): ("Estás de frente a la cámara: así los golpes van hacia el móvil y los brazos parecen más "
                        "cortos. Pon el móvil " + PLACE + "."),
}


# Que hacer, sin repetir el motivo: en "Sin nota" el motivo ya sale antes con su dato
ADVICE = {
    "wrist_out": "Aleja el móvil hasta dejar un palmo de margen por encima de los brazos y por debajo de los pies.",
    "front": "De frente, los golpes van hacia el móvil y los brazos parecen más cortos. Pon el móvil " + PLACE + ".",
    "visible": "Graba con buena luz, " + FRAME + ".",
}


def advice(reason, level, stance=None):
    """Que hacer ante cada motivo (con pocos golpes o sobre todo curvos, su mensaje completo). Casi de perfil,
    con los lados de la guardia elegida."""
    if reason == "profile":
        return profile_advice(stance)
    return ADVICE.get(reason) or MESSAGES.get((reason, level), "")


def profile(q, cfg):
    """Lo que falla es sobre todo el brazo de atras: codo y muneca sin ver a la vez la mayor parte del tiempo y el
    resto (cara, hombros y brazo de delante) bien visible. Solo cambia el texto del motivo, no la fiabilidad.
    No usa la orientacion (hombros / tronco): con los clips de hoy, el corte de perfil tiene muy poco margen."""
    t = cfg["quality"]
    hidden, rest = q.get("rear_arm_hidden_pct"), q.get("rest_visible_pct")
    return (hidden is not None and rest is not None
            and hidden > t["profile_rear_hidden"] and rest >= t["min_visible_high"])


def message(q):
    """Mensaje de la fiabilidad con los textos de ahora: los analisis guardados (como el ejemplo de la app)
    llevan en metrics.json el mensaje de su dia."""
    return MESSAGES.get((q.get("reason"), q.get("level")), q.get("message", ""))


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
    # Solo para el texto del motivo (casi de perfil): codo y muneca de la mano de atras, y todo lo demas
    rear_arm_points = ["l_elbow", "l_wrist"] if cfg.get("stance") == "southpaw" else ["r_elbow", "r_wrist"]
    rear_hidden = df[[f"{k}_v" for k in rear_arm_points]].isna().all(axis=1).to_numpy()
    rest = df[[f"{k}_v" for k in KEY_POINTS if k not in rear_arm_points]].notna().all(axis=1).to_numpy()

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
    rear_arm = {"rear_arm_hidden_pct": round(100 * float(rear_hidden[active].mean()), 1),
                "rest_visible_pct": round(100 * float(rest[active].mean()), 1)}
    if reason == "visible" and worst == 0 and profile(rear_arm, cfg):
        reason = "profile"
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
        **rear_arm,
    }
