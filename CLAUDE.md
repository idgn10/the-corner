# Boxeo MVP - Analisis de boxeo con IA

## Contexto
Proyecto personal de Ignacio, inspirado en el analisis de padel que estudia
partidos con camaras e IA (estimacion de pose, "esqueleto digital", ficha de jugador y coach virtual).
Este MVP aplica la misma idea al boxeo: un video de alguien boxeando entra,
y sale un analisis con esqueleto, metricas, puntuacion y consejos.

Plazo: 5 dias. Prioridad absoluta: una version funcional de punta a punta lo antes posible,
y despues pulir. Simplicidad por encima de todo.

Ignacio no es programador: explicale siempre en espanol, de forma breve, que has hecho y
como probarlo. Las decisiones de producto (alcance, umbrales, pesos) las toma el.

## Flujo de usuario
1. El usuario sube un video corto (20-60 s) de si mismo haciendo sombra o en el saco.
2. La app procesa el video.
3. Muestra:
   - El video con el esqueleto dibujado encima, contador de golpes e indicador de guardia.
   - Una ficha con las metricas y una puntuacion total de 0 a 100.
   - Tres consejos concretos para mejorar, en espanol.

## Alcance (MoSCoW)
- Must: extraccion de pose, video con esqueleto, deteccion de golpes (mano izquierda/derecha),
  metricas basicas, puntuacion, CLI y app Streamlit local.
- Should: ficha visual cuidada, consejos por reglas, despliegue en Streamlit Community Cloud.
- Could: consejos redactados con la API de Claude, grafica de evolucion entre sesiones.
- Won't (por ahora): distinguir ganchos/uppercuts, varias personas en el plano, tiempo real.

## Stack
- Python 3.11 (MediaPipe da problemas con versiones muy nuevas de Python).
- MediaPipe Pose Landmarker (Tasks API, modo VIDEO). El modelo .task se descarga con un script
  en `models/` (gitignored). Si MediaPipe diera problemas serios, alternativa: Ultralytics YOLO pose.
- OpenCV, numpy, pandas, PyYAML.
- Streamlit para la interfaz.
- imageio-ffmpeg para codificar el video de salida en H.264.

## Estructura del repo
```
boxeo-mvp/
  CLAUDE.md
  README.md
  requirements.txt
  config.yaml            # umbrales y pesos del scoring (editable por Ignacio)
  app.py                 # interfaz Streamlit
  scripts/
    download_model.py
    analyze.py           # CLI: python scripts/analyze.py data/video.mp4
  boxeo/
    pose.py              # landmarks por frame -> DataFrame, suavizado
    metrics.py           # angulos, distancias, guardia, base
    punches.py           # deteccion de golpes
    scoring.py           # subscores 0-100 y total ponderado
    tips.py              # consejos por reglas
    render.py            # dibujo del esqueleto y overlays, escritura H.264
  data/                  # videos de entrada (gitignored)
  outputs/               # resultados (gitignored)
  models/                # modelo descargado (gitignored)
```

## Definicion de metricas (valores iniciales, se calibraran con videos reales)
Indices de landmarks MediaPipe: nariz 0, hombros 11/12, codos 13/14, munecas 15/16,
caderas 23/24, rodillas 25/26, tobillos 27/28.

Reglas generales:
- Normalizar todas las distancias por la anchura de hombros (distancia 11-12) para que no
  dependan de lo cerca que este la camara.
- Ignorar landmarks con visibility < 0.5. Suavizar con media movil o mediana de pocos frames.
- Coordenadas de imagen: la y crece hacia abajo.
- Guardia configurable: orthodox (mano adelantada = izquierda) o southpaw.

Metricas:
1. Guardia: una mano esta "arriba" si la muneca esta a menos de 1.0 anchuras de hombro de la
   nariz y por encima de la altura de los hombros. Metrica: % de frames sin golpe con ambas manos arriba.
2. Mano contraria arriba: en cada golpe, se comprueba si la otra mano mantiene la guardia.
   Metrica: % de golpes con la mano contraria arriba.
3. Extension: angulo del codo (hombro-codo-muneca) en el pico del golpe. Bueno >= 160 grados.
   Metrica: % de golpes bien extendidos y angulo medio.
4. Vuelta a la guardia: tiempo desde el pico del golpe hasta que esa mano vuelve a la guardia.
   Bueno < 0.4 s. Metrica: tiempo medio.
5. Base: distancia entre tobillos / anchura de hombros entre 1.0 y 1.6, y rodillas flexionadas
   (angulo cadera-rodilla-tobillo < 170 grados). Metrica: % de frames con base correcta.
6. Volumen y ritmo: golpes por minuto y velocidad pico media de la muneca.

Deteccion de golpes (punches.py):
- Un golpe se detecta sobre todo por la muneca: maximo local de la distancia muneca-hombro,
  alcanzado alejandola rapido (aumento de alcance + pico de velocidad). El codo solo filtra:
  en el pico debe superar 125 grados (configurable). Asi un golpe corto cuenta como golpe y
  baja la nota de extension (que sigue valorandose con 160 grados).
- En el pico la muneca no puede estar muy por debajo de los hombros (bajar el brazo no es golpe).
- Debounce de 0.25 s por mano para no contar dos veces el mismo golpe.
- Etiquetar mano izquierda/derecha y, segun la guardia, jab (mano adelantada) o directo.

## Scoring
- Cada metrica se convierte en un subscore 0-100 con un mapeo lineal entre un umbral "malo"
  y uno "bueno" (definidos en config.yaml).
- Pesos iniciales: guardia 25, mano contraria 20, extension 20, vuelta a la guardia 15,
  base 10, volumen y ritmo 10.
- Total = media ponderada. Todo en config.yaml para que Ignacio pueda ajustarlo sin tocar codigo.

## Consejos
- Por reglas, sin IA: elegir los 3 subscores mas bajos y generar un consejo en espanol con el
  dato concreto (ej.: "Bajas la mano derecha en el 40% de tus jabs: mantenla pegada a la barbilla").
- La API de Claude es opcional y solo si Ignacio lo pide (coste y narrativa: no usar IA donde
  una regla basta).

## Salidas
- outputs/<nombre>/annotated.mp4 (H.264), metrics.json, landmarks.csv.
- La app Streamlit muestra el video anotado, la ficha y los consejos.

## Problemas conocidos a evitar
- OpenCV con codec mp4v genera videos que el navegador no reproduce: codificar en H.264
  con imageio-ffmpeg.
- Procesar a 720p como maximo para ir rapido. Limitar la app a videos de 60 s.
- No subir nunca videos, outputs ni modelos a git.
- La medicion es 2D: los angulos dependen del angulo de camara. Recomendado: camara fija,
  cuerpo entero, de frente o en diagonal a unos 45 grados.

## Forma de trabajar
- Commits pequenos con mensajes claros; push a GitHub en cada hito que funcione.
- Antes de anadir una dependencia pesada, preguntar.
- Al final de cada paso: resumen breve en espanol de que se ha hecho, como probarlo y que falta.
- Mantener README actualizado (como instalar, como usar, limitaciones).
- MVP: si algo se complica, proponer la version mas simple y seguir.
