"""App Streamlit: subes un video de boxeo y ves tu ficha, tus consejos y tu sesion segundo a segundo.

Arranque: streamlit run app.py   (modo demo directo: http://localhost:8501/?demo=1)
"""
import json
import os
from pathlib import Path

import cv2
import streamlit as st

from boxeo.card import CSS, header_html, hero_html, legend_html, metrics_html, tips_html
from boxeo.charts import session_chart
from boxeo.pipeline import ROOT, analyze, load_config
from scripts.download_model import ensure_model

APP_NAME = "Esquina"
TAGLINE = ("Graba tu sombra, súbela y en un minuto sabrás cómo están tu guardia, tu extensión y tu ritmo, "
           "con consejos concretos para tu próxima sesión.")
DEMO_DIR = ROOT / "demo"   # metrics.json (en git) + annotated.mp4 (solo en local, ver docs/DECISIONES.md)

st.set_page_config(page_title=f"{APP_NAME} · Análisis de boxeo", page_icon="🥊", layout="wide")
st.html(CSS + """<style>
.block-container{max-width:1150px;padding-top:2rem}
div[data-testid="stFileUploaderDropzone"]{border:1.5px dashed #3A4458;border-radius:14px}
[data-testid="stVideo"] video, video{max-height:72vh;border-radius:14px;background:#000}
</style>""")

cfg = load_config()


@st.cache_resource
def _model():
    return ensure_model()


try:
    _model()  # en Streamlit Cloud descarga el modelo al arrancar (models/ no esta en git)
except Exception:
    pass      # si falla, se reintenta al analizar y el usuario ve un mensaje amable


def _duration(path):
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    n = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    return n / fps if n > 0 else 0


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
    return "Algo ha fallado al analizar el vídeo. Prueba con otro clip; si se repite, avísanos."


# ---------- Paso 1: subir ----------

def upload_view():
    st.html(header_html(APP_NAME, TAGLINE, step=1))
    left, right = st.columns([3, 2], gap="large")

    with right:
        with st.container(border=True):
            st.markdown("#### Cómo grabar para que salga bien")
            st.markdown(
                "- 📱 **Móvil fijo**, apoyado o en trípode, con la cámara trasera.\n"
                "- 🧍 **Cuerpo entero** en el plano, de lado o en diagonal.\n"
                "- 💡 **Buena luz** y solo tú en la imagen.\n"
                "- ⏱️ **20-60 segundos** de sombra o saco, con jabs y directos."
            )
        with st.container(border=True):
            st.markdown("#### ¿No tienes un vídeo a mano?")
            st.caption("Mira un análisis de ejemplo ya hecho, sin subir nada.")
            if st.button("Ver un ejemplo", icon="▶️", width="stretch"):
                _load_demo()
                if "result" in st.session_state:
                    st.rerun()
            if st.session_state.pop("demo_missing", False):
                st.warning("El ejemplo no está disponible en esta instalación.")

    with left:
        with st.container(border=True):
            st.markdown("#### Sube tu vídeo")
            stance = st.segmented_control(
                "¿Con qué guardia boxeas?", ["orthodox", "southpaw"], default=cfg["stance"], required=True,
                format_func=lambda s: "Diestro (izquierda adelante)" if s == "orthodox" else "Zurdo (derecha adelante)",
            )
            upload = st.file_uploader("Vídeo en MP4 o MOV (el del móvil vale tal cual)",
                                      type=["mp4", "mov", "m4v"])
            if upload is None:
                st.caption("Cuando lo subas, pulsa **Analizar mi vídeo**. Tarda alrededor de un minuto.")
            go = st.button("Analizar mi vídeo", type="primary", disabled=upload is None, width="stretch")
            if go and upload is not None:
                process(upload, stance)


# ---------- Paso 2: procesar ----------

