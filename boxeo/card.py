"""Componentes visuales de la app (HTML). El estilo esta en styles.css (lo carga app.py)."""
import base64
from html import escape

from boxeo.drawings import side_view, top_view
from boxeo.moves import curved_summary
from boxeo.quality import advice, message as quality_message, profile
from boxeo.recording import HOWTO, fps_text, rear_side
from boxeo.render import GREEN, LEFT_COLOR, NEUTRAL, RED, RIGHT_COLOR, hex_color
from boxeo.tips import GOOD_SCORE, make_tips, ranked_keys

# Paleta de The Corner (la misma que styles.css y .streamlit/config.toml)
BEIGE, BLACK, COPPER, GRAY = "#D3D1BA", "#161616", "#E2A27E", "#9A9A92"
GOOD, MID, BAD, NONE = "#5F8A62", "#B8862F", "#B0533C", GRAY   # niveles en tonos apagados
# Los colores del video con esqueleto (boxeo/render.py), tambien en la grafica y las leyendas
LEFT, RIGHT = hex_color(LEFT_COLOR), hex_color(RIGHT_COLOR)             # mano izquierda / derecha
GUARD_UP, GUARD_LOW, GUARD_OFF = hex_color(GREEN), hex_color(RED), hex_color(NEUTRAL)  # indicador de guardia
BETA_NOTE = "Aún en pruebas: lo hemos ajustado con un solo boxeador."

# Nombres que ve el usuario (las claves y el "label" de metrics.json no cambian; docs/DECISIONES.md, punto 21)
LABELS = {
    "guard": "Guardia entre golpes",
    "other_hand": "Guardia al golpear",
    "extension": "Extensión",
    "recovery": "Vuelta a la guardia",
    "base": "Base",
    "volume": "Golpes por minuto",
}


def label(key, sub=None):
    return LABELS.get(key, (sub or {}).get("label", key))


def svg_img(svg, width=None, alt=""):
    """Un SVG como imagen: st.html quita las etiquetas <svg>, pero deja las imagenes con datos incrustados."""
    data = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    size = f' width="{width}"' if width else ""
    return f'<img src="data:image/svg+xml;base64,{data}"{size} alt="{escape(alt)}">'


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


STEPS = ["Graba y sube tu vídeo", "Lo analizamos", "Mejora con tu ficha"]


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


def progress_steps_html(steps, current):
    """Los pasos del analisis: hechos (con ✓), el actual resaltado y los pendientes en gris."""
    items = "".join(
        f'<div class="tc-pstep {"done" if i < current else "on" if i == current else ""}">'
        f'<b>{"✓" if i < current else f"{i + 1:02d}"}</b><span>{escape(s)}</span></div>'
        for i, s in enumerate(steps)
    )
    return f'<div class="tc tc-pwrap"><div class="tc-psteps">{items}</div></div>'


def section_html(num, kicker, title, badge=None, anchor=None):
    """Titulo de seccion editorial: '(01) · Tu nota' encima de un titulo grande condensado.

    `badge` (p. ej. "Orientativo") anade una etiqueta bien visible junto al titulo.
    """
    label = f"({num:02d}) · {kicker}" if num else f"· {kicker}"
    tag = f'<span class="tc-badge">{escape(badge)}</span>' if badge else ""
    ident = f' id="{anchor}"' if anchor else ""
    return (f'<div class="tc"{ident}><div class="tc-sec"><div class="tc-kicker">{escape(label)}</div>'
            f'<div class="tc-title">{escape(title)}{tag}</div></div></div>')


