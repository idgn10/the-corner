"""Video anotado: esqueleto, rotulo de cada golpe, contador e indicador de guardia. Se escribe en H.264."""
import cv2
import imageio_ffmpeg
import numpy as np

from boxeo.moves import curved_punches
from boxeo.pose import iter_frames_fast

# Colores en BGR
LEFT_COLOR = (255, 170, 0)     # azul: lado izquierdo
RIGHT_COLOR = (0, 140, 255)    # naranja: lado derecho
CENTER_COLOR = (230, 230, 230)
GREEN = (60, 200, 60)
RED = (40, 40, 230)
NEUTRAL = (150, 150, 150)      # gris: la nota no mide la guardia en ese momento
HAND_COLORS = {"left": LEFT_COLOR, "right": RIGHT_COLOR}

BONES = [
    ("l_shoulder", "r_shoulder", CENTER_COLOR), ("l_hip", "r_hip", CENTER_COLOR),
    ("l_shoulder", "l_hip", LEFT_COLOR), ("r_shoulder", "r_hip", RIGHT_COLOR),
    ("l_shoulder", "l_elbow", LEFT_COLOR), ("l_elbow", "l_wrist", LEFT_COLOR),
    ("r_shoulder", "r_elbow", RIGHT_COLOR), ("r_elbow", "r_wrist", RIGHT_COLOR),
    ("l_hip", "l_knee", LEFT_COLOR), ("l_knee", "l_ankle", LEFT_COLOR),
    ("r_hip", "r_knee", RIGHT_COLOR), ("r_knee", "r_ankle", RIGHT_COLOR),
]
JOINTS = ["nose", "l_shoulder", "r_shoulder", "l_elbow", "r_elbow", "l_wrist", "r_wrist",
          "l_hip", "r_hip", "l_knee", "r_knee", "l_ankle", "r_ankle"]

SIDE_TAGS = {"left": "IZQ", "right": "DER"}
MOVE_TAGS = {"crochet": "CROCHET", "uppercut": "UPPER"}
COUNTERS = {"rectos": "RECTOS", "curvos": "CURVOS", "esquivas": "ESQUIVAS"}


def _pt(row, name):
    x, y = row[f"{name}_x"], row[f"{name}_y"]
    if np.isnan(x) or np.isnan(y):
        return None
    return int(x), int(y)


def _label(img, text, org, color, scale):
    # Contorno negro con copias desplazadas del MISMO grosor que el texto: en OpenCV el espaciado
    # entre letras depende del grosor, y un contorno mas grueso quedaba como un "fantasma" desplazado.
    th = max(2, round(2 * scale))
    d = max(1, round(1.5 * scale))
    x, y = org
    for dx in (-d, 0, d):
        for dy in (-d, 0, d):
            if dx or dy:
                cv2.putText(img, text, (x + dx, y + dy), cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 0, 0), th, cv2.LINE_AA)
    cv2.putText(img, text, org, cv2.FONT_HERSHEY_SIMPLEX, scale, color, th, cv2.LINE_AA)


def _text_width(text, scale):
    return cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, max(2, round(2 * scale)))[0][0]


def build_tags(punches, moves, fps, tag_seconds=0.6):
    """Un rotulo por golpe o esquiva: {"start", "end" (frames), "text", "color", "kind" (contador), "slot" (fila)}.

    Aparece en el instante que marca la grafica (pico del recto, centro del curvo, punto mas bajo de la esquiva)
    y dura al menos tag_seconds. Un golpe que sale como crochet y como uppercut a la vez cuenta una vez, como en
    el volumen de la nota, la ficha y la grafica (moves.curved_punches), con el nombre del primero que se detecta.
    Si coinciden varios rotulos, cada uno ocupa una fila libre y no se mueve hasta que se quita.
    """
    hold = int(round(tag_seconds * fps))
    tags = []
    for p in punches:
        f = p["frame_peak"]
        tags.append({"start": f, "end": f + hold, "text": "JAB" if p["type"] == "jab" else "DIRECTO",
                     "color": HAND_COLORS[p["hand"]], "kind": "rectos"})
    for g in curved_punches(moves, fps):
        f = int(round(g["t"] * fps))
        tags.append({"start": f, "end": max(f + hold, g["frame_end"]),
                     "text": f"{MOVE_TAGS[g['type']]} {SIDE_TAGS[g['hand']]}",
                     "color": HAND_COLORS[g["hand"]], "kind": "curvos"})
    for m in moves:
        if m["type"] == "esquiva":
            f = int(round(m["t"] * fps))
            tags.append({"start": f, "end": max(f + hold, m["frame_end"]), "text": "ESQUIVA",
                         "color": CENTER_COLOR, "kind": "esquivas"})
    tags.sort(key=lambda t: t["start"])
    busy = []  # frame en que se libera cada fila
    for t in tags:
        slot = next((i for i, end in enumerate(busy) if end < t["start"]), len(busy))
        busy[slot:slot + 1] = [t["end"]]
        t["slot"] = slot
    return tags