def process(upload, stance):
    out_dir = ROOT / "outputs" / "app" / Path(upload.name).stem
    out_dir.mkdir(parents=True, exist_ok=True)
    video_path = out_dir / f"input{Path(upload.name).suffix.lower()}"
    video_path.write_bytes(upload.getbuffer())

    max_s = cfg["video"]["max_seconds"]
    if _duration(video_path) > max_s:
        st.info(f"Tu vídeo dura más de {max_s} s: analizaremos el primer minuto.")

    steps = {"Detectando el esqueleto": "Detectando tu esqueleto fotograma a fotograma…",
             "Calculando métricas": "Contando golpes y midiendo tu guardia…",
             "Dibujando el vídeo": "Preparando tu vídeo con el esqueleto…",
             "Listo": "¡Listo!"}
    bar = st.progress(0.0, text="Preparando el análisis…")
    try:
        _model()
        result = analyze(video_path, out_dir, load_config(stance=stance),
                         progress=lambda p, msg: bar.progress(min(p, 1.0), text=steps.get(msg, msg)))
    except Exception as e:  # mensaje amable + detalle tecnico plegado
        bar.empty()
        st.error(_friendly_error(e))
        with st.expander("Detalle técnico"):
            st.code(f"{type(e).__name__}: {e}")
        return
    st.session_state.update(result=result, video=str(out_dir / "annotated.mp4"), source="upload", seek=0)
    st.rerun()


# ---------- Paso 3: resultados ----------

def _seek(t):
    st.session_state["seek"] = max(0.0, t - 0.5)


def results_view():
    r = st.session_state["result"]
    m = r["metrics"]
    st.html(header_html(APP_NAME, TAGLINE, step=3))

    if st.session_state.get("source") == "demo":
        st.info("Estás viendo un **análisis de ejemplo** ya hecho. Sube tu vídeo para ver el tuyo.")
    if m["pose_detected_pct"] < 50:
        st.warning(f"Solo te hemos visto en el {m['pose_detected_pct']:.0f}% del vídeo. Para un análisis fiable, "
                   "que se vea tu cuerpo entero y haya buena luz.")

    if not m["n_punches"]:
        st.warning("**No hemos detectado golpes en este vídeo.** Comprueba que se te ve el cuerpo entero, "
                   "con la cámara fija de lado o en diagonal, y que lanzas golpes rectos estirando el brazo.")
        _video_block(r)
        st.button("Probar con otro vídeo", type="primary", on_click=_reset)
        return

    c1, c2 = st.columns([5, 6], gap="large")
    with c1:
        st.html(hero_html(r))
    with c2:
        st.html(tips_html(r))

    st.write("")
    vertical = r.get("size", [9, 16])[1] > r.get("size", [9, 16])[0]
    cv, cs = st.columns([2, 3] if vertical else [1, 1], gap="large")
    with cv:
        _video_block(r)
    with cs:
        st.markdown("#### Tu sesión, segundo a segundo")
        st.html(legend_html())
        st.altair_chart(session_chart(r), width="stretch", theme=None)
        _moments(r)

    st.write("")
    st.html(metrics_html(r, cfg))

    st.write("")
    b1, b2, _ = st.columns([1, 1, 2])
    b1.button("Analizar otro vídeo", type="primary", on_click=_reset, width="stretch")
    b2.download_button("Descargar datos (JSON)", json.dumps(r, ensure_ascii=False, indent=2),
                       file_name=f"{Path(r['video']).stem}_analisis.json", mime="application/json",
                       width="stretch")
    st.caption("La medición es 2D: funciona mejor con la cámara fija, de lado o en diagonal. "
               "Los ganchos se cuentan como golpes rectos.")


def _video_block(r):
    video = st.session_state.get("video")
    if video and (str(video).startswith("http") or Path(video).exists()):
        seek = st.session_state.get("seek", 0)
        st.video(video, start_time=seek, autoplay=bool(seek), muted=True)
    else:
        with st.container(border=True):
            st.markdown("🎬 **El vídeo de este análisis no está disponible aquí.** "
                        "La ficha, la gráfica y los consejos sí son los del análisis original.")


def _moments(r):
    worst = r.get("timeline", {}).get("worst_guard", [])
    st.markdown("#### Momentos para revisar")
    if not worst:
        st.success("No hay momentos largos con la guardia baja. ¡Bien!")
        return
    st.caption("Los tramos más largos con la guardia baja. Pulsa para verlos en el vídeo.")
    for i, g in enumerate(worst):
        dur = g["end"] - g["start"]
        who = "las dos manos" if g["hand"] == "las dos" else f"la mano {g['hand']}"
        label = f"Segundo {g['start']:.1f}".replace(".", ",") + f" · bajas {who} {dur:.1f} s".replace(".", ",")
        st.button(label, key=f"moment{i}", icon="⏯️", on_click=_seek, args=(g["start"],), width="stretch")


# ---------- Enrutado ----------

if "result" not in st.session_state and st.query_params.get("demo") == "1":
    _load_demo()

if "result" in st.session_state:
    results_view()
else:
    upload_view()
