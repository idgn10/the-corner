"""Video anotado: esqueleto, contador de golpes e indicador de guardia. Se escribe en H.264."""
import cv2
import imageio_ffmpeg
import numpy as np

from boxeo.pose import iter_frames_fast

# Colores en BGR
LEFT_COLOR = (255, 170, 0)     # azul: lado izquierdo
RIGHT_COLOR = (0, 140, 255)    # naranja: lado derecho
CENTER_COLOR = (230, 230, 230)
GREEN = (60, 200, 60)
RED = (40, 40, 230)

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


def draw_frame(img, row, counts, guard_up, flash_side=None):
    h = img.shape[0]
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
    _label(img, f"Izq: {counts['left']}   Der: {counts['right']}", (pad, int(45 * scale)), (255, 255, 255), 1.1 * scale)
    if guard_up is not None:
        color = GREEN if guard_up else RED
        cv2.circle(img, (pad + int(12 * scale), int(85 * scale)), int(12 * scale), color, -1, cv2.LINE_AA)
        _label(img, "Guardia" if guard_up else "Guardia baja", (pad + int(34 * scale), int(97 * scale)), color, 0.9 * scale)
    return img


def render_video(video_path, out_path, df, punches, info, flash_seconds=0.15, progress=None):
    """Escribe el video anotado en H.264 (reproducible en navegador), al tamano de analisis (720p como maximo).

    Lee el original con el lector rapido (ffmpeg): el video de salida no interviene en el analisis.
    """
    fps, size = info["fps"], info["size"]
    flash = int(flash_seconds * fps)
    peaks = {}
    for p in punches:
        for f in range(p["frame_peak"], p["frame_peak"] + flash + 1):
            peaks[f] = "l" if p["hand"] == "left" else "r"
    counts = {"left": 0, "right": 0}
    by_peak = {}
    for p in punches:
        by_peak.setdefault(p["frame_peak"], []).append(p["hand"])

    writer = imageio_ffmpeg.write_frames(
        str(out_path), size, fps=fps, codec="libx264", pix_fmt_out="yuv420p",
        macro_block_size=2, quality=7, output_params=["-preset", "veryfast", "-movflags", "+faststart"],
    )
    n = len(df)
    writer.send(None)
    try:
        for i, frame in enumerate(iter_frames_fast(video_path, size, n)):
            if progress and i % 30 == 0:
                progress(i / max(n, 1))
            row = df.iloc[i]
            for hand in by_peak.get(i, []):
                counts[hand] += 1
            up_l, up_r = row["up_l"], row["up_r"]
            guard_up = None if np.isnan(up_l) or np.isnan(up_r) else bool(up_l and up_r)
            draw_frame(frame, row, counts, guard_up, peaks.get(i))
            writer.send(np.ascontiguousarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
    finally:
        writer.close()
    return out_path
