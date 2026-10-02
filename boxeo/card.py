"""Componentes visuales de la app (HTML autocontenido): cabecera, ficha, consejos y detalle de metricas."""
from html import escape

from boxeo.tips import ranked_keys

# Paleta propia (la misma que el tema de .streamlit/config.toml)
GOLD = "#E8B33F"
LEFT = "#4EA8FF"     # mano izquierda (igual que en el video anotado)
RIGHT = "#FF9F43"    # mano derecha
GOOD, MID, BAD, NONE = "#3DDC84", "#F5B942", "#FF5C5C", "#6B7385"


def _n(x, nd=0):
    return f"{x:.{nd}f}".replace(".", ",")


def color(score):
    if score is None:
        return NONE
    return GOOD if score >= 80 else MID if score >= 60 else BAD


def verdict(total):
    if total is None:
        return "Sin golpes detectados"
    if total >= 85:
        return "Técnica sólida"
    if total >= 70:
        return "Buen nivel"
    if total >= 50:
        return "En progreso"
    return "A trabajar"


CSS = f"""
<style>
.bx{{font-family:inherit;color:#EEF1F6}}
.bx *{{box-sizing:border-box}}
.bx-header{{display:flex;align-items:center;gap:14px;margin:4px 0 6px}}
.bx-logo{{width:46px;height:46px;border-radius:12px;background:{GOLD};color:#0F1218;display:flex;
  align-items:center;justify-content:center;font-weight:900;font-size:26px;flex:none}}
.bx-brand{{font-size:30px;font-weight:800;letter-spacing:-.01em;line-height:1.1}}
.bx-tag{{color:#9AA3B5;font-size:15px;margin-top:2px}}
.bx-steps{{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 4px}}
.bx-step{{font-size:13px;padding:6px 12px;border-radius:999px;border:1px solid #2A3242;color:#9AA3B5}}
.bx-step.on{{border-color:{GOLD};color:{GOLD};font-weight:700}}
.bx-step.done{{color:#EEF1F6}}
.bx-panel{{background:#171C25;border:1px solid #2A3242;border-radius:16px;padding:18px 20px}}
.bx-hero{{background:linear-gradient(160deg,#1F2633 0%,#12161F 75%);border:2px solid {GOLD};border-radius:18px;
  padding:20px 22px}}
.bx-kicker{{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:{GOLD};font-weight:700}}
.bx-sub{{font-size:13px;color:#9AA3B5;margin-top:3px;overflow-wrap:anywhere}}
.bx-score{{display:flex;align-items:baseline;gap:10px;margin:8px 0 0}}
.bx-total{{font-size:88px;line-height:1;font-weight:800;font-variant-numeric:tabular-nums}}
.bx-of{{font-size:20px;color:#9AA3B5;font-weight:600}}
.bx-verdict{{font-size:16px;font-weight:700;margin-top:4px}}
.bx-stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:16px;padding-top:14px;
  border-top:1px solid #2A3242;text-align:center}}
.bx-stat b{{display:block;font-size:24px;font-weight:800;font-variant-numeric:tabular-nums}}
.bx-stat span{{font-size:10.5px;color:#9AA3B5;text-transform:uppercase;letter-spacing:.07em}}
.bx-h{{font-size:19px;font-weight:800;margin:0 0 12px}}
.bx-tip{{display:flex;gap:12px;align-items:flex-start;padding:12px 0;border-top:1px solid #2A3242}}
.bx-tip:first-of-type{{border-top:none;padding-top:2px}}
.bx-num{{flex:none;width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;
  font-weight:800;font-size:14px;color:#0F1218}}
.bx-tip-label{{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#9AA3B5;font-weight:700}}
.bx-tip-text{{font-size:15px;line-height:1.45;margin-top:2px}}
.bx-metric{{padding:14px 0;border-top:1px solid #2A3242}}
.bx-metric:first-of-type{{border-top:none;padding-top:0}}
.bx-mhead{{display:flex;justify-content:space-between;align-items:baseline;gap:10px}}
.bx-mname{{font-size:16px;font-weight:700}}
.bx-mweight{{font-size:12px;color:#9AA3B5;font-weight:500;margin-left:6px}}
.bx-mscore{{font-size:20px;font-weight:800;font-variant-numeric:tabular-nums}}
.bx-bar{{height:8px;border-radius:4px;background:#2A3242;margin:7px 0 5px;overflow:hidden}}
.bx-bar i{{display:block;height:100%;border-radius:4px}}
.bx-detail{{font-size:13px;color:#C3CAD6}}
.bx details{{margin-top:6px}}
.bx summary{{cursor:pointer;font-size:13px;color:{GOLD};font-weight:600;list-style:none}}
.bx summary::-webkit-details-marker{{display:none}}
.bx summary:before{{content:"＋ "}}
.bx details[open] summary:before{{content:"－ "}}
.bx-how{{font-size:13.5px;line-height:1.5;color:#C3CAD6;background:#11151C;border-radius:10px;padding:10px 12px;
  margin-top:6px}}
.bx-legend{{display:flex;flex-wrap:wrap;gap:14px;font-size:12.5px;color:#9AA3B5;margin:2px 0 4px}}
.bx-dot{{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:-1px}}
@media (max-width:640px){{
  .bx-total{{font-size:72px}}
  .bx-stats{{grid-template-columns:repeat(2,1fr);row-gap:12px}}
  .bx-brand{{font-size:25px}}
}}
</style>
"""


