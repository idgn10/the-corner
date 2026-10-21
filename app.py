"""App Streamlit: subes un video de boxeo y ves tu ficha, tus consejos y tu sesion segundo a segundo.

Arranque: streamlit run app.py   (modo demo directo: http://localhost:8501/?demo=1)
"""
import json
import os
import shutil
import tempfile
from pathlib import Path
from urllib.parse import unquote

import cv2
import streamlit as st

from boxeo.card import (header_html, hero_html, howto_html, legend_html, metrics_html, no_score_html,
                        orientative_note_html, progress_steps_html, review_moments, section_html, strip_html, svg_img,
                        tips_html, video_legend_html)
from boxeo.charts import session_chart
from boxeo.pipeline import ROOT, STEPS, analyze, load_config
from boxeo.recording import FRAME, MAX_SECONDS, MIN_SECONDS, PLACE, SUMMARY, fps_policy, fps_text
from boxeo.tips import GOOD_SCORE
from scripts.download_model import ensure_model

APP_NAME = "The Corner"
TAGLINE = ("Graba tu sombra, súbela y en un minuto sabrás cómo están tu guardia, tu extensión y tu ritmo, "
           "con consejos concretos para tu próxima sesión.")
STRIP = "Tu entrenador entre asaltos"
PRIVACY = "No guardamos tu vídeo: se borra del servidor al terminar el análisis."
LOCK = svg_img('<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" '
               'stroke="#5F8A62" stroke-width="2.2"><rect x="4" y="11" width="16" height="10" rx="2"/>'
               '<path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>', 15)
DEMO_DIR = ROOT / "demo"   # metrics.json + annotated.mp4 (los dos en git, ver docs/DECISIONES.md punto 3)

st.set_page_config(page_title=f"{APP_NAME} · Análisis de boxeo", page_icon="🥊", layout="wide")
st.html(f"<style>{(ROOT / 'styles.css').read_text(encoding='utf-8')}</style>")  # todo el estilo visual

cfg = load_config()


@st.cache_resource
def _model():
    return ensure_model()


try:
    _model()  # en Streamlit Cloud descarga el modelo al arrancar (models/ no esta en git)
except Exception:
    pass      # si falla, se reintenta al analizar y el usuario ve un mensaje amable


def _video_path(folder, name):
    """Ruta dentro de la carpeta temporal: nunca el nombre del archivo, solo su extension si es de video."""
    suffix = Path(name).suffix.lower()
    return folder / f"input{suffix if suffix in ('.mp4', '.mov', '.m4v') else '.mp4'}"


def _probe(upload):
    """Fotogramas por segundo, duracion y orientacion del video recien subido, antes de analizarlo.

    Se lee con OpenCV como el analisis, desde una carpeta temporal de nombre aleatorio que se borra en el acto
    (docs/DECISIONES.md, punto 20). Se guarda en la sesion para no repetirlo en cada interaccion.
    """
    if st.session_state.get("probe_id") == upload.file_id:
        return st.session_state["probe"]
    folder = Path(tempfile.mkdtemp(prefix="thecorner-"))
    try:
        path = _video_path(folder, upload.name)
        path.write_bytes(upload.getbuffer())
        cap = cv2.VideoCapture(str(path))
        fps = cap.get(cv2.CAP_PROP_FPS) if cap.isOpened() else 0
        n = cap.get(cv2.CAP_PROP_FRAME_COUNT) if cap.isOpened() else 0
        ok, frame = cap.read() if cap.isOpened() else (False, None)
        cap.release()
    finally:
        shutil.rmtree(folder, ignore_errors=True)
    info = {"ok": bool(ok and fps and n > 0)}
    if info["ok"]:
        h, w = frame.shape[:2]  # ya con la rotacion de los videos verticales del movil aplicada
        info.update(fps=fps, seconds=n / fps, vertical=h >= w)
    st.session_state.update(probe_id=upload.file_id, probe=info)
    return info