def hero_html(result):
    """Ficha principal: tarjeta negra con la nota, el veredicto y las cifras de la sesion."""
    m, total = result["metrics"], result["total"]
    stance = "Diestro" if result.get("stance") == "orthodox" else "Zurdo"
    ppm = _n(m["punches_per_min"]) if m.get("punches_per_min") is not None else "–"
    curved = m.get("n_curved", 0)
    ppm_note = f"<em>incluye {curved} curvo{'s' if curved > 1 else ''}</em>" if curved else ""
    return ('<div class="tc"><div class="tc-hero">'
            '<div class="tc-label">Tu nota de la sesión</div>'
            f'<div class="tc-hero-sub">{escape(result["video"])} · {stance} · '
            f'{_n(m.get("active_s", m["duration_s"]))} s analizados</div>'
            f'<div class="tc-score"><span class="tc-total">{total if total is not None else "–"}</span>'
            '<span class="tc-of">/ 100</span></div>'
            f'<div class="tc-verdict"><i style="background:{color(total)}"></i>{verdict(total)}</div>'
            '<div class="tc-scale">Cómo leerla: desde 70, buen nivel, con un par de cosas que pulir; desde 85, '
            "técnica sólida, solo quedan detalles.</div>"
            '<div class="tc-stats">'
            f'<div class="tc-stat"><b>{m["by_type"]["jab"]["count"]}</b><span>Jabs</span></div>'
            f'<div class="tc-stat"><b>{m["by_type"]["directo"]["count"]}</b><span>Directos</span></div>'
            f'<div class="tc-stat"><b>{m["n_punches"]}</b><span>Rectos<em>jabs + directos</em></span></div>'
            f'<div class="tc-stat"><b>{ppm}</b><span>Golpes por minuto{ppm_note}</span></div>'
            "</div>" + beta_html(result) + _quality_html(result.get("quality")) + "</div></div>")


def beta_html(result):
    """Curvos y esquivas (beta): cuantos hay y el aviso. Solo los curvos puntuan (volumen). Cada curvo cuenta
    una vez, como en el volumen, la grafica y el video. Los analisis antiguos no los tienen."""
    if "moves" not in result:
        return ""
    curved = result["metrics"].get("n_curved")
    n = curved_summary(result["moves"], result["fps"])
    items = "".join(f'<div class="tc-stat"><b>{n[k]}</b><span>{label}</span></div>'
                    for k, label in (("crochet", "Crochets"), ("uppercut", "Uppercuts"), ("esquiva", "Esquivas")))
    stats = (f'<div class="tc-beta-stats">{items}</div>' if any(n.values())
             else '<div class="tc-quality-msg">No hemos visto curvos ni esquivas en este vídeo.</div>')
    return ('<div class="tc-beta"><div class="tc-quality-head"><span>Curvos y esquivas</span>'
            '<b class="tc-beta-tag">En pruebas</b></div>'
            + stats +
            '<div class="tc-quality-msg">'
            + (f"Los {curved} curvos suman a tus golpes por minuto; el resto de la nota juzga solo jabs y directos. "
               if curved else "La nota juzga solo jabs y directos. ")
            + "Mientras lanzas un curvo o esquivas no se mide la guardia. "
            + escape(BETA_NOTE) + "</div></div>")


QUALITY_COLORS = {"alta": GOOD, "media": MID, "baja": BAD}


def _quality_html(q, message=True):
    """Linea de fiabilidad dentro de la ficha (los analisis antiguos no la tienen)."""
    if not q:
        return ""
    msg = f'<div class="tc-quality-msg">{escape(quality_message(q))}</div>' if message else ""
    return ('<div class="tc-quality"><div class="tc-quality-head"><span>Fiabilidad del análisis</span>'
            f'<b><i style="background:{QUALITY_COLORS[q["level"]]}"></i>{q["level"].capitalize()}</b></div>'
            + msg + "</div>")


