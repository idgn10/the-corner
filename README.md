# Boxeo MVP

Análisis de boxeo con IA: subes un vídeo corto haciendo sombra o en el saco y obtienes
el vídeo con el esqueleto dibujado, métricas de técnica, una puntuación de 0 a 100 y tres consejos.

Inspirado en el análisis de pádel con cámaras e IA (estimación de pose, "esqueleto digital", ficha de jugador
y coach virtual), aplicado al boxeo.

## Instalación

Requiere Python 3.11.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/download_model.py   # descarga el modelo de pose en models/
```

## Uso

### App (recomendado)

```bash
source .venv/bin/activate
streamlit run app.py
```

Se abre en el navegador (http://localhost:8501). Subes el vídeo, eliges la guardia en la barra lateral
y ves el vídeo anotado, la ficha con la puntuación y tres consejos. Los vídeos de más de 60 s se recortan.

### Terminal

```bash
python scripts/analyze.py data/mi_video.mp4
```

Acepta .mp4 y .MOV del iPhone (HEVC/HDR, vertical u horizontal). Opción `--stance southpaw` para zurdos.

Genera en `outputs/mi_video/`:
- `annotated.mp4`: vídeo con esqueleto, contador de golpes e indicador de guardia (H.264).
- `metrics.json`: métricas, puntuaciones y consejos.
- `landmarks.csv`: puntos del cuerpo por frame.

Los umbrales y pesos de la puntuación se ajustan en `config.yaml`.

## Cómo grabar el vídeo

- Cámara fija, cuerpo entero en plano, de frente o en diagonal a unos 45 grados.
- Una sola persona, buena luz, 20-60 segundos.
- Mejor con la cámara trasera: si el vídeo sale en espejo, se confunden la mano izquierda y la derecha.

## Limitaciones

- La medición es 2D: los ángulos dependen del ángulo de cámara.
- No distingue ganchos ni uppercuts (solo golpes rectos con mano izquierda/derecha).
- Vídeos de 60 s como máximo; se procesan a 720p como máximo.
