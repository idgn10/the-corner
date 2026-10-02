"""Componentes visuales de la app (HTML). El estilo esta en styles.css (lo carga app.py)."""
from html import escape

from boxeo.tips import ranked_keys

# Paleta de The Corner (la misma que styles.css y .streamlit/config.toml)
BEIGE, BLACK, COPPER, GRAY = "#D3D1BA", "#161616", "#E2A27E", "#9A9A92"
GOOD, MID, BAD, NONE = "#5F8A62", "#B8862F", "#B0533C", GRAY   # niveles en tonos apagados
LEFT, RIGHT = BLACK, COPPER                                      # mano izquierda / derecha en la grafica


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


STEPS = ["Sube tu vídeo", "Lo analizamos", "Mejora con tu ficha"]


def header_html(name, tagline, step):
    """Marca, frase de valor y los 3 pasos del flujo como tarjetas numeradas (step: 1, 2 o 3)."""
    steps = "".join(
        f'<div class="tc-step {"on" if i + 1 == step else "done" if i + 1 < step else ""}">'
        f"<b>{i + 1:02d}</b><span>{label}</span></div>"
        for i, label in enumerate(STEPS)
    )
    return (f'<div class="tc"><div class="tc-brand">{escape(name)}<span>.</span></div>'
            f'<div class="tc-tag">{escape(tagline)}</div><div class="tc-steps">{steps}</div></div>')


def strip_html(text, repeat=8):
    """Franja negra con un texto repetido (se duplica para que el desplazamiento sea continuo)."""
    item = f"<span>{escape(text)} <i>✦</i></span>"
    return f'<div class="tc"><div class="tc-strip"><div class="tc-track">{item * repeat * 2}</div></div></div>'


def section_html(num, kicker, title):
    """Titulo de seccion editorial: '(01) · Tu nota' encima de un titulo grande condensado."""
    label = f"({num:02d}) · {kicker}" if num else f"· {kicker}"
    return (f'<div class="tc"><div class="tc-sec"><div class="tc-kicker">{escape(label)}</div>'
            f'<div class="tc-title">{escape(title)}</div></div></div>')


def hero_html(result):
    """Ficha principal: tarjeta negra con la nota, el veredicto y las cifras de la sesion."""
    m, total = result["metrics"], result["total"]
    stance = "Diestro" if result.get("stance") == "orthodox" else "Zurdo"
    ppm = _n(m["punches_per_min"]) if m.get("punches_per_min") is not None else "–"
    return ('<div class="tc"><div class="tc-hero">'
            '<div class="tc-label">Tu nota de la sesión</div>'
            f'<div class="tc-hero-sub">{escape(result["video"])} · {stance} · '
            f'{_n(m.get("active_s", m["duration_s"]))} s analizados</div>'
            f'<div class="tc-score"><span class="tc-total">{total if total is not None else "–"}</span>'
            '<span class="tc-of">/ 100</span></div>'
            f'<div class="tc-verdict"><i style="background:{color(total)}"></i>{verdict(total)}</div>'
            '<div class="tc-stats">'
            f'<div class="tc-stat"><b>{m["n_left"]}</b><span>Izquierda</span></div>'
            f'<div class="tc-stat"><b>{m["n_right"]}</b><span>Derecha</span></div>'
            f'<div class="tc-stat"><b>{ppm}</b><span>Golpes/min</span></div>'
            f'<div class="tc-stat"><b>{m["n_punches"]}</b><span>Golpes</span></div>'
            "</div></div></div>")


def tips_html(result):
    """Los consejos como tarjetas blancas numeradas 01, 02, 03 (orden: lo que mas resta a la nota)."""
    subs = result["subscores"]
    keys = ranked_keys(result) if result["metrics"].get("n_punches") else []
    cards = []
    for i, tip in enumerate(result["tips"]):
        key = keys[i] if i < len(keys) else None
        label = subs[key]["label"] if key else "Consejo"
        dot = f'<i style="background:{color(subs[key]["score"])}"></i>' if key else ""
        cards.append(
            f'<div class="tc-tip"><div class="tc-tip-num">{i + 1:02d}</div><div>'
            f'<div class="tc-tip-label">{dot}{escape(label)}</div>'
            f'<div class="tc-tip-text">{escape(tip)}</div></div></div>'
        )
    return '<div class="tc"><div class="tc-tips">' + "".join(cards) + "</div></div>"


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
            f'<div class="tc-metric"><div class="tc-mhead"><span class="tc-mname">{escape(s["label"])}'
            f'<span class="tc-mweight">· pesa {round(100 * s["weight"] / total_w)}% de la nota</span></span>'
            f'<span class="tc-mscore" style="color:{color(sc)}">{sc if sc is not None else "–"}</span></div>'
            f'<div class="tc-bar"><i style="width:{sc or 0}%;background:{color(sc)}"></i></div>'
            f'<div class="tc-detail">{escape(_detail(key, m))}</div>'
            f'<details><summary>¿Cómo se calcula?</summary><div class="tc-how">{escape(explain(key, cfg))}</div></details>'
            "</div>"
        )
    total_how = ("La nota total es la media de estas notas, pesando más lo que más importa para no recibir "
                 "golpes: " + ", ".join(f'{s["label"].lower()} {round(100 * s["weight"] / total_w)}%'
                                         for s in result["subscores"].values() if s["weight"]) + ".")
    return ('<div class="tc"><div class="tc-panel">' + "".join(rows)
            + f'<div class="tc-total-how"><details><summary>¿Cómo se calcula la nota total?</summary>'
            f'<div class="tc-how">{escape(total_how)}</div></details></div></div></div>')


def legend_html():
    return ('<div class="tc"><div class="tc-legend">'
            f'<span><i class="tc-dot" style="background:{LEFT}"></i>Golpe con la izquierda</span>'
            f'<span><i class="tc-dot" style="background:{RIGHT}"></i>Golpe con la derecha</span>'
            f'<span><i class="tc-dot" style="background:{BAD}"></i>Guardia baja</span>'
            '<span>Más claro = golpe corto</span></div></div>')