def _quality_reason(q, reason=None, level=None, stance=None):
    """El motivo concreto, con el dato medido (casi de perfil, con el brazo de atras de la guardia elegida)."""
    reason = reason or q["reason"]
    if reason == "punches":
        n = q.get("n_punches", 0)
        return "No hemos detectado ningún golpe recto." if n == 0 else \
            f"Solo hemos detectado {n} golpe{'s' if n > 1 else ''} recto{'s' if n > 1 else ''}."
    if reason == "curved":
        n, k = q.get("n_punches", 0), q.get("n_moves", 0)
        rectos = "Ningún golpe recto" if n == 0 else f"Solo {n} golpe{'s' if n > 1 else ''} recto{'s' if n > 1 else ''}"
        return f"{rectos} y {k} curvos y esquivas."
    if reason == "visible":
        return f"Solo se te ven bien la cara y los brazos el {_n(q['visible_pct'])}% del tiempo."
    if reason == "profile":
        return (f"Tu brazo {rear_side(stance)}, el de atrás, queda tapado por tu cuerpo el "
                f"{_n(q['rear_arm_hidden_pct'])}\u00a0% del tiempo: el móvil te ve casi de perfil.")
    if reason == "wrist_out":
        return f"El puño se sale de la imagen el {_n(q['wrist_out_pct'])}% del tiempo."
    if reason == "front":
        where = {"baja": "de frente", "media": "casi de frente"}.get(level) or q.get("orientation", "de frente")
        return f"Estás {where} a la cámara."
    if reason == "fps":
        return f"Tu vídeo está grabado a {q['fps']:.0f} fotogramas por segundo."
    return ""


RECORDING_CAUSES = ("wrist_out", "front", "visible", "profile")


def causes(q, cfg):
    """Motivos de un "Sin nota", primero los de la grabacion (mano fuera de la imagen, de frente, poco visible) y
    despues el de los golpes. Con "pocos golpes", que suele ser consecuencia de la grabacion, van delante todos los
    de la grabacion; con "sobre todo curvos", solo los que por si solos dejan sin nota (los de nivel medio, detras).
    Se sacan de los datos guardados en "quality" con los umbrales de config.yaml; solo cambia el orden en que se
    cuentan, no la fiabilidad. Si lo que no se ve es sobre todo el brazo de atras, el motivo "poco visible" pasa a
    "casi de perfil" (quality.profile). [(motivo, nivel)]."""
    if q.get("reason") == "fps":
        return [("fps", "baja")]
    t = cfg["quality"]
    lvl = lambda bad, mid: "baja" if bad else "media" if mid else None
    checks = {
        "wrist_out": (q.get("wrist_out_pct"), lambda v: lvl(v > t["max_wrist_out_medium"], v > t["max_wrist_out_high"])),
        "front": (q.get("orientation_ratio"), lambda v: lvl(v > t["max_front_medium"], v > t["max_front_high"])),
        "visible": (q.get("visible_pct"), lambda v: lvl(v < t["min_visible_medium"], v < t["min_visible_high"])),
    }
    found = [(k, f(v)) for k, (v, f) in checks.items() if v is not None and f(v)]
    found = [("profile", lv) if k == "visible" and lv == "baja" and profile(q, cfg) else (k, lv) for k, lv in found]
    found.sort(key=lambda c: c[1] != "baja")  # primero los que dejan sin nota
    if q.get("reason") == "punches":
        found.append(("punches", "baja"))
    elif q.get("reason") == "curved":
        at = sum(lv == "baja" for _, lv in found)
        found.insert(at, ("curved", "baja"))
    return found or [(q.get("reason"), q.get("level"))]


def no_score_html(result, cfg):
    """Ficha sin nota: el motivo principal (primero el de la grabacion), los demas y como grabar mejor."""
    q, m = result["quality"], result["metrics"]
    guard = result.get("stance", cfg["stance"])
    stance = "Diestro" if guard == "orthodox" else "Zurdo"
    found = causes(q, cfg)
    (main, main_level), rest = found[0], found[1:]
    main_msg = fps_text(q["fps"], lead=False) if main == "fps" else advice(main, main_level, guard)
    others = ""
    if rest:
        items = "".join(
            f"<li><b>{escape(_quality_reason(q, k, lv, guard))}</b>"
            + (f" {escape(advice(k, lv, guard))}" if k in RECORDING_CAUSES else "") + "</li>"
            for k, lv in rest)
        others = f'<div class="tc-label tc-reason-more">También</div><ul class="tc-reason-list">{items}</ul>'
    return ('<div class="tc"><div class="tc-hero">'
            '<div class="tc-label">Tu nota de la sesión</div>'
            f'<div class="tc-hero-sub">{escape(result["video"])} · {stance} · '
            f'{_n(q.get("measured_s", m.get("active_s", m["duration_s"])))} s analizados</div>'
            '<div class="tc-noscore">Sin nota</div>'
            '<div class="tc-noscore-sub">El vídeo no permite un análisis fiable.</div>'
            '<div class="tc-reason"><div class="tc-label">Motivo</div>'
            f'<div class="tc-reason-text">{escape(_quality_reason(q, main, main_level, guard))}</div>'
            + "".join(f'<div class="tc-quality-msg">{escape(p)}</div>' for p in main_msg.split("\n"))
            + f"{others}</div>"
            + _quality_html(q, message=False) + "</div></div>")


