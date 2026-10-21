"""Como grabar: un solo texto para toda la app y la terminal (docs/DECISIONES.md, punto 21).

Lo usan la pantalla de entrada, la de "Sin nota" ("Graba de nuevo asi"), los avisos de fiabilidad, el pie de la
ficha y la terminal. Si cambia la forma de grabar, se cambia solo aqui.
"""

# Piezas que repiten los avisos, para que digan exactamente lo mismo que la lista
PLACE = "a unos 2 m, entre tu frente y tu hombro adelantado"
FRAME = "con el cuerpo entero en la imagen y un palmo de margen por encima de los brazos y por debajo de los pies"
SUMMARY = f"móvil en vertical a 1,2 m del suelo, {PLACE}, {FRAME}"
IPHONE_60 = "Ajustes > Cámara > Grabar vídeo > «1080p a 60 fps»"
IPHONE_60_SHORTCUT = "en la cámara, en modo vídeo, toca el «30» de la esquina para que ponga «60»"


def rear_side(stance):
    """El lado de la mano de atras: "derecho" en guardia de diestro, "izquierdo" en la de zurdo."""
    return "izquierdo" if stance == "southpaw" else "derecho"


def turn_text(stance=None):
    """Como colocarte respecto al movil (punto 2 de la lista). Sin guardia, para diestros y zurdos; con ella
    (en "Sin nota", con la guardia elegida), con tus lados: se gira hacia el lado de la mano de atras."""
    if stance is None:
        turn, shoulder = "hacia tu derecha (si eres zurdo, hacia tu izquierda)", "tu hombro adelantado"
    elif stance == "southpaw":
        turn, shoulder = "hacia tu izquierda", "tu hombro derecho"
    else:
        turn, shoulder = "hacia tu derecha", "tu hombro izquierdo"
    return (f"Ponte en guardia mirando al móvil y gira un poco {turn} hasta que el móvil quede entre tu frente y "
            f"{shoulder}. Golpea siempre hacia donde miras ahora.")


def test_text(stance=None):
    """La prueba de 5 segundos antes de grabar: con la camara trasera no te ves desde tu sitio, asi que se graba,
    se mira y se borra. Con guardia, el puno de atras por su lado."""
    fist = "el puño de atrás" if stance is None else f"tu puño {rear_side(stance)}"
    return ("Graba 5 segundos de prueba, míralos y bórralos antes de grabar de verdad. "
            "En ellos, ponte en guardia, estira los brazos hacia arriba y lanza un jab largo. "
            f"Se te tienen que ver la cara y los dos puños: si {fist} queda escondido detrás de tu cabeza, gira "
            "un poco hacia el móvil; si algo se sale de la imagen, da un paso atrás.")


def profile_advice(stance=None):
    """Que hacer cuando el movil te ve casi de perfil ("Sin nota"): el punto 2 y la prueba de 5 segundos, en dos
    parrafos (separados por un salto de linea)."""
    return f"{turn_text(stance)}\n{test_text(stance)}"


# (lo importante, en negrita; el resto)
HOWTO = [
    ("Móvil en vertical y fijo,",
     "a 1,2 m del suelo y recto (apoyado o en trípode), con la cámara trasera."),
    ("A unos 2 m.", turn_text()),
    ("Cuerpo entero,",
     "con un palmo de margen por encima de los brazos y por debajo de los pies: que los puños no se salgan al "
     "golpear."),
    ("Prueba de 5 segundos.", test_text()),
    ("Sombra libre, quieto en el sitio:",
     "cualquier combinación de golpes y defensas, sin guion. Sin saco, sin guantes y sin vendas."),
    ("De 20 a 60 segundos, a 60 fotogramas por segundo.",
     f"En el iPhone: {IPHONE_60}. Atajo en el iPhone: {IPHONE_60_SHORTCUT}. En Android: en los ajustes de la "
     "cámara, busca la resolución de vídeo y elige 1080p a 60 fotogramas por segundo."),
    ("Solo tú en la imagen,", "con buena luz y sin espejos detrás."),
]


def howto_lines():
    """La lista como frases sueltas (terminal y consejos guardados en metrics.json)."""
    return [f"{bold} {rest}" for bold, rest in HOWTO]


# Videos grabados a menos de MIN_FPS fotogramas por segundo (docs/DECISIONES.md, punto 22; decidido por Ignacio):
#   "aviso"        nota normal con un aviso de que puede variar unos puntos
#   "orientativa"  nota marcada como orientativa, con el aviso de que suele salir mas baja (lo de hoy)
#   "sin_nota"     sin nota, como con fiabilidad baja
# Solo cambia lo que ensena la app: el analisis y metrics.json son los mismos.
MIN_FPS = 50
FPS_POLICY = "orientativa"

# Duracion recomendada (la lista de arriba dice "de 20 a 60 segundos"); el analisis usa como mucho video.max_seconds
MIN_SECONDS, MAX_SECONDS = 20, 60


def fps_policy(fps):
    """None si los fotogramas por segundo bastan; si no, la politica de FPS_POLICY."""
    return None if fps is None or fps >= MIN_FPS else FPS_POLICY


def fps_text(fps, lead=True):
    """El aviso de los fotogramas por segundo segun la politica (antes de analizar y en el resultado).
    Sin `lead`, sin la primera frase (cuando ya la dice el motivo de "Sin nota")."""
    policy = fps_policy(fps)
    if policy is None:
        return None
    if policy == "orientativa":
        # Copias a 30 de los 5 clips de referencia: en sombra libre, hasta 7 puntos menos (DECISIONES, punto 22)
        return ("Con 30 fotogramas por segundo la nota suele salir hasta 7 puntos más baja. "
                "Graba a 60 para tu nota de verdad.")
    then = {
        "aviso": "te daremos nota, pero puede variar unos puntos.",
        "sin_nota": "con menos fotogramas no podemos darte una nota fiable.",
    }[policy]
    first = f"Tu vídeo está grabado a {fps:.0f} fotogramas por segundo. " if lead else ""
    return f"{first}The Corner está ajustada con vídeos a 60: {then} Para la próxima, en el iPhone: {IPHONE_60}."
