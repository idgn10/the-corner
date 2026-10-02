"""App Streamlit: subir un video de boxeo y ver esqueleto, ficha con puntuacion y consejos.

Arranque: streamlit run app.py
"""
import json
from pathlib import Path

import cv2
import streamlit as st

from boxeo.pipeline import ROOT, analyze, load_config
from scripts.download_model import ensure_model

st.set_page_config(page_title="Boxeo MVP", page_icon="🥊", layout="wide")


@st.cache_resource
def _model():
    return ensure_model()


def _duration(path):
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    n = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    return n / fps if n > 0 else 0


def show_card(r):
    m = r["metrics"]
    st.metric("Puntuación total", f"{r['total']} / 100" if r["total"] is not None else "–")
    c1, c2, c3 = st.columns(3)
    c1.metric("Golpes izquierda", m["n_left"])
    c2.metric("Golpes derecha", m["n_right"])
    c3.metric("Golpes por minuto", m["punches_per_min"] if m["punches_per_min"] is not None else "–")
    st.markdown("**Subscores**")
    for s in r["subscores"].values():
        if s["score"] is None:
            st.progress(0, text=f"{s['label']}: sin datos")
        else:
            st.progress(s["score"] / 100, text=f"{s['label']}: {s['score']}")


cfg = load_config()

with st.sidebar:
    st.header("Ajustes")
    stance = st.radio(
        "Guardia", ["orthodox", "southpaw"],
        index=0 if cfg["stance"] == "orthodox" else 1,
        format_func=lambda s: "Diestro (orthodox)" if s == "orthodox" else "Zurdo (southpaw)",
    )
    st.header("Cómo grabar")
    st.markdown(
        "- Cámara fija y trasera, en diagonal a unos 45°.\n"
        "- Cuerpo entero en plano, solo tú.\n"
        "- Buena luz, 20-60 segundos.\n"
        "- Sombra o saco, golpes rectos (jab y directo)."
    )

st.title("🥊 Boxeo MVP")
st.caption("Sube un vídeo haciendo sombra o en el saco y obtén tu esqueleto, una ficha con puntuación y tres consejos.")

upload = st.file_uploader("Vídeo (mp4 o MOV del iPhone)", type=["mp4", "mov", "m4v"])

if upload is None:
    st.info("Sube un vídeo para empezar.")
    st.stop()

key = f"{upload.name}-{upload.size}-{stance}"
if st.session_state.get("key") != key:
    _model()
    out_dir = ROOT / "outputs" / "app" / Path(upload.name).stem
    out_dir.mkdir(parents=True, exist_ok=True)
    video_path = out_dir / f"input{Path(upload.name).suffix.lower()}"
    video_path.write_bytes(upload.getbuffer())

    max_s = cfg["video"]["max_seconds"]
    if _duration(video_path) > max_s:
        st.warning(f"El vídeo dura más de {max_s} s: se analizan solo los primeros {max_s} s.")

    bar = st.progress(0.0, text="Empezando")
    try:
        result = analyze(video_path, out_dir, load_config(stance=stance),
                         progress=lambda p, msg: bar.progress(min(p, 1.0), text=msg))
    except Exception as e:  # mostrar el error en la app en vez de una traza
        bar.empty()
        st.error(f"No se ha podido analizar el vídeo: {e}")
        st.stop()
    bar.empty()
    st.session_state.update(key=key, result=result, out_dir=str(out_dir))

r = st.session_state["result"]
out_dir = Path(st.session_state["out_dir"])

if r["metrics"]["pose_detected_pct"] < 50:
    st.warning(
        f"Solo se te detecta en el {r['metrics']['pose_detected_pct']}% del vídeo: "
        "comprueba que se ve el cuerpo entero y hay buena luz."
    )

col_video, col_card = st.columns([3, 2])
with col_video:
    st.video(str(out_dir / "annotated.mp4"))
with col_card:
    show_card(r)

st.subheader("Consejos")
for i, tip in enumerate(r["tips"], 1):
    st.markdown(f"**{i}.** {tip}")

st.download_button(
    "Descargar métricas (JSON)",
    json.dumps(r, ensure_ascii=False, indent=2),
    file_name=f"{Path(upload.name).stem}_metrics.json",
    mime="application/json",
)