def howto_html():
    """"Como grabar": los dibujos y la misma lista en la entrada y en "Sin nota" (texto en boxeo/recording.py)."""
    items = "".join(f"<li><span><b>{escape(bold)}</b> {escape(rest)}</span></li>" for bold, rest in HOWTO)
    figures = (
        '<div class="tc-draw">'
        f'<figure class="tc-draw-top">{svg_img(top_view(), alt="Visto desde arriba: miras y golpeas hacia delante y el móvil queda a unos 2 m, entre tu frente y tu hombro adelantado")}'
        "<figcaption>Visto desde arriba, si eres diestro. Si eres zurdo, igual pero en espejo: "
        "el móvil a tu derecha.</figcaption></figure>"
        f'<figure class="tc-draw-side">{svg_img(side_view(), alt="El móvil a 1,2 m del suelo y un palmo de margen arriba y abajo")}'
        "<figcaption>Altura del móvil y margen de la imagen.</figcaption></figure></div>"
    )
    return f'<div class="tc tc-howto">{figures}<ol>{items}</ol></div>'


def orientative_note_html():
    return ('<div class="tc"><div class="tc-orient">Por cómo está grabado el vídeo, estos datos pueden no ser '
            "correctos. Úsalos solo como referencia: no cuentan para ninguna nota.</div></div>")


def current_tips(result, cfg):
    """Los consejos con los textos de ahora, a partir de los datos guardados (en el ejemplo de la app,
    metrics.json lleva los textos de su dia). Si algo falla, los guardados."""
    try:
        return make_tips(result["metrics"], result, {**cfg, "stance": result.get("stance", cfg["stance"])})
    except (KeyError, TypeError):
        return result["tips"]


def _tip_card(head, name, dot, tip, good=False):
    return (f'<div class="tc-tip{" tc-tip-good" if good else ""}"><div class="tc-tip-num">{head}</div><div>'
            f'<div class="tc-tip-label">{dot}{escape(name)}</div>'
            f'<div class="tc-tip-text">{escape(tip)}</div></div></div>')


def tips_html(result, cfg):
    """Los consejos (orden: lo que mas resta a la nota). Devuelve (titulo de la seccion, html).

    Los de mejora salen numerados bajo "Tu plan para la proxima sesion"; los de refuerzo (subnota de 85 o mas),
    aparte, bajo "Lo que ya haces bien": una felicitacion no es un plan.
    """
    subs = result["subscores"]
    keys = ranked_keys(result) if result["metrics"].get("n_punches") else []
    fix, good = [], []
    for i, tip in enumerate(current_tips(result, cfg)):
        key = keys[i] if i < len(keys) else None
        name = label(key, subs[key]) if key else "Consejo"
        dot = f'<i style="background:{color(subs[key]["score"])}"></i>' if key else ""
        if key and subs[key]["score"] >= GOOD_SCORE:
            good.append((name, dot, tip))
        else:
            fix.append((name, dot, tip))
    html = "".join(_tip_card(f"{i + 1:02d}", *t) for i, t in enumerate(fix))
    if good:
        sub = '<div class="tc-tips-sub">Lo que ya haces bien</div>' if fix else ""
        html += sub + "".join(_tip_card("✓", *t, good=True) for t in good)
    title = "Tu plan para la próxima sesión" if fix else "Lo que ya haces bien"
    return title, '<div class="tc"><div class="tc-tips">' + html + "</div></div>"