def _early_warnings(info):
    """Avisos nada mas subir el video, antes de pulsar "Analizar": lo que ya se sabe que va a fallar."""
    if not info["ok"]:
        st.warning("No conseguimos leer este vídeo. Prueba a exportarlo de nuevo desde el móvil en formato MP4 o MOV.")
        return
    fps_msg = fps_text(info["fps"])
    if fps_msg:
        (st.warning if fps_policy(info["fps"]) == "sin_nota" else st.info)(fps_msg)
    secs, max_s = info["seconds"], cfg["video"]["max_seconds"]
    if secs > max_s:
        st.info(f"Tu vídeo dura {secs:.0f} s: analizaremos solo el primer minuto.")
    elif secs < MIN_SECONDS:
        st.info(f"Tu vídeo dura {secs:.0f} s. Recomendamos de {MIN_SECONDS} a {MAX_SECONDS}: con menos puede que no "
                "haya golpes suficientes para darte nota. Puedes analizarlo igual.")
    if not info["vertical"]:
        st.info("Tu vídeo está en horizontal. Se puede analizar, pero con el móvil en vertical se te ve más grande: "
                "pruébalo así la próxima vez.")


def _reset():
    for k in ("result", "video", "source", "seek"):
        st.session_state.pop(k, None)
    st.query_params.clear()


def _load_demo():
    """Carga un analisis ya hecho, sin subir ni procesar nada."""
    path = DEMO_DIR / "metrics.json"
    if not path.exists():
        st.session_state["demo_missing"] = True
        return
    video = DEMO_DIR / "annotated.mp4"
    st.session_state.update(
        result=json.loads(path.read_text(encoding="utf-8")),
        video=str(video) if video.exists() else os.environ.get("DEMO_VIDEO_URL"),
        source="demo", seek=0,
    )


def _friendly_error(e):
    if isinstance(e, FileNotFoundError):
        return "Falta el modelo de IA en el servidor. Prueba a recargar la página en un minuto."
    if isinstance(e, ValueError):
        return ("No hemos podido leer este vídeo. Prueba a exportarlo de nuevo desde el móvil "
                "en formato MP4 o MOV.")
    return "Algo ha fallado al analizar el vídeo. Prueba con otro vídeo; si se repite, avísanos."


# ---------- Paso 1: subir ----------

def _top(step):
    st.html(header_html(APP_NAME, TAGLINE, step=step))
    st.html(strip_html(STRIP))


def upload_view():
    _top(step=1)
    # "Como grabar" va primero: en el movil las columnas se apilan en este orden y tiene que salir antes del boton
    left, right = st.columns([3, 2], gap="large")

    with left:
        st.html(section_html(0, "Antes de grabar", "Cómo grabar"))
        st.html('<div class="tc tc-jump"><a href="#tc-sube">¿Ya tienes el vídeo? Ve a subirlo ↓</a></div>')
        with st.container(key="tc-card-howto"):
            st.html(howto_html())

    with right:
        st.html(section_html(0, "Cuando lo tengas", "Sube tu vídeo", anchor="tc-sube"))
        with st.container(key="tc-card-upload"):
            stance = st.segmented_control(
                "¿Con qué guardia boxeas?", ["orthodox", "southpaw"], default=cfg["stance"], required=True,
                format_func=lambda s: "Diestro (izquierda adelante)" if s == "orthodox" else "Zurdo (derecha adelante)",
            )
            upload = st.file_uploader("Vídeo en MP4 o MOV (el del móvil vale tal cual)",
                                      type=["mp4", "mov", "m4v"])
            if upload is not None:
                _early_warnings(_probe(upload))
            go = st.button("Analizar mi vídeo", type="primary", disabled=upload is None, width="stretch")
            if upload is None:
                st.html('<div class="tc"><div class="tc-note">Cuando lo subas, pulsa <b>Analizar mi vídeo</b>. '
                        "Tarda alrededor de un minuto.</div></div>")
            st.html(f'<div class="tc"><div class="tc-privacy">{LOCK}<span>{PRIVACY}</span></div></div>')
            if go and upload is not None:
                process(upload, stance)
        with st.container(key="tc-card-demo"):
            st.html('<div class="tc"><div class="tc-card-title">¿Sin vídeo a mano?</div>'
                    '<div class="tc-card-sub">Mira un análisis de ejemplo ya hecho, sin subir nada.</div></div>')
            if st.button("Ver un ejemplo", width="stretch"):
                _load_demo()
                if "result" in st.session_state:
                    st.rerun()
            if st.session_state.pop("demo_missing", False):
                st.warning("El ejemplo no está disponible en esta instalación.")


# ---------- Paso 2: procesar ----------

