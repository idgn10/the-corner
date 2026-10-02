"""Metricas: angulos, distancias, guardia, base y resumen de la sesion.

Distancias normalizadas por la anchura de hombros. Coordenadas de imagen: la y crece hacia abajo.
"""
import numpy as np
import pandas as pd

SIDES = {"left": "l", "right": "r"}


def _pt(df, name):
    return df[f"{name}_x"].to_numpy(float), df[f"{name}_y"].to_numpy(float)


def dist(df, a, b):
    ax, ay = _pt(df, a)
    bx, by = _pt(df, b)
    return np.hypot(ax - bx, ay - by)


def angle(df, a, b, c):
    """Angulo (grados) en el punto b formado por a-b-c."""
    ax, ay = _pt(df, a)
    bx, by = _pt(df, b)
    cx, cy = _pt(df, c)
    v1 = np.stack([ax - bx, ay - by])
    v2 = np.stack([cx - bx, cy - by])
    with np.errstate(invalid="ignore", divide="ignore"):
        cos = (v1 * v2).sum(0) / (np.linalg.norm(v1, axis=0) * np.linalg.norm(v2, axis=0))
    return np.degrees(np.arccos(np.clip(cos, -1, 1)))


def _flag(cond, *inputs):
    """Booleano como float, con NaN donde falta algun dato."""
    out = cond.astype(float)
    out[np.any([np.isnan(x) for x in inputs], axis=0)] = np.nan
    return out


def _hand_up(df, s, scale, shoulders_y, g):
    """1 si la mano esta en guardia, 0 si no, NaN si faltan datos (regla en config: guard.rule)."""
    to_nose = dist(df, f"{s}_wrist", "nose") / scale
    _, wy = _pt(df, f"{s}_wrist")
    if g.get("rule", "shoulders") == "elbow":
        _, ey = _pt(df, f"{s}_elbow")
        return _flag((to_nose < g["max_dist_nose"]) & (wy < ey), to_nose, wy, ey)
    limit = shoulders_y + g["max_below_shoulder"] * scale
    return _flag((to_nose < g["max_dist_nose"]) & (wy < limit), to_nose, wy, limit)


def add_features(df, fps, cfg):
    """Anade columnas por frame: escala, angulo de codo, alcance, velocidad, manos arriba y base."""
    out = df.copy()
    # Anchura de hombros con mediana movil de 2 s: estable aunque el tronco rote al golpear
    sw = pd.Series(dist(df, "l_shoulder", "r_shoulder"))
    scale = sw.rolling(max(1, int(2 * fps)), center=True, min_periods=1).median().to_numpy()
    out["scale"] = scale
    shoulders_y = (df["l_shoulder_y"].to_numpy(float) + df["r_shoulder_y"].to_numpy(float)) / 2

    for s in SIDES.values():
        out[f"elbow_{s}"] = angle(df, f"{s}_shoulder", f"{s}_elbow", f"{s}_wrist")
        out[f"reach_{s}"] = dist(df, f"{s}_wrist", f"{s}_shoulder") / scale
        wx, wy = _pt(df, f"{s}_wrist")
        if len(df) > 1:
            out[f"speed_{s}"] = np.hypot(np.gradient(wx), np.gradient(wy)) * fps / scale
        else:
            out[f"speed_{s}"] = np.nan
        out[f"up_{s}"] = _hand_up(df, s, scale, shoulders_y, cfg["guard"])

    b = cfg["base"]
    ratio = dist(df, "l_ankle", "r_ankle") / scale
    knee = (angle(df, "l_hip", "l_knee", "l_ankle") + angle(df, "r_hip", "r_knee", "r_ankle")) / 2
    out["base_ratio"] = ratio
    out["knee_angle"] = knee
    ok = (ratio >= b["min_ratio"]) & (ratio <= b["max_ratio"]) & (knee < b["max_knee_angle"])
    out["base_ok"] = _flag(ok, ratio, knee)
    return out


def annotate_punches(df, punches, fps, cfg):
    """Anade a cada golpe: si la otra mano sigue arriba, si esta extendido y el tiempo de vuelta."""
    max_rec = cfg["recovery"]["max_seconds"]
    for p in punches:
        s = SIDES[p["hand"]]
        o = "r" if s == "l" else "l"
        seg = df[f"up_{o}"].iloc[p["frame_start"]:p["frame_peak"] + 1]
        p["other_hand_up"] = bool(seg.mean() >= 0.5) if seg.notna().any() else None
        p["extended"] = bool(p["angle_peak"] >= cfg["extension"]["good_angle"])
        after = df[f"up_{s}"].iloc[p["frame_peak"]:p["frame_peak"] + int(max_rec * fps) + 1].to_numpy()
        hits = np.flatnonzero(after == 1)
        p["recovery_s"] = round(float(hits[0] / fps), 3) if len(hits) else max_rec
        p["frame_end"] = p["frame_peak"] + round(p["recovery_s"] * fps)
    return punches


def _pct(values):
    values = [v for v in values if v is not None]
    return round(100 * float(np.mean(values)), 1) if values else None


def _mean(values, nd=1):
    values = [v for v in values if v is not None]
    return round(float(np.mean(values)), nd) if values else None


def compute_metrics(df, punches, fps, cfg):
    """Resumen de la sesion. Los golpes deben venir anotados con annotate_punches.

    Guardia, base y ritmo se miden solo en el tramo activo (alrededor de los golpes).
    """
    n = len(df)
    active = np.ones(n, bool)
    if punches:
        margin = int(cfg["active_margin_seconds"] * fps)
        active[:] = False
        active[max(0, punches[0]["frame_start"] - margin):punches[-1]["frame_end"] + margin + 1] = True
    duration = active.sum() / fps if fps else 0
    in_punch = np.zeros(n, bool)
    for p in punches:
        in_punch[p["frame_start"]:p["frame_end"] + 1] = True

    both_up = df["up_l"] * df["up_r"]
    valid = both_up.notna().to_numpy() & ~in_punch & active
    base_valid = df["base_ok"].notna().to_numpy() & active

    by_type = {}
    for t in ("jab", "directo"):
        ps = [p for p in punches if p["type"] == t]
        down = _pct([not p["other_hand_up"] for p in ps if p["other_hand_up"] is not None])
        by_type[t] = {"count": len(ps), "other_hand_down_pct": down}

    return {
        "duration_s": round(n / fps, 1) if fps else 0.0,
        "active_s": round(duration, 1),
        "pose_detected_pct": round(100 * float(df["l_shoulder_x"].notna().mean()), 1) if n else 0.0,
        "n_punches": len(punches),
        "n_left": sum(p["hand"] == "left" for p in punches),
        "n_right": sum(p["hand"] == "right" for p in punches),
        "guard_pct": round(100 * float(both_up[valid].mean()), 1) if valid.any() else None,
        "other_hand_up_pct": _pct([p["other_hand_up"] for p in punches]),
        "extended_pct": _pct([p["extended"] for p in punches]),
        "extension_mean_angle": _mean([p["angle_peak"] for p in punches]),
        "recovery_mean_s": _mean([p["recovery_s"] for p in punches], 2),
        "base_pct": round(100 * float(df["base_ok"][base_valid].mean()), 1) if base_valid.any() else None,
        "punches_per_min": round(len(punches) / duration * 60, 1) if duration else None,
        "peak_speed_mean": _mean([p["peak_speed"] for p in punches]),
        "by_type": by_type,
    }
