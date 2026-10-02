"""Consejos por reglas: los 3 subscores mas bajos, cada uno con el dato concreto de la sesion."""


def _n(x, nd=0):
    """Numero con coma decimal."""
    return f"{x:.{nd}f}".replace(".", ",")


GOOD_SCORE = 85  # a partir de esta nota el consejo es de refuerzo, no de correccion

GOOD = {
    "guard": "Muy bien la guardia: tienes las dos manos arriba el {guard_pct}% del tiempo entre golpes. Mantenlo también cuando te canses.",
    "other_hand": "Bien protegido: la otra mano sigue arriba en el {other_hand_up_pct}% de tus golpes.",
    "extension": "Buena extensión: estiras del todo el brazo en el {extended_pct}% de tus golpes (codo a {extension_mean_angle}° de media).",
    "recovery": "Recoges rápido: tardas {recovery_mean_s} s de media en volver a la guardia.",
    "base": "Base sólida el {base_pct}% del tiempo: pies bien separados y rodillas flexionadas.",
    "volume": "Buen ritmo: {punches_per_min} golpes por minuto. Prueba a mantenerlo en asaltos más largos.",
}


def _tip(key, m, cfg, sub_score):
    if sub_score >= GOOD_SCORE and key in GOOD:
        nd = {"recovery_mean_s": 2}
        vals = {k: _n(v, nd.get(k, 0)) for k, v in m.items() if isinstance(v, (int, float))}
        return GOOD[key].format(**vals)
    stance_other = {"jab": "derecha", "directo": "izquierda"}
    if cfg["stance"] == "southpaw":
        stance_other = {"jab": "izquierda", "directo": "derecha"}

    if key == "guard":
        return (f"Solo mantienes las dos manos arriba el {_n(m['guard_pct'])}% del tiempo entre golpes: "
                "vuelve siempre a la guardia con los puños a la altura de la barbilla.")
    if key == "other_hand":
        by_type = m["by_type"]
        worst = max(by_type, key=lambda t: by_type[t]["other_hand_down_pct"] or 0)
        down = by_type[worst]["other_hand_down_pct"] or 0
        if down > 0:
            name = "jabs" if worst == "jab" else "directos"
            return (f"Bajas la mano {stance_other[worst]} en el {_n(down)}% de tus {name}: "
                    "mientras golpeas con una mano, deja la otra pegada a la barbilla.")
        return (f"Mantienes la otra mano arriba en el {_n(m['other_hand_up_pct'])}% de tus golpes: "
                "sigue protegiéndote la cara con la mano que no golpea.")
    if key == "extension":
        return (f"Solo extiendes del todo el brazo en el {_n(m['extended_pct'])}% de tus golpes "
                f"(ángulo medio del codo {_n(m['extension_mean_angle'])}°): termina cada golpe con el brazo "
                f"estirado, buscando {cfg['extension']['good_angle']}° o más.")
    if key == "recovery":
        return (f"Tardas de media {_n(m['recovery_mean_s'], 2)} s en devolver la mano a la guardia: "
                "recógela igual de rápido que la lanzas (objetivo: menos de 0,4 s).")
    if key == "base":
        return (f"Tu base es correcta solo el {_n(m['base_pct'])}% del tiempo: separa los pies algo más "
                "que los hombros y mantén las rodillas ligeramente flexionadas.")
    if key == "volume":
        return (f"Lanzas {_n(m['punches_per_min'])} golpes por minuto: sube el ritmo con series cortas "
                f"e intensas (objetivo: {cfg['scoring']['volume']['good']} o más).")
    return None


def make_tips(metrics, scores, cfg, n=3):
    """Lista de hasta `n` consejos en espanol, empezando por la peor metrica."""
    if not metrics.get("n_punches"):
        return ["No he detectado golpes. Comprueba que se te ve el cuerpo entero, con la cámara fija "
                "y en diagonal a unos 45 grados, y que lanzas golpes rectos estirando el brazo."]
    ranked = sorted(
        (v["score"], k) for k, v in scores["subscores"].items() if v["score"] is not None and v["weight"] > 0
    )
    tips = [_tip(k, metrics, cfg, sc) for sc, k in ranked[:n]]
    return [t for t in tips if t]