def _draw_counter(img, counts, scale, pad):
    """Marcador arriba a la izquierda: una columna por tipo (RECTOS, CURVOS, ESQUIVAS) con su numero debajo."""
    x = pad
    for kind, n in counts.items():
        name, num = COUNTERS[kind], str(n)
        col = max(_text_width(name, 0.6 * scale), _text_width(num, 1.1 * scale))
        _label(img, name, (x + (col - _text_width(name, 0.6 * scale)) // 2, int(30 * scale)), (255, 255, 255), 0.6 * scale)
        _label(img, num, (x + (col - _text_width(num, 1.1 * scale)) // 2, int(68 * scale)), (255, 255, 255), 1.1 * scale)
        x += col + int(22 * scale)


def draw_frame(img, row, counts, guard_up, flash_side=None, tags=()):
    h, w = img.shape[:2]
    th = max(2, h // 240)
    for a, b, color in BONES:
        pa, pb = _pt(row, a), _pt(row, b)
        if pa and pb:
            cv2.line(img, pa, pb, color, th, cv2.LINE_AA)
    for j in JOINTS:
        p = _pt(row, j)
        if p:
            cv2.circle(img, p, th + 2, (255, 255, 255), -1, cv2.LINE_AA)
    # Destello en la muneca al detectar un golpe
    if flash_side:
        p = _pt(row, f"{flash_side}_wrist")
        if p:
            cv2.circle(img, p, h // 18, (0, 255, 255), th + 1, cv2.LINE_AA)

    scale = h / 720
    pad = int(20 * scale)
    _draw_counter(img, counts, scale, pad)
    # Guardia: verde arriba, rojo baja y gris cuando la nota no la mide (siempre visible, para que no parpadee)
    color = NEUTRAL if guard_up is None else GREEN if guard_up else RED
    cv2.circle(img, (pad + int(12 * scale), int(92 * scale)), int(12 * scale), color, -1, cv2.LINE_AA)
    _label(img, "Guardia baja" if guard_up is False else "Guardia", (pad + int(34 * scale), int(104 * scale)),
           color, 0.9 * scale)
    # Rotulos abajo y centrados, apilados hacia arriba: arriba no caben bajo el marcador sin tapar la cara.
    # Dejan libre la franja de abajo, donde el reproductor pone sus controles al pausar
    for t in tags:
        s = 1.15 * scale
        y = h - int(72 * scale) - t["slot"] * int(46 * scale)
        _label(img, t["text"], ((w - _text_width(t["text"], s)) // 2, y), t["color"], s)
    return img


def render_video(video_path, out_path, df, punches, info, guard_eval, moves=None, flash_seconds=0.15, progress=None):
    """Escribe el video anotado en H.264 (reproducible en navegador), al tamano de analisis (720p como maximo).

    `guard_eval`: frames en los que la nota mide la guardia (metrics.guard_frames). Solo ahi sale el indicador
    en verde o en rojo; en el resto (golpes, curvos, esquivas, entrada en guardia y bajada final), en gris.
    `moves`: curvos y esquivas (beta) que se rotulan y cuentan; None si no se muestran (fiabilidad baja).
    Lee el original con el lector rapido (ffmpeg): el video de salida no interviene en el analisis.
    """
    fps, size = info["fps"], info["size"]
    n = len(df)
    flash = int(flash_seconds * fps)
    peaks = {}
    for p in punches:
        for f in range(p["frame_peak"], p["frame_peak"] + flash + 1):
            peaks[f] = "l" if p["hand"] == "left" else "r"
    counts = {"rectos": 0} if moves is None else {"rectos": 0, "curvos": 0, "esquivas": 0}
    tags = build_tags(punches, moves or [], fps)
    both_up = (df["up_l"] * df["up_r"]).to_numpy(float)

    writer = imageio_ffmpeg.write_frames(
        str(out_path), size, fps=fps, codec="libx264", pix_fmt_out="yuv420p",
        macro_block_size=2, quality=7, output_params=["-preset", "veryfast", "-movflags", "+faststart"],
    )
    writer.send(None)
    try:
        for i, frame in enumerate(iter_frames_fast(video_path, size, n)):
            if progress and i % 30 == 0:
                progress(i / max(n, 1))
            row = df.iloc[i]
            for t in tags:
                if t["start"] == i:
                    counts[t["kind"]] += 1
            guard_up = bool(both_up[i]) if guard_eval[i] else None
            draw_frame(frame, row, counts, guard_up, peaks.get(i), [t for t in tags if t["start"] <= i <= t["end"]])
            writer.send(np.ascontiguousarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
    finally:
        writer.close()
    return out_path
