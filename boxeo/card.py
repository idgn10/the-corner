"""Ficha visual tipo tarjeta deportiva (HTML autocontenido para la app)."""
from html import escape


def _n(x, nd=0):
    return f"{x:.{nd}f}".replace(".", ",")


def _color(score):
    if score is None:
        return "#6b7385"
    if score >= 80:
        return "#3ddc84"
    if score >= 60:
        return "#f5b942"
    return "#ff5c5c"


def _verdict(total):
    if total is None:
        return "Sin golpes detectados"
    if total >= 85:
        return "Técnica sólida"
    if total >= 70:
        return "Buen nivel"
    if total >= 50:
        return "En progreso"
    return "A trabajar"


def _detail(key, m):
    """Dato concreto bajo cada barra."""
    if key == "guard" and m["guard_pct"] is not None:
        return f"Manos arriba el {_n(m['guard_pct'])}% del tiempo"
    if key == "other_hand" and m["other_hand_up_pct"] is not None:
        return f"Otra mano arriba en el {_n(m['other_hand_up_pct'])}% de los golpes"
    if key == "extension" and m["extended_pct"] is not None:
        return f"{_n(m['extended_pct'])}% bien extendidos · codo {_n(m['extension_mean_angle'])}°"
    if key == "recovery" and m["recovery_mean_s"] is not None:
        return f"{_n(m['recovery_mean_s'], 2)} s de media en volver"
    if key == "base" and m["base_pct"] is not None:
        return f"Base correcta el {_n(m['base_pct'])}% del tiempo"
    if key == "volume" and m["punches_per_min"] is not None:
        return f"{_n(m['punches_per_min'])} golpes por minuto"
    return "Sin datos"


CSS = """
<style>
.bx-card{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;color:#eef1f6;
  background:linear-gradient(160deg,#1d2433 0%,#12161f 70%);border:2px solid #c9a34a;border-radius:18px;
  padding:22px 22px 18px;max-width:440px;box-shadow:0 8px 24px rgba(0,0,0,.25)}
.bx-top{display:flex;justify-content:space-between;align-items:center;font-size:11px;letter-spacing:.14em;
  text-transform:uppercase;color:#c9a34a;font-weight:700}
.bx-name{font-size:13px;color:#9aa3b5;margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bx-score{display:flex;align-items:baseline;gap:10px;margin:10px 0 2px}
.bx-total{font-size:84px;line-height:1;font-weight:800;font-variant-numeric:tabular-nums}
.bx-of{font-size:20px;color:#9aa3b5;font-weight:600}
.bx-verdict{font-size:15px;font-weight:700;letter-spacing:.02em}
.bx-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:16px 0 18px;padding:12px 0;
  border-top:1px solid #2c3446;border-bottom:1px solid #2c3446;text-align:center}
.bx-stat b{display:block;font-size:26px;font-weight:800;font-variant-numeric:tabular-nums}
.bx-stat span{font-size:11px;color:#9aa3b5;text-transform:uppercase;letter-spacing:.08em}
.bx-row{margin-bottom:12px}
.bx-row-head{display:flex;justify-content:space-between;font-size:14px;font-weight:600}
.bx-bar{height:8px;border-radius:4px;background:#2c3446;margin:5px 0 3px;overflow:hidden}
.bx-bar i{display:block;height:100%;border-radius:4px}
.bx-detail{font-size:12px;color:#9aa3b5}
</style>
"""


def card_html(result):
    m = result["metrics"]
    total = result["total"]
    stance = "Diestro" if result.get("stance") == "orthodox" else "Zurdo"
    rows = []
    for key, s in result["subscores"].items():
        if s["weight"] == 0:
            continue  # metrica desactivada en config.yaml (p. ej. base grabando de perfil)
        sc = s["score"]
        rows.append(
            f'<div class="bx-row"><div class="bx-row-head"><span>{escape(s["label"])}</span>'
            f'<span style="color:{_color(sc)}">{sc if sc is not None else "–"}</span></div>'
            f'<div class="bx-bar"><i style="width:{sc or 0}%;background:{_color(sc)}"></i></div>'
            f'<div class="bx-detail">{escape(_detail(key, m))}</div></div>'
        )
    ppm = _n(m["punches_per_min"]) if m["punches_per_min"] is not None else "–"
    return (
        CSS
        + '<div class="bx-card">'
        + f'<div class="bx-top"><span>Ficha de boxeo</span><span>{stance}</span></div>'
        + f'<div class="bx-name">{escape(result["video"])} · {_n(m["active_s"])} s activos</div>'
        + f'<div class="bx-score"><span class="bx-total" style="color:{_color(total)}">'
        + f'{total if total is not None else "–"}</span><span class="bx-of">/ 100</span></div>'
        + f'<div class="bx-verdict" style="color:{_color(total)}">{_verdict(total)}</div>'
        + '<div class="bx-stats">'
        + f'<div class="bx-stat"><b>{m["n_left"]}</b><span>Izquierda</span></div>'
        + f'<div class="bx-stat"><b>{m["n_right"]}</b><span>Derecha</span></div>'
        + f'<div class="bx-stat"><b>{ppm}</b><span>Golpes/min</span></div>'
        + "</div>"
        + "".join(rows)
        + "</div>"
    )