def _spread(items, n):
    """Hasta n elementos repartidos a lo largo de la lista (el primero, el ultimo y en medio)."""
    if len(items) <= n:
        return items
    return [items[round(i * (len(items) - 1) / (n - 1))] for i in range(n)]


def review_moments(result, cfg, n=3):
    """Momentos del video para revisar el fallo del primer consejo.

    Devuelve (clave del primer consejo, nombre de la metrica de los momentos, [(segundo, texto)]).

    Guardia al golpear: golpes del tipo que mas falla con la otra mano abajo. Extension: los golpes con el brazo
    menos estirado. Vuelta a la guardia: los golpes que mas tardan. Guardia entre golpes, o si el primer consejo no
    tiene un momento concreto (ritmo o felicitacion): los tramos mas largos con la guardia baja.
    """
    subs, punches, m = result["subscores"], result.get("punches", []), result["metrics"]
    keys = ranked_keys(result) if m.get("n_punches") else []
    first = keys[0] if keys else None
    key = first if first and subs[first]["score"] < GOOD_SCORE else None
    name = lambda p: "Jab" if p["type"] == "jab" else "Directo"
    other = {"left": "derecha", "right": "izquierda"}
    by_time = lambda ps: sorted(ps, key=lambda p: p["t_peak"])
    items = []
    if key == "other_hand":
        down = [p for p in punches if p.get("other_hand_up") is False]
        worst = max(m["by_type"], key=lambda t: m["by_type"][t]["other_hand_down_pct"] or 0)
        down = [p for p in down if p["type"] == worst] or down
        items = [(p["t_peak"], f"{name(p)}: bajas la {other[p['hand']]}") for p in _spread(by_time(down), n)]
    elif key == "extension":
        short = sorted((p for p in punches if not p.get("extended")), key=lambda p: p["angle_peak"])[:n]
        items = [(p["t_peak"], f"{name(p)} sin estirar ({_n(p['angle_peak'])}°)") for p in by_time(short)]
    elif key == "recovery":
        slow = sorted(punches, key=lambda p: -p["recovery_s"])[:n]
        items = [(p["t_peak"], f"{name(p)}: tardas {_n(p['recovery_s'], 1)} s en volver"
                  if p.get("recovered", True) else f"{name(p)}: no vuelves a la guardia")
                 for p in by_time(slow)]
    if not items:
        key = "guard"
        for g in result.get("timeline", {}).get("worst_guard", []):
            who = "las dos manos" if g["hand"] == "las dos" else f"la {g['hand']}"
            items.append((g["start"], f"Bajas {who} {_n(g['end'] - g['start'], 1)} s"))
    return first, label(key), items


def video_legend_html(beta=True):
    """Leyenda bajo el video con esqueleto: los colores del indicador de guardia, de las manos y los rotulos."""
    dot = lambda c: f'<i class="tc-dot tc-round" style="background:{c}"></i>'
    moves = " · CROCHET · UPPER · ESQUIVA" if beta else ""
    return ('<div class="tc"><div class="tc-vlegend">'
            f"<div><b>Indicador de guardia</b> (arriba a la izquierda): {dot(GUARD_UP)}verde, guardia arriba · "
            f"{dot(GUARD_LOW)}rojo, guardia baja · {dot(GUARD_OFF)}gris, mientras golpeas no se mide la guardia "
            "(tampoco al colocarte ni al terminar).</div>"
            f"<div><b>Manos:</b> {dot(LEFT)}azul, la izquierda · {dot(RIGHT)}naranja, la derecha. Cada golpe sale "
            f"rotulado abajo con el color de su mano: JAB · DIRECTO{moves}.</div>"
            "</div></div>")


