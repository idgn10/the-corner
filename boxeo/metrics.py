"""Metricas: angulos, distancias, guardia, base y resumen de la sesion.

Distancias normalizadas por la anchura de hombros. Coordenadas de imagen: la y crece hacia abajo.
"""
import numpy as np
import pandas as pd

from boxeo.moves import curved_punches, moves_mask, summary

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
    """Anade a cada golpe: si la otra mano sigue arriba, si esta extendido y el tiempo de vuelta.

    Vuelta a la guardia: desde el pico hasta que esa mano esta arriba (regla guard.rule) con el brazo
    recogido (codo < recovery.max_elbow_angle; de perfil, el puno estirado queda delante de la cara y
    la regla de guardia sola lo da por arriba). Tiene que volver antes del pico del siguiente golpe y
    como mucho en recovery.max_seconds; si no, el golpe queda como no recuperado y cuenta max_seconds.
    """
    rc = cfg["recovery"]
    max_rec = rc["max_seconds"]
    peaks = [p["frame_peak"] for p in punches]
    for p in punches:
        s = SIDES[p["hand"]]
        o = "r" if s == "l" else "l"
        seg = df[f"up_{o}"].iloc[p["frame_start"]:p["frame_peak"] + 1]
        p["other_hand_up"] = bool(seg.mean() >= 0.5) if seg.notna().any() else None
        p["extended"] = bool(p["angle_peak"] >= cfg["extension"]["good_angle"])
        next_peaks = [f for f in peaks if f > p["frame_peak"]]
        end = min([len(df), p["frame_peak"] + int(max_rec * fps) + 1] + next_peaks)
        back = (df[f"up_{s}"] == 1) & (df[f"elbow_{s}"] < rc["max_elbow_angle"])
        hits = np.flatnonzero(back.iloc[p["frame_peak"]:end].to_numpy())
        p["recovered"] = bool(len(hits))
        p["recovery_s"] = round(float(hits[0] / fps), 3) if len(hits) else max_rec
        p["frame_end"] = p["frame_peak"] + (int(hits[0]) if len(hits) else end - p["frame_peak"])
    return punches


def _pct(values):
    values = [v for v in values if v is not None]
    return round(100 * float(np.mean(values)), 1) if values else None


def _mean(values, nd=1):
    values = [v for v in values if v is not None]
    return round(float(np.mean(values)), nd) if values else None


def _masks(n, punches, fps, cfg, moves=None):
    """(tramo activo, frames dentro de un golpe) como arrays booleanos.

    Con `moves` (curvos y esquivas, beta) sus tramos cuentan tambien como "dentro de un golpe": no son guardia
    baja. El tramo activo sigue dependiendo solo de los rectos.
    """
    active = np.ones(n, bool)
    if punches:
        margin = int(cfg["active_margin_seconds"] * fps)
        active[:] = False
        active[max(0, punches[0]["frame_start"] - margin):punches[-1]["frame_end"] + margin + 1] = True
    in_punch = np.zeros(n, bool)
    for p in punches:
        in_punch[p["frame_start"]:p["frame_end"] + 1] = True
    if moves:
        in_punch |= moves_mask(n, moves, fps, cfg)
    return active, in_punch


def _guard_mask(df, punches, fps, cfg, moves=None):
    """Tramo en el que se mide la guardia: el tramo activo sin la entrada en guardia ni la bajada final.

    Empieza la primera vez que las dos manos estan arriba (al menos guard.initial_up_seconds) antes del primer
    golpe: lo de antes es colocarse, no guardia baja (si no las subes antes, empieza en el primer golpe).
    Acaba la ultima vez que las dos manos estan arriba (al menos guard.final_up_seconds) despues de la vuelta
    del ultimo golpe: si bajas las manos y ya no las subes, has terminado y no cuenta.
    Solo acorta el tramo activo, nunca lo alarga. Ver docs/DECISIONES.md, puntos 14 y 16.
    """
    active, in_punch = _masks(len(df), punches, fps, cfg, moves)
    if not punches:
        return active, in_punch
    both_up = ((df["up_l"] == 1) & (df["up_r"] == 1)).to_numpy()
    g = cfg["guard"]

    first = punches[0]["frame_start"]
    min_run = max(1, int(round(g.get("initial_up_seconds", 0) * fps)))
    begin, run = first, 0
    for i in range(int(np.argmax(active)), first):
        run = run + 1 if both_up[i] else 0
        if run >= min_run:
            begin = i - run + 1
            break

    min_run = max(1, int(round(g["final_up_seconds"] * fps)))
    start = punches[-1]["frame_end"]
    end, run = start + 1, 0
    for i in range(start, len(df)):
        run = run + 1 if both_up[i] else 0
        if run >= min_run:
            end = i + 1
    active = active.copy()
    active[:begin] = False
    active[end:] = False
    return active, in_punch


