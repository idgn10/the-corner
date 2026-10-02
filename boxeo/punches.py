"""Deteccion de golpes rectos por mano, basada sobre todo en el movimiento de la muneca."""
import numpy as np

from boxeo.metrics import SIDES


def detect_punches(df, fps, cfg):
    """Devuelve una lista de golpes ordenada por tiempo.

    Un golpe es un maximo local de la distancia muneca-hombro (el pico del golpe) al que se llega
    alejando la muneca rapido (aumento de alcance + pico de velocidad). El codo solo filtra:
    en el pico tiene que superar angle_min. La extension buena (160) se valora aparte, en metrics.
    `df` debe traer las columnas de metrics.add_features.
    """
    pc = cfg["punches"]
    rise = max(1, round(pc["max_rise_seconds"] * fps))
    half = max(1, round(pc["debounce_seconds"] * fps / 2))
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
        for i in range(1, len(reach)):
            # Pico: la muneca esta mas lejos del hombro que en los frames de alrededor
            if np.isnan(reach[i]) or reach[i] < np.nanmax(reach[max(0, i - half):i + half + 1]):
                continue
            t_peak = i / fps
            if t_peak - last_peak_t < pc["debounce_seconds"]:
                continue
            # Inicio: punto mas cercano al hombro en la ventana previa
            j0 = max(0, i - rise)
            if np.all(np.isnan(reach[j0:i])):
                continue
            start = j0 + int(np.nanargmin(reach[j0:i]))
            reach_gain = reach[i] - reach[start]
            peak_speed = np.nanmax(speed[start:i + 1])
            angle_peak = np.nanmax(a[start:i + 2]) if not np.all(np.isnan(a[start:i + 2])) else np.nan
            if (reach_gain >= pc["min_reach_increase"]
                    and peak_speed >= pc["min_peak_speed"]
                    and angle_peak >= pc["angle_min"]
                    and not below[i] > pc["max_wrist_below_shoulder"]):
                punches.append({
                    "hand": hand,
                    "type": "jab" if hand == lead else "directo",
                    "frame_start": int(start),
                    "frame_peak": int(i),
                    "t_start": round(start / fps, 3),
                    "t_peak": round(t_peak, 3),
                    "angle_peak": round(float(angle_peak), 1),
                    "peak_speed": round(float(peak_speed), 2),
                    "reach_gain": round(float(reach_gain), 2),
                })
                last_peak_t = t_peak

    return sorted(punches, key=lambda p: p["t_peak"])
