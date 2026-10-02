"""Consejos por reglas: las 3 metricas que mas restan a la nota total, cada una con el dato concreto.

Lo que resta cada metrica = (100 - subscore) x peso. Asi un 55 en volumen (peso 10) pesa menos
que un 63 en guardia (peso 25).
"""


def _n(x, nd=0):
    """Numero con coma decimal."""
    return f"{x:.{nd}f}".replace(".", ",")


GOOD_SCORE = 85  # a partir de esta nota el consejo es de refuerzo, no de correccion


def _good_tip(key, m, cfg):
    if key == "guard":
        return (f"Muy buena guardia: entre golpes tienes las dos manos arriba el {_n(m['guard_pct'])}% "
                "del tiempo. Que no se te bajen cuando llegue el cansancio.")
    if key == "other_hand":
        return (f"Bien protegido: mientras golpeas, la otra mano se queda en la cara en el "
                f"{_n(m['other_hand_up_pct'])}% de los golpes. Mantenlo también en combinaciones largas.")
    if key == "extension":
        return (f"Buena extensión: estiras del todo el brazo en el {_n(m['extended_pct'])}% de tus golpes "
                f"(codo a {_n(m['extension_mean_angle'])}° de media).")
    if key == "recovery":
        return (f"Recoges bien la mano: tardas {_n(m['recovery_mean_s'], 2)} s de media en volver a la guardia "
                "después de cada golpe.")
    if key == "base":
        return f"Base sólida el {_n(m['base_pct'])}% del tiempo: pies bien separados y rodillas flexionadas."
    if key == "volume":
        return (f"Buen ritmo: {_n(m['punches_per_min'])} golpes por minuto. El siguiente paso es "
                "aguantarlo en asaltos más largos.")
    return None


def _tip(key, m, cfg, sub_score):
    if sub_score >= GOOD_SCORE:
        return _good_tip(key, m, cfg)
    other = {"jab": "derecha", "directo": "izquierda"}
    if cfg["stance"] == "southpaw":
        other = {"jab": "izquierda", "directo": "derecha"}

    if key == "guard":
        return (f"Entre golpes tienes las dos manos arriba solo el {_n(m['guard_pct'])}% del tiempo. "
                "Después de cada golpe, vuelve a llevar los puños a la barbilla antes de moverte.")
    if key == "other_hand":
        by_type = m["by_type"]
        worst = max(by_type, key=lambda t: by_type[t]["other_hand_down_pct"] or 0)
        down = by_type[worst]["other_hand_down_pct"] or 0
        if down > 0:
            name = "jabs" if worst == "jab" else "directos"
            return (f"Bajas la mano {other[worst]} en el {_n(down)}% de tus {name}: mantenla pegada "
                    "a la barbilla mientras golpeas con la otra.")
        return (f"La mano que no golpea se queda en la cara en el {_n(m['other_hand_up_pct'])}% de tus golpes: "
                "intenta que sea en todos.")
    if key == "extension":
        good = cfg["extension"]["good_angle"]
        short = 100 - m["extended_pct"]
        return (f"El {_n(short)}% de tus golpes se quedan cortos (codo por debajo de {good}°): "
                "termina cada golpe con el brazo estirado, como si quisieras atravesar el objetivo.")
    if key == "recovery":
        target = _n(cfg["scoring"]["recovery"]["good"], 1)
        return (f"Tardas {_n(m['recovery_mean_s'], 2)} s de media en devolver la mano a la guardia: "
                f"recógela igual de rápido que la lanzas (objetivo: menos de {target} s).")
    if key == "base":
        return (f"Tu base es correcta solo el {_n(m['base_pct'])}% del tiempo: separa los pies algo más "
                "que los hombros y mantén las rodillas ligeramente flexionadas.")
    if key == "volume":
        return (f"Vas a {_n(m['punches_per_min'])} golpes por minuto. Para subir el ritmo, prueba series "
                f"de 20-30 segundos a tope (objetivo: {cfg['scoring']['volume']['good']} o más).")
    return None


def ranked_keys(scores):
    """Metricas puntuadas, de la que mas resta a la nota a la que menos. Empate: primero la de mas peso."""
    ranked = sorted(
        ((100 - v["score"]) * v["weight"], v["weight"], k)
        for k, v in scores["subscores"].items() if v["score"] is not None and v["weight"] > 0
    )[::-1]
    return [k for _, _, k in ranked]


# Con fiabilidad baja no se dan consejos de tecnica (saldrian de datos poco fiables): se dan estas 3 claves
# para volver a grabar. (titulo, explicacion)
RECORDING_KEYS = [
    ("Casi de perfil o en diagonal",
     "No de frente: así se ve bien cómo estiras el brazo y cuándo vuelves a la guardia."),
    ("Cuerpo entero en el plano",
     "De la cabeza a los pies, también cuando estiras el brazo: que el puño no se salga de la imagen."),
    ("A 2-3 metros de la cámara",
     "Con el móvil fijo, apoyado o en trípode."),
]


def recording_tips():
    return [f"{title}. {text}" for title, text in RECORDING_KEYS]


def make_tips(metrics, scores, cfg, n=3):
    """Lista de hasta `n` consejos en espanol, empezando por la metrica que mas resta a la nota."""
    if not metrics.get("n_punches"):
        return ["No he detectado golpes. Comprueba que se te ve el cuerpo entero, con la cámara fija "
                "de lado o en diagonal, y que lanzas golpes rectos estirando el brazo."]
    subs = scores["subscores"]
    tips = [_tip(k, metrics, cfg, subs[k]["score"]) for k in ranked_keys(scores)[:n]]
    return [t for t in tips if t]
