"""Grafica de la sesion: golpes de cada mano y momentos con la guardia baja a lo largo del tiempo."""
import altair as alt
import pandas as pd

from boxeo.card import BAD, LEFT, RIGHT

LANES = ["Izquierda", "Derecha", "Guardia baja"]


def session_chart(result):
    punches = pd.DataFrame([
        {
            "t": p["t_peak"],
            "carril": "Izquierda" if p["hand"] == "left" else "Derecha",
            "golpe": "Jab" if p["type"] == "jab" else "Directo",
            "codo": p["angle_peak"],
            "extension": "Completa" if p.get("extended") else "Corta",
        }
        for p in result["punches"]
    ], columns=["t", "carril", "golpe", "codo", "extension"])
    low = pd.DataFrame(result.get("timeline", {}).get("guard_low", []), columns=["start", "end", "hand"])
    low["carril"] = "Guardia baja"
    low["duracion"] = (low["end"] - low["start"]).round(1)
    end_t = max(result["metrics"]["duration_s"], float(punches["t"].max()) if len(punches) else 0)

    x = alt.X("t:Q", title="Segundo del vídeo", scale=alt.Scale(domain=[0, end_t], nice=False))
    y = alt.Y("carril:N", title=None, sort=LANES, scale=alt.Scale(domain=LANES))
    ticks = alt.Chart(punches).mark_tick(thickness=4, size=26, cornerRadius=2).encode(
        x=x, y=y,
        color=alt.Color("carril:N", scale=alt.Scale(domain=["Izquierda", "Derecha"], range=[LEFT, RIGHT]), legend=None),
        opacity=alt.Opacity("extension:N", scale=alt.Scale(domain=["Completa", "Corta"], range=[1.0, 0.4]), legend=None),
        tooltip=[alt.Tooltip("golpe:N", title="Golpe"), alt.Tooltip("t:Q", title="Segundo", format=".1f"),
                 alt.Tooltip("codo:Q", title="Codo (°)", format=".0f"), alt.Tooltip("extension:N", title="Extensión")],
    )
    bars = alt.Chart(low).mark_bar(height=18, cornerRadius=3, color=BAD).encode(
        x=alt.X("start:Q", scale=alt.Scale(domain=[0, end_t], nice=False)), x2="end:Q", y=y,
        tooltip=[alt.Tooltip("start:Q", title="Desde (s)", format=".1f"), alt.Tooltip("duracion:Q", title="Duración (s)"),
                 alt.Tooltip("hand:N", title="Mano abajo")],
    )
    return (
        alt.layer(bars, ticks)
        .properties(height=170)
        .configure(background="transparent")
        .configure_view(stroke=None)
        .configure_axis(labelColor="#9AA3B5", titleColor="#9AA3B5", gridColor="#2A3242", domainColor="#2A3242",
                        tickColor="#2A3242", labelFontSize=12, titleFontSize=12)
    )