def header_html(name, tagline, step):
    """Cabecera con marca, frase y pasos del flujo (step: 1 subir, 2 analizar, 3 resultados)."""
    labels = ["1 · Sube tu vídeo", "2 · Lo analizamos", "3 · Mejora con tu ficha"]
    steps = "".join(
        f'<span class="bx-step {"on" if i + 1 == step else "done" if i + 1 < step else ""}">{l}</span>'
        for i, l in enumerate(labels)
    )
    return (CSS + f'<div class="bx"><div class="bx-header"><div class="bx-logo">{escape(name[0])}</div>'
            f'<div><div class="bx-brand">{escape(name)}</div><div class="bx-tag">{escape(tagline)}</div></div></div>'
            f'<div class="bx-steps">{steps}</div></div>')


def hero_html(result):
    """Ficha principal: nota total, veredicto y cifras de la sesion."""
    m, total = result["metrics"], result["total"]
    stance = "Diestro" if result.get("stance") == "orthodox" else "Zurdo"
    ppm = _n(m["punches_per_min"]) if m.get("punches_per_min") is not None else "–"
    return (CSS + '<div class="bx"><div class="bx-hero">'
            f'<div class="bx-kicker">Tu nota de la sesión</div>'
            f'<div class="bx-sub">{escape(result["video"])} · {stance} · {_n(m.get("active_s", m["duration_s"]))} s analizados</div>'
            f'<div class="bx-score"><span class="bx-total" style="color:{color(total)}">'
            f'{total if total is not None else "–"}</span><span class="bx-of">/ 100</span></div>'
            f'<div class="bx-verdict" style="color:{color(total)}">{verdict(total)}</div>'
            '<div class="bx-stats">'
            f'<div class="bx-stat"><b style="color:{LEFT}">{m["n_left"]}</b><span>Izquierda</span></div>'
            f'<div class="bx-stat"><b style="color:{RIGHT}">{m["n_right"]}</b><span>Derecha</span></div>'
            f'<div class="bx-stat"><b>{ppm}</b><span>Golpes/min</span></div>'
            f'<div class="bx-stat"><b>{m["n_punches"]}</b><span>Golpes</span></div>'
            '</div></div></div>')


def tips_html(result):
    """Los consejos, numerados por prioridad, con la metrica a la que se refieren."""
    subs = result["subscores"]
    by_rank = ranked_keys(result) if result["metrics"].get("n_punches") else []
    items = []
    for i, tip in enumerate(result["tips"]):
        key = by_rank[i] if i < len(by_rank) else None
        sc = subs[key]["score"] if key else None
        label = subs[key]["label"] if key else "Consejo"
        items.append(
            f'<div class="bx-tip"><div class="bx-num" style="background:{color(sc) if key else GOLD}">{i + 1}</div>'
            f'<div><div class="bx-tip-label">{escape(label)}</div>'
            f'<div class="bx-tip-text">{escape(tip)}</div></div></div>'
        )
    return (CSS + '<div class="bx"><div class="bx-panel"><div class="bx-h">Tu plan para la próxima sesión</div>'
            + "".join(items) + "</div></div>")


def _detail(key, m):
    if key == "guard" and m["guard_pct"] is not None:
        return f"Manos arriba el {_n(m['guard_pct'])}% del tiempo entre golpes"
    if key == "other_hand" and m["other_hand_up_pct"] is not None:
        return f"La otra mano se queda en la cara en el {_n(m['other_hand_up_pct'])}% de los golpes"
    if key == "extension" and m["extended_pct"] is not None:
        return f"{_n(m['extended_pct'])}% de golpes bien extendidos · codo a {_n(m['extension_mean_angle'])}° de media"
    if key == "recovery" and m["recovery_mean_s"] is not None:
        return f"{_n(m['recovery_mean_s'], 2)} s de media en volver a la guardia"
    if key == "base" and m["base_pct"] is not None:
        return f"Base correcta el {_n(m['base_pct'])}% del tiempo"
    if key == "volume" and m["punches_per_min"] is not None:
        return f"{_n(m['punches_per_min'])} golpes por minuto"
    return "Sin datos en este vídeo"


