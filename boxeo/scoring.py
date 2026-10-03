"""Puntuacion: subscores 0-100 por metrica y total ponderado (configurado en config.yaml)."""

# Las notas solo son comparables entre analisis con la misma version (docs/DECISIONES.md, punto 17).
# v1: antes de curvos y esquivas (sin campo en metrics.json). v2: curvos y esquivas en beta.
SCORING_VERSION = "v2"

LABELS = {
    "guard": "Guardia",
    "other_hand": "Mano contraria arriba",
    "extension": "Extensión",
    "recovery": "Vuelta a la guardia",
    "base": "Base",
    "volume": "Volumen y ritmo",
}


def linear(value, bad, good):
    """0 puntos en `bad`, 100 en `good`, recta entre medias. Funciona aunque good < bad."""
    if value is None:
        return None
    score = 100 * (value - bad) / (good - bad)
    return round(max(0.0, min(100.0, score)))


def score(metrics, cfg):
    """Devuelve {"subscores": {clave: {...}}, "total": int|None}.

    Sin golpes detectados no hay total. Las metricas sin datos no puntuan y no cuentan en el total.
    """
    subscores = {}
    for key, s in cfg["scoring"].items():
        value = metrics.get(s["metric"])
        subscores[key] = {
            "label": LABELS.get(key, key),
            "metric": s["metric"],
            "value": value,
            "score": linear(value, s["bad"], s["good"]),
            "weight": s["weight"],
        }
    if not metrics.get("n_punches"):
        return {"subscores": subscores, "total": None}  # sin golpes no hay nota que dar
    scored = [v for v in subscores.values() if v["score"] is not None]
    weights = sum(v["weight"] for v in scored)
    total = round(sum(v["score"] * v["weight"] for v in scored) / weights) if weights else None
    return {"subscores": subscores, "total": total}