def process(upload, stance):
    steps_box = st.empty()
    bar = st.progress(0.0)
    shown = {"step": None}

    def show(p, step):
        """Pasos (solo se redibujan al cambiar de paso) y barra con el avance total."""
        if step in STEPS:
            k = STEPS.index(step)
            if shown["step"] != step:
                steps_box.html(progress_steps_html(STEPS, k))
                shown["step"] = step
            bar.progress(min(p, 1.0), text=f"Paso {k + 1} de {len(STEPS)} · {step}… {int(100 * min(p, 1.0))} %")
        else:
            steps_box.html(progress_steps_html(STEPS, len(STEPS)))
            bar.progress(1.0, text="¡Listo! Preparando tu ficha…")

    show(0.0, STEPS[0])
    # Cada subida en su carpeta temporal de nombre aleatorio (nunca el nombre del archivo), que se borra entera al
    # terminar, salga bien o mal: en el disco no queda nada. El video con esqueleto queda solo en la memoria de la
    # sesion (docs/DECISIONES.md, punto 20)
    out_dir = Path(tempfile.mkdtemp(prefix="thecorner-"))
    try:
        video_path = _video_path(out_dir, upload.name)
        video_path.write_bytes(upload.getbuffer())

        _model()
        result = analyze(video_path, out_dir, load_config(stance=stance), progress=show)
        video = (out_dir / "annotated.mp4").read_bytes()
    except Exception as e:  # mensaje amable + detalle tecnico plegado
        bar.empty()
        steps_box.empty()
        st.error(_friendly_error(e))
        with st.expander("Detalle técnico"):
            st.code(f"{type(e).__name__}: {e}")
        return
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)
    result["video"] = unquote(upload.name)  # el nombre original, solo para la ficha (algunos navegadores lo
                                            # mandan codificado: "%22Vago%22.MOV" en vez de '"Vago".MOV')
    st.session_state.update(result=result, video=video, source="upload", seek=0)
    st.rerun()


# ---------- Paso 3: resultados ----------

def _seek(t):
    st.session_state["seek"] = max(0.0, t - 0.5)


def results_view():
    r = st.session_state["result"]
    m = r["metrics"]
    _top(step=3)

    if st.session_state.get("source") == "demo":
        st.info("Estás viendo un **análisis de ejemplo** ya hecho. Sube tu vídeo para ver el tuyo.")
    if (r.get("quality") or {}).get("level") == "baja":
        low_quality_view(r)
        return
    if m["pose_detected_pct"] < 50:
        st.warning(f"Solo te hemos visto en el {m['pose_detected_pct']:.0f}% del vídeo. Para un análisis fiable, "
                   f"graba con buena luz, {FRAME}.")

    if not m["n_punches"]:
        st.warning(f"**No hemos detectado golpes en este vídeo.** Graba de 20 a 60 segundos de sombra con jabs y "
                   f"directos, con el móvil {PLACE}, {FRAME}.")
        _video_block(r)
        st.button("Probar con otro vídeo", type="primary", on_click=_reset, width="stretch")
        return
    # Calibrado a 60 fps: que hacer por debajo lo decide FPS_POLICY (boxeo/recording.py; DECISIONES puntos 12 y 22)
    policy = fps_policy(r.get("fps"))
    if policy == "sin_nota":
        low_quality_view({**r, "total": None, "quality": {**r["quality"], "level": "baja", "reason": "fps",
                                                          "fps": r["fps"]}})
        return
    if policy:
        st.info(fps_text(r["fps"]))

    # Nota y video juntos; bajo el video, su leyenda y los momentos para revisar (cada boton lo lleva a ese segundo:
    # en el movil quedan justo debajo). Despues los consejos, la grafica y el detalle
    c1, c2 = st.columns([5, 6], gap="large")
    with c1:
        st.html(section_html(1, "Tu nota", "Así ha ido", badge="Orientativa" if policy == "orientativa" else None))
        st.html(hero_html(r))
    with c2:
        st.html(section_html(2, "Tu vídeo", "Mírate"))
        _video_block(r)
        st.html(video_legend_html(beta="moves" in r))
        _moments(r)

    title, tips = tips_html(r, cfg)
    st.html(section_html(3, "Consejos", title))
    st.html(tips)

    st.html(section_html(4, "Tu sesión", "Segundo a segundo"))
    with st.container(key="tc-card-chart"):
        st.html(legend_html(beta="moves" in r))
        st.altair_chart(session_chart(r), width="stretch", theme=None)

    st.html(section_html(5, "Detalle", "Detalle de tu técnica"))
    st.html(metrics_html(r, cfg))

    st.write("")
    b1, b2 = st.columns(2, gap="small")
    b1.button("Analizar mi vídeo" if st.session_state.get("source") == "demo" else "Analizar otro vídeo",
              type="primary", on_click=_reset, width="stretch")
    b2.download_button("Descargar datos", json.dumps(r, ensure_ascii=False, indent=2),
                       file_name=f"{Path(r['video']).stem}_analisis.json", mime="application/json",
                       width="stretch")
    st.html(f'<div class="tc"><div class="tc-note">Para comparar tus sesiones, graba siempre igual: {SUMMARY}. '
            "La nota juzga los jabs y los directos. Los curvos y las esquivas se detectan en pruebas: los curvos solo "
            "suman a los golpes por minuto y las esquivas no puntúan.</div></div>")


