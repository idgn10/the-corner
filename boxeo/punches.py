"""Deteccion de golpes rectos por mano a partir del angulo del codo, el alcance y la velocidad."""
import numpy as np

from boxeo.metrics import SIDES


def detect_punches(df, fps, cfg):
    """Devuelve una lista de golpes ordenada por tiempo.

    Un golpe es una subida rapida del angulo del codo (de < angle_bent a > angle_extended)
    con aumento de la distancia muneca-hombro y un pico de velocidad de la muneca.
    `df` debe traer las columnas de metrics.add_features.
    """
    pc = cfg["punches"]
    bent, ext = pc["angle_bent"], pc["angle_extended"]
    rise = max(1, round(pc["max_rise_seconds"] * fps))
    lead = "left" if cfg["stance"] == "orthodox" else "right"
    shoulders_y = (df["l_shoulder_y"].to_numpy(float) + df["r_shoulder_y"].to_numpy(float)) / 2
    scale = df["scale"].to_numpy(float)
    punches = []

    for hand, s in SIDES.items():
        a = df[f"elbow_{s}"].to_numpy(float)
        reach = df[f"reach_{s}"].to_numpy(float)
        speed = df[f"speed_{s}"].to_numpy(float)
        below = (df[f"{s}_wrist_y"].to_numpy(float) - shoulders_y) / scale
        last_peak_t = -np.inf
        i = 1
        while i < len(a):
            # Buscamos el frame en que el codo cruza hacia arriba el umbral de brazo estirado
            if not (a[i] > ext and a[i - 1] <= ext):
                i += 1
                continue
            # Fin del tramo estirado (limitado para no alargarlo sin fin)
            k = i
            while k + 1 < len(a) and a[k + 1] > ext and k + 1 - i < rise:
                k += 1
            # Ultimo frame con el brazo doblado dentro de la ventana previa
            j0 = max(0, i - rise)
            bent_idx = np.flatnonzero(a[j0:i] < bent)
            if len(bent_idx) and not np.all(np.isnan(reach[j0:k + 1])):
                start = j0 + bent_idx[-1]
                seg = slice(start, k + 1)
                peak = start + int(np.nanargmax(reach[seg]))
                reach_gain = np.nanmax(reach[seg]) - reach[start]
                peak_speed = np.nanmax(speed[seg])
                t_peak = peak / fps
                if (reach_gain >= pc["min_reach_increase"]
                        and peak_speed >= pc["min_peak_speed"]
                        and not below[peak] > pc["max_wrist_below_shoulder"]
                        and t_peak - last_peak_t >= pc["debounce_seconds"]):
                    punches.append({
                        "hand": hand,
                        "type": "jab" if hand == lead else "directo",
                        "frame_start": int(start),
                        "frame_peak": int(peak),
                        "t_start": round(start / fps, 3),
                        "t_peak": round(t_peak, 3),
                        "angle_peak": round(float(np.nanmax(a[seg])), 1),
                        "peak_speed": round(float(peak_speed), 2),
                        "reach_gain": round(float(reach_gain), 2),
                    })
                    last_peak_t = t_peak
            i = k + 1

    return sorted(punches, key=lambda p: p["t_peak"])
