"""Movimientos que no son rectos (BETA): crochet, uppercut y esquiva.

No puntuan. Sirven para: mostrarlos en la ficha y la grafica, que un curvo no cuente como jab/directo
y que curvos y esquivas no cuenten como guardia baja. Calibrado con un solo boxeador (docs/DECISIONES.md,
punto 15). Umbrales en config.yaml, seccion `moves`.

Unidad: T = longitud del tronco de pie (centro de hombros a centro de caderas). A diferencia de la anchura
de hombros, casi no cambia con el angulo de camara (de frente a perfil la anchura de hombros cambia x2,5).
"""
import numpy as np
import pandas as pd

TYPES = ("crochet", "uppercut", "esquiva")
LABELS = {"crochet": "Crochet", "uppercut": "Uppercut", "esquiva": "Esquiva"}
HANDS = {"l": "left", "r": "right"}


def _roll(x, n, q):
    return pd.Series(x).rolling(n, center=True, min_periods=max(1, n // 4)).quantile(q).to_numpy()


def _peaks(x, fps, min_val, min_gap):
    """Maximos locales >= min_val separados al menos min_gap s (si dos estan mas cerca, queda el mayor)."""
    half = max(1, int(min_gap * fps / 2))
    out = []
    for i in range(len(x)):
        if np.isnan(x[i]) or x[i] < min_val:
            continue
        if x[i] >= np.nanmax(x[max(0, i - half):i + half + 1]):
            if out and i - out[-1] < 2 * half:
                if x[i] > x[out[-1]]:
                    out[-1] = i
                continue
            out.append(i)
    return out


def _runs(mask, fps, min_frames=2, merge_seconds=0.3):
    """Tramos seguidos con mask=True (de al menos min_frames), uniendo los separados por menos de merge_seconds."""
    runs, i, n = [], 0, len(mask)
    while i < n:
        if not mask[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and mask[j + 1]:
            j += 1
        if j - i + 1 >= min_frames:
            if runs and (i - runs[-1][1]) / fps < merge_seconds:
                runs[-1][1] = j
            else:
                runs.append([i, j])
        i = j + 1
    return runs


def _signals(df, fps):
    """Senales por frame, relativas al cuerpo y en unidades T."""
    shx = ((df["l_shoulder_x"] + df["r_shoulder_x"]) / 2).to_numpy(float)
    shy = ((df["l_shoulder_y"] + df["r_shoulder_y"]) / 2).to_numpy(float)
    hy = ((df["l_hip_y"] + df["r_hip_y"]) / 2).to_numpy(float)
    hx = ((df["l_hip_x"] + df["r_hip_x"]) / 2).to_numpy(float)
    win = int(4 * fps)
    tref = _roll(np.hypot(shx - hx, shy - hy), win, 0.8)   # tronco "de pie" (al agacharse se acorta)
    ny = df["nose_y"].to_numpy(float)
    s = {"drop": (ny - _roll(ny, win, 0.15)) / tref}         # cuanto baja la nariz respecto a estar de pie
    for k in "lr":
        wy = df[f"{k}_wrist_y"].to_numpy(float)
        h = (ny - wy) / tref                                  # muneca sobre la nariz (+ = mas alta)
        s[f"h_{k}"] = h
        s[f"vh_{k}"] = np.gradient(h) * fps if len(h) > 1 else np.full(len(h), np.nan)
        s[f"eh_{k}"] = (df[f"{k}_shoulder_y"].to_numpy(float) - df[f"{k}_elbow_y"].to_numpy(float)) / tref
        s[f"elb_{k}"] = df[f"elbow_{k}"].to_numpy(float)
        s[f"vis_{k}"] = df[f"{k}_wrist_v"].notna().to_numpy() & df[f"{k}_elbow_v"].notna().to_numpy()
    return s


def _move(kind, hand, a, b, t, fps):
    return {"type": kind, "hand": hand, "frame_start": int(a), "frame_end": int(b),
            "t_start": round(a / fps, 2), "t_end": round(b / fps, 2), "t": round(t, 2)}


def detect_moves(df, fps, cfg):
    """Lista de movimientos no rectos ordenada por tiempo. `df` debe traer las columnas de metrics.add_features."""
    mc = cfg["moves"]
    if not mc.get("enabled", True) or len(df) < 2:
        return []
    s = _signals(df, fps)
    moves = []
    for k, hand in HANDS.items():
        # Crochet: codo a la altura del hombro con el brazo doblado y la muneca a la altura de la cabeza
        with np.errstate(invalid="ignore"):
            hook = ((s[f"eh_{k}"] >= mc["hook_elbow_min"]) & (s[f"elb_{k}"] <= mc["hook_angle_max"])
                    & (s[f"h_{k}"] >= mc["hook_wrist_min"]) & s[f"vis_{k}"])
        moves += [_move("crochet", hand, a, b, (a + b) / 2 / fps, fps) for a, b in _runs(hook, fps)]
        # Uppercut: la muneca viene de abajo y sube rapido hasta la cara, con el codo doblado arriba
        h, el = s[f"h_{k}"], s[f"elb_{k}"]
        for i in _peaks(s[f"vh_{k}"], fps, mc["up_speed"], 0.3):
            a, b = max(0, i - int(0.4 * fps)), min(len(h), i + int(0.25 * fps))
            if np.all(np.isnan(h[a:i + 1])) or np.all(np.isnan(h[i:b])):
                continue
            low = a + int(np.nanargmin(h[a:i + 1]))
            top = i + int(np.nanargmax(h[i:b]))
            if (h[low] <= mc["up_low"] and h[top] - h[low] >= mc["up_rise"] and h[top] >= mc["up_top"]
                    and el[top] <= mc["up_angle_max"]):
                moves.append(_move("uppercut", hand, low, top, i / fps, fps))
    # Esquiva: la nariz baja respecto a estar de pie (no distingue media y entera: no es fiable)
    drop = s["drop"]
    for i in _peaks(drop, fps, mc["dodge_drop"], 0.4):
        lo, hi = max(0, i - int(0.45 * fps)), i + int(0.45 * fps)
        above = np.flatnonzero(drop[lo:hi] >= mc["dodge_drop"] / 2) + lo
        moves.append(_move("esquiva", None, above[0], above[-1], i / fps, fps))
    return sorted(moves, key=lambda m: m["t"])


def split_straights(punches, moves, fps):
    """Separa los golpes rectos que en realidad son un curvo de la misma mano. Devuelve (rectos, quitados).

    Crochet: el pico del "recto" puede caer en la preparacion (brazo abierto) hasta 0,2 s antes del crochet
    (en los clips de prueba, como mucho 0,13 s; un jab real 0,23 s antes de un crochet es otro golpe).
    Uppercut: solo si cae dentro del propio uppercut (un directo justo antes es otro golpe).
    """
    pre = {"crochet": 0.2, "uppercut": 0.1}
    keep, removed = [], []
    for p in punches:
        curved = any(
            m["type"] in pre and m["hand"] == p["hand"]
            and m["frame_start"] - int(pre[m["type"]] * fps) <= p["frame_peak"] <= m["frame_end"] + int(0.15 * fps)
            for m in moves)
        (removed if curved else keep).append(p)
    return keep, removed


def drop_late_dodges(moves, punches):
    """Quita las esquivas cuyo punto mas bajo es posterior al ultimo golpe (pico de un recto o centro de un
    curvo): al terminar, acercarse a la camara para pararla tambien baja la nariz en la imagen."""
    last = max([p["t_peak"] for p in punches] + [m["t"] for m in moves if m["type"] != "esquiva"], default=None)
    if last is None:
        return moves
    return [m for m in moves if m["type"] != "esquiva" or m["t"] <= last]


def moves_mask(n, moves, fps, cfg):
    """Frames dentro de un movimiento no recto (con margen): no cuentan para la guardia."""
    out = np.zeros(n, bool)
    margin = cfg["moves"]["guard_margin_seconds"]
    for m in moves:
        before, after = margin[m["type"]]
        out[max(0, m["frame_start"] - int(before * fps)):min(n, m["frame_end"] + int(after * fps) + 1)] = True
    return out


def summary(moves):
    return {t: sum(m["type"] == t for m in moves) for t in TYPES}