def explain(key, cfg):
    """'¿Como se calcula?' en lenguaje sencillo, con los umbrales reales de config.yaml."""
    s = cfg["scoring"][key]
    scale = f"Puntuación: {_n(s['bad'], 1 if s['bad'] < 5 else 0)} o peor = 0 puntos; {_n(s['good'], 1 if s['good'] < 5 else 0)} o mejor = 100."
    g = cfg["guard"]
    texts = {
        "guard": ("Miramos tus manos en los momentos en que no estás golpeando. Una mano está «arriba» si "
                  f"la muñeca está cerca de la cara (a menos de {_n(g['max_dist_nose'], 1)} veces el ancho de tus "
                  "hombros desde la nariz) y por encima del codo. Medimos el % del tiempo con las dos manos arriba. "
                  f"{scale.replace(' o peor', '% o menos').replace(' o mejor', '% o más')}"),
        "other_hand": ("En cada golpe comprobamos si la mano que no golpea se queda arriba, protegiendo la cara, "
                       "mientras la otra sale. Medimos el % de golpes en los que lo hace. "
                       f"{scale.replace(' o peor', '% o menos').replace(' o mejor', '% o más')}"),
        "extension": ("Medimos el ángulo del codo en el punto más lejano de cada golpe (180° es el brazo "
                      f"totalmente recto). Un golpe está bien extendido si llega a {cfg['extension']['good_angle']}° "
                      "o más. Medimos el % de golpes bien extendidos. "
                      f"{scale.replace(' o peor', '% o menos').replace(' o mejor', '% o más')}"),
        "recovery": ("Desde que el golpe llega a su punto más lejano, contamos el tiempo hasta que esa mano "
                     "vuelve a la guardia. Medimos la media de todos los golpes. "
                     f"Puntuación: {_n(s['bad'], 1)} s o más = 0 puntos; {_n(s['good'], 1)} s o menos = 100."),
        "base": ("Medimos la separación de los pies respecto al ancho de los hombros y si las rodillas están "
                 "algo flexionadas. " + scale.replace(" o peor", "% o menos").replace(" o mejor", "% o más")),
        "volume": ("Contamos los golpes por minuto en la parte activa del vídeo: desde un segundo antes del "
                   "primer golpe hasta un segundo después del último (no cuenta prepararte ni salir de plano). "
                   f"Puntuación: {s['bad']} golpes/min o menos = 0 puntos; {s['good']} o más = 100."),
    }
    return texts.get(key, "") + " Entre esos dos valores, la nota sube en proporción."


def metrics_html(result, cfg):
    """Detalle de cada metrica: nota, barra, dato concreto y '¿Como se calcula?' desplegable."""
    m = result["metrics"]
    total_w = sum(s["weight"] for s in result["subscores"].values()) or 1
    rows = []
    for key, s in sorted(result["subscores"].items(), key=lambda kv: -kv[1]["weight"]):
        if s["weight"] == 0:
            continue  # metrica desactivada en config.yaml (p. ej. base grabando de perfil)
        sc = s["score"]
        rows.append(
            f'<div class="bx-metric"><div class="bx-mhead"><span class="bx-mname">{escape(s["label"])}'
            f'<span class="bx-mweight">· pesa {round(100 * s["weight"] / total_w)}% de la nota</span></span>'
            f'<span class="bx-mscore" style="color:{color(sc)}">{sc if sc is not None else "–"}</span></div>'
            f'<div class="bx-bar"><i style="width:{sc or 0}%;background:{color(sc)}"></i></div>'
            f'<div class="bx-detail">{escape(_detail(key, m))}</div>'
            f'<details><summary>¿Cómo se calcula?</summary><div class="bx-how">{escape(explain(key, cfg))}</div></details>'
            "</div>"
        )
    total_how = ("La nota total es la media de estas notas, pesando más lo que más importa para no recibir "
                 "golpes: " + ", ".join(f'{s["label"].lower()} {round(100 * s["weight"] / total_w)}%'
                                         for s in result["subscores"].values() if s["weight"]) + ".")
    return (CSS + '<div class="bx"><div class="bx-panel"><div class="bx-h">Detalle de tu técnica</div>'
            + "".join(rows)
            + f'<details><summary>¿Cómo se calcula la nota total?</summary><div class="bx-how">{escape(total_how)}</div></details>'
            + "</div></div>")


def legend_html():
    return (CSS + '<div class="bx"><div class="bx-legend">'
            f'<span><i class="bx-dot" style="background:{LEFT}"></i>Golpe con la izquierda</span>'
            f'<span><i class="bx-dot" style="background:{RIGHT}"></i>Golpe con la derecha</span>'
            f'<span><i class="bx-dot" style="background:{BAD}"></i>Guardia baja</span>'
            '<span>Más claro = golpe corto</span></div></div>')