def low_quality_view(r):
    """Fiabilidad baja: sin nota ni consejos de tecnica; video y detalle solo como referencia."""
    c1, c2 = st.columns([5, 6], gap="large")
    with c1:
        st.html(section_html(1, "Tu nota", "Sin nota"))
        st.html(no_score_html(r, cfg))
        st.button("Subir otro vídeo", type="primary", on_click=_reset, width="stretch")
    with c2:
        st.html(section_html(2, "Cómo grabar", "Graba de nuevo así"))
        with st.container(key="tc-card-howto"):
            st.html(howto_html())

    st.html(section_html(3, "Tu vídeo", "Lo que hemos visto", badge="Orientativo"))
    vertical = r.get("size", [9, 16])[1] > r.get("size", [9, 16])[0]
    cv, cn = st.columns([2, 3] if vertical else [1, 1], gap="large")
    with cv:
        _video_block(r)
    with cn:
        st.html(orientative_note_html())
        st.html(video_legend_html(beta=False))  # con fiabilidad baja el video no rotula curvos ni esquivas

    st.html(section_html(4, "Detalle", "Detalle de tu técnica", badge="Orientativo"))
    st.html(metrics_html(r, cfg, orientative=True))

    st.write("")
    st.download_button("Descargar datos", json.dumps(r, ensure_ascii=False, indent=2),
                       file_name=f"{Path(r['video']).stem}_analisis.json", mime="application/json", width="stretch")


def _video_block(r):
    video = st.session_state.get("video")  # bytes (subida) o ruta/URL (ejemplo)
    if isinstance(video, bytes) or (video and (str(video).startswith("http") or Path(video).exists())):
        seek = st.session_state.get("seek", 0)
        st.video(video, start_time=seek, autoplay=bool(seek), muted=True)
    else:
        with st.container(key="tc-card-novideo"):
            st.markdown("**El vídeo de este análisis no está disponible aquí.** "
                        "La ficha, la gráfica y los consejos sí son los del análisis original.")


def _moments(r):
    """Momentos para revisar el fallo del primer consejo (card.review_moments); cada boton lleva el video ahi."""
    first, name, items = review_moments(r, cfg)
    if not items:
        why = ("Tu primer consejo es el ritmo, que no tiene un momento concreto: mira el vídeo entero."
               if first == "volume" and r["subscores"]["volume"]["score"] < GOOD_SCORE
               else "No hay fallos largos que revisar en el vídeo. ¡Bien!")
        st.html(f'<div class="tc"><div class="tc-moments-head"><b>Momentos para revisar.</b> {why}</div></div>')
        return
    st.html(f'<div class="tc"><div class="tc-moments-head"><b>Momentos para revisar: {name.lower()}.</b> Pulsa uno '
            "y el vídeo salta a ese momento.</div></div>")
    for i, (t, text) in enumerate(items):
        st.button(f"Segundo {t:.1f}".replace(".", ",") + f" · {text}", key=f"moment{i}",
                  icon=":material/play_circle:", on_click=_seek, args=(t,), width="stretch")


# ---------- Enrutado ----------

if "result" not in st.session_state and st.query_params.get("demo") == "1":
    _load_demo()

if "result" in st.session_state:
    results_view()
else:
    upload_view()