def _detail(key, m):
    """El dato concreto de cada metrica, dicho como lo diria un entrenador."""
    if key == "guard" and m["guard_pct"] is not None:
        return f"Entre golpes tienes las dos manos arriba el {_n(m['guard_pct'])}% del tiempo."
    if key == "other_hand" and m["other_hand_up_pct"] is not None:
        return f"Mientras golpeas, la otra mano se queda en la cara en el {_n(m['other_hand_up_pct'])}% de los golpes."
    if key == "extension" and m["extended_pct"] is not None:
        return (f"Estiras del todo el brazo en el {_n(m['extended_pct'])}% de los golpes "
                f"(codo a {_n(m['extension_mean_angle'])}° de media).")
    if key == "recovery" and m["recovery_mean_s"] is not None:
        return f"Tardas {_n(m['recovery_mean_s'], 2)} s de media en volver a la guardia después de cada golpe."
    if key == "base" and m["base_pct"] is not None:
        return f"Base correcta el {_n(m['base_pct'])}% del tiempo."
    if key == "volume" and m["punches_per_min"] is not None:
        curved = m.get("n_curved", 0)
        extra = f", contando {curved} curvos" if curved else ""
        return f"{_n(m['punches_per_min'])} golpes por minuto{extra}."
    return None


def _target(key, cfg):
    """Lo que hace falta para sacar 100 en cada metrica (el umbral "good" de config.yaml)."""
    good = cfg["scoring"][key]["good"]
    return {
        "guard": f"el {_n(good)}% del tiempo o más",
        "other_hand": f"en el {_n(good)}% de los golpes o más",
        "extension": f"en el {_n(good)}% de los golpes o más",
        "recovery": f"{_n(good, 1)} s o menos",
        "base": f"el {_n(good)}% del tiempo o más",
        "volume": f"{_n(good)} golpes por minuto o más",
    }.get(key)


def judgement(score):
    """Bien / Regular / A mejorar, con los mismos cortes que los colores (80 y 60)."""
    if score is None:
        return None
    return "Bien" if score >= 80 else "Regular" if score >= 60 else "A mejorar"


def explain(key, cfg):
    """'¿Como se calcula?' en lenguaje sencillo, con los umbrales reales de config.yaml."""
    s = cfg["scoring"][key]
    pct = f"Puntuación: {_n(s['bad'])}% o menos = 0 puntos; {_n(s['good'])}% o más = 100."
    g = cfg["guard"]
    texts = {
        "guard": ("Miramos tus manos cuando no estás golpeando. Una mano cuenta como «arriba» si el puño está cerca "
                  f"de la cara (a menos de {_n(g['max_dist_nose'], 1)} veces el ancho de tus hombros desde la nariz) "
                  "y por encima del codo. Medimos qué parte del tiempo tienes las dos arriba. No cuenta mientras "
                  "lanzas un golpe, un curvo o esquivas, ni al colocarte al empezar o al bajar los brazos al "
                  f"terminar. {pct}"),
        "other_hand": ("En cada jab o directo miramos si la mano que no golpea se queda arriba, protegiendo la cara, "
                       f"mientras la otra sale. Medimos en qué parte de los golpes lo hace. {pct}"),
        "extension": ("Medimos el ángulo del codo en el punto más lejano de cada jab o directo (180° es el brazo "
                      f"totalmente recto). Un golpe cuenta como bien estirado si llega a {cfg['extension']['good_angle']}° "
                      f"o más. Medimos qué parte de los golpes lo están. {pct}"),
        "recovery": ("Desde que el golpe llega a su punto más lejano, contamos el tiempo hasta que esa mano "
                     "vuelve a la guardia: arriba y con el brazo recogido (codo doblado a menos de "
                     f"{_n(cfg['recovery']['max_elbow_angle'])}°). Si no vuelve antes del siguiente golpe, "
                     f"cuenta como {_n(cfg['recovery']['max_seconds'], 1)} s. Medimos la media de todos los golpes. "
                     f"Puntuación: {_n(s['bad'], 1)} s o más = 0 puntos; {_n(s['good'], 1)} s o menos = 100."),
        "base": ("Medimos la separación de los pies respecto al ancho de los hombros y si las rodillas están "
                 f"algo flexionadas. {pct}"),
        "volume": ("Contamos tus golpes por minuto desde un segundo antes del primero hasta un segundo después del "
                   "último (prepararte o salir de la imagen no cuenta). Cuentan jabs, directos y curvos; las esquivas "
                   f"no. Puntuación: {s['bad']} golpes por minuto o menos = 0 puntos; {s['good']} o más = 100."),
    }
    return texts.get(key, "") + " Entre esos dos valores, la nota sube en proporción."