def guard_timeline(df, punches, fps, cfg, moves=None, min_seconds=0.4, merge_seconds=0.25, worst=3):
    """Tramos con la guardia baja (fuera de los golpes, curvos y esquivas, en el tramo activo) y los peores momentos.

    Devuelve {"guard_low": [{"start", "end", "hand"}], "worst_guard": [los `worst` tramos mas largos]}.
    hand: "izquierda", "derecha" o "las dos" (la mano que estuvo abajo la mayor parte del tramo).
    """
    n = len(df)
    active, in_punch = _guard_mask(df, punches, fps, cfg, moves)
    up_l, up_r = df["up_l"].to_numpy(float), df["up_r"].to_numpy(float)
    low = active & ~in_punch & ((up_l == 0) | (up_r == 0))

    # Tramos seguidos, uniendo huecos cortos
    segs, i = [], 0
    while i < n:
        if not low[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and low[j + 1]:
            j += 1
        if segs and i - segs[-1][1] <= merge_seconds * fps:
            segs[-1][1] = j
        else:
            segs.append([i, j])
        i = j + 1

    out = []
    for a, b in segs:
        if (b - a + 1) / fps < min_seconds:
            continue
        down_l = np.nanmean(up_l[a:b + 1] == 0)
        down_r = np.nanmean(up_r[a:b + 1] == 0)
        hand = "las dos" if min(down_l, down_r) > 0.6 else ("izquierda" if down_l >= down_r else "derecha")
        out.append({"start": round(a / fps, 2), "end": round((b + 1) / fps, 2), "hand": hand})
    worst_list = sorted(out, key=lambda g: g["end"] - g["start"], reverse=True)[:worst]
    return {"guard_low": out, "worst_guard": sorted(worst_list, key=lambda g: g["start"])}


def compute_metrics(df, punches, fps, cfg, moves=None):
    """Resumen de la sesion. Los golpes (solo rectos) deben venir anotados con annotate_punches.

    Guardia, base y ritmo se miden solo en el tramo activo (alrededor de los golpes); la guardia, sin la
    entrada en guardia ni la bajada final (_guard_mask) ni los curvos y esquivas (`moves`, beta).
    El volumen cuenta rectos y curvos (crochet y uppercut); el resto de metricas, solo los rectos.
    """
    n = len(df)
    active, _ = _masks(n, punches, fps, cfg)
    guard_active, in_move = _guard_mask(df, punches, fps, cfg, moves)
    duration = active.sum() / fps if fps else 0
    curved = curved_punches(moves or [], fps)
    volume_s = duration
    if curved:  # el tramo del volumen abarca tambien los curvos
        events = punches + curved
        margin = int(cfg["active_margin_seconds"] * fps)
        lo = max(0, min(e["frame_start"] for e in events) - margin)
        hi = min(n, max(e["frame_end"] for e in events) + margin + 1)
        volume_s = (hi - lo) / fps

    both_up = df["up_l"] * df["up_r"]
    valid = both_up.notna().to_numpy() & ~in_move & guard_active
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
        "n_curved": len(curved),
        "punches_per_min": round((len(punches) + len(curved)) / volume_s * 60, 1) if volume_s else None,
        "peak_speed_mean": _mean([p["peak_speed"] for p in punches]),
        "by_type": by_type,
        "moves_beta": summary(moves or []),
    }