def metrics_html(result, cfg, orientative=False):
    """Detalle de cada metrica: nota, barra, dato concreto con si esta bien o mal, y '¿Como se calcula?'.

    Con `orientative` (fiabilidad baja) las notas van en gris y sin "Bien / A mejorar": son solo referencia.
    """
    m = result["metrics"]
    tone = (lambda sc: NONE) if orientative else color
    total_w = sum(s["weight"] for s in result["subscores"].values()) or 1
    rows = []
    for key, s in sorted(result["subscores"].items(), key=lambda kv: -kv[1]["weight"]):
        if s["weight"] == 0:
            continue  # metrica desactivada en config.yaml (p. ej. la base)
        sc = s["score"]
        detail, target, word = _detail(key, m), _target(key, cfg), judgement(sc)
        if orientative and key == "volume" and m.get("n_curved"):
            # con fiabilidad baja no se ensenan los curvos (de frente un recto parece un crochet) y este numero los suma
            sc, detail, target = None, "Sin datos fiables: con esta grabación no distinguimos bien los curvos.", None
        if detail is None:
            text = "Sin datos en este vídeo."
        else:
            head = "" if orientative or word is None else f'<b style="color:{tone(sc)}">{word}.</b> '
            text = head + escape(detail) + (f" <span>Para sacar 100: {escape(target)}.</span>" if target else "")
        rows.append(
            f'<div class="tc-metric"><div class="tc-mhead"><span class="tc-mname">{escape(label(key, s))}'
            f'<span class="tc-mweight">· pesa {round(100 * s["weight"] / total_w)}% de la nota</span></span>'
            f'<span class="tc-mscore" style="color:{tone(sc)}">{sc if sc is not None else "–"}</span></div>'
            f'<div class="tc-bar"><i style="width:{sc or 0}%;background:{tone(sc)}"></i></div>'
            f'<div class="tc-detail">{text}</div>'
            f'<details><summary>¿Cómo se calcula?</summary><div class="tc-how">{escape(explain(key, cfg))}</div></details>'
            "</div>"
        )
    total_how = ("La nota total es la media de estas notas, pesando más lo que más importa para no recibir "
                 "golpes: " + ", ".join(f'{label(k, s).lower()} {round(100 * s["weight"] / total_w)}%'
                                         for k, s in result["subscores"].items() if s["weight"]) + ".")
    return ('<div class="tc"><div class="tc-panel">' + "".join(rows)
            + f'<div class="tc-total-how"><details><summary>¿Cómo se calcula la nota total?</summary>'
            f'<div class="tc-how">{escape(total_how)}</div></details></div></div></div>')


def legend_html(beta=False):
    """Leyenda de la grafica (mismos colores que el video). `beta`: trae curvos y esquivas (los antiguos no)."""
    return ('<div class="tc"><div class="tc-legend">'
            f'<span><i class="tc-dot" style="background:{LEFT}"></i>Golpe con la izquierda</span>'
            f'<span><i class="tc-dot" style="background:{RIGHT}"></i>Golpe con la derecha</span>'
            f'<span><i class="tc-dot" style="background:{GUARD_LOW}"></i>Guardia baja</span>'
            '<span>Más claro = brazo sin estirar</span>'
            + ('<span><b>En pruebas:</b> ● crochet · ▲ uppercut · ◆ esquiva</span>' if beta else "") + "</div></div>")
