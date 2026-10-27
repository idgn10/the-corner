Español · [English](README.md)

# The Corner · Análisis de boxeo con IA

Prototipo personal de producto. App online: https://thecorner-boxeo.streamlit.app/ (ejemplo sin subir nada: `?demo=1`).

Subes un vídeo de 20-60 segundos haciendo sombra y, en un minuto, recibes tu vídeo con el
esqueleto dibujado, una ficha con tu nota de 0 a 100, tu sesión segundo a segundo y tres consejos
concretos para la próxima vez.

La idea viene del análisis de pádel con cámaras e IA (estimación de pose, "esqueleto digital", ficha de
jugador y coach virtual), aplicada a un deporte en el que casi siempre se entrena solo.

## Cómo se ha construido

Proyecto personal. Yo llevo el producto: defino el problema, el alcance, qué se mide, cómo se puntúa y cómo
se valida. Claude Code escribe el código siguiendo esas decisiones. Las decisiones de producto y de calibración
están documentadas en [docs/DECISIONES.md](docs/DECISIONES.md).

## Probar la app

La app está publicada en Streamlit Community Cloud: https://thecorner-boxeo.streamlit.app/. Es una decisión de
coste: el alojamiento es gratuito mientras se valida el prototipo.

- Para verla sin subir ningún vídeo, abre el modo demo: https://thecorner-boxeo.streamlit.app/?demo=1
- Si lleva tiempo sin uso, la app se duerme. Al abrirla aparece un aviso con un botón para despertarla: hay que
  pulsarlo y esperar a que cargue.
- El servidor gratuito tiene poca potencia, así que el análisis tarda más que en un ordenador.
- Es un prototipo en validación: la nota está calibrada con una sola persona (ver Limitaciones conocidas).
- Qué pasa con tu vídeo: mientras se analiza, se escribe en una carpeta temporal del servidor con nombre
  aleatorio, que se borra entera al terminar, tanto si sale bien como si falla. El vídeo con el esqueleto y la
  ficha se quedan solo en la memoria de tu sesión y se liberan al pulsar "Analizar otro vídeo" o al cerrar la
  sesión. La única excepción es que el servidor se caiga a mitad de un análisis: entonces la carpeta temporal
  puede quedarse hasta que el servidor se reinicie.

---

## 1. El problema

En boxeo amateur la mayor parte del entrenamiento técnico es sombra y saco, sin nadie mirando.
Los errores que más castigan en un combate (bajar la guardia, dejar caer la mano que no golpea,
no extender el brazo, tardar en recoger) son justo los que uno no ve en sí mismo. Las opciones hoy:

- Entrenador o compañero: caro o no siempre disponible.
- Grabarse y revisarlo: lento, y sin criterio claro de qué mirar.
- Apps de fitness con boxeo: cuentan golpes o calorías, no corrigen técnica.

## 2. Usuario

Boxeador amateur o de fitness boxing que entrena solo varias veces por semana, en casa o en el
gimnasio, y que quiere mejorar la técnica entre clase y clase. Tiene un móvil y 5 minutos.
Lo que necesita no es un informe biomecánico: es **saber qué corregir mañana** y poder comprobar si mejora.

## 3. Qué hace

1. Sube tu vídeo desde el móvil (MP4 o MOV del iPhone, tal cual) y elige tu guardia (diestro o zurdo).
2. Lo analizamos: detectamos tu esqueleto fotograma a fotograma, contamos tus golpes y medimos
   tu técnica.
3. Mejora con tu ficha:
   - Nota total de 0 a 100, jabs, directos y golpes por minuto.
   - Tu plan para la próxima sesión: 3 consejos ordenados por lo que más te resta, cada uno con tu dato.
   - Tu vídeo con el esqueleto, un rótulo en cada golpe (jab, directo, crochet, uppercut, esquiva), contador
     de rectos, curvos y esquivas e indicador de guardia (verde/rojo cuando la nota la mide; gris durante los
     golpes, al colocarte y al terminar).
   - Tu sesión, segundo a segundo: gráfica con cada golpe de cada mano y los momentos con la guardia baja.
   - Momentos para revisar: los tramos más largos con la guardia baja; un clic y el vídeo salta a ese segundo.
   - Detalle de cada métrica con un "¿Cómo se calcula?" en lenguaje sencillo.

## 4. Alcance (MoSCoW)

| Prioridad | Qué | Estado |
|---|---|---|
| Must | Extracción de pose, vídeo con esqueleto, detección de golpes por mano, métricas, puntuación, CLI y app local | Hecho |
| Should | Ficha visual cuidada, consejos por reglas, despliegue en Streamlit Community Cloud | Hecho (app publicada en Streamlit Community Cloud) |
| Could | Consejos redactados con la API de Claude, evolución entre sesiones | Descartado por ahora (no usar IA generativa donde una regla basta) |
| Beta | Detectar crochets, uppercuts y esquivas (no puntúan; dejan de contar como recto y como guardia baja) | En pruebas, calibrado con un solo boxeador |
| Won't (por ahora) | Puntuar curvos y esquivas, varias personas en plano, tiempo real | Fuera de alcance |

Además del plan inicial: gráfica de la sesión, momentos para revisar con salto al vídeo y modo demo.

## 5. Cómo funciona

```
vídeo (MP4/MOV) ─► pose (MediaPipe, 33 puntos/frame) ─► suavizado ─► golpes ─► métricas ─► notas ─► consejos
                                                                           └──► vídeo anotado (H.264)
```

- Pose: MediaPipe Pose Landmarker en modo vídeo, sobre el vídeo reducido a 720p como máximo.
  Se ignoran los puntos con visibilidad < 0,5 y se suaviza con mediana móvil de 0,1 s.
- Escala: todas las distancias se miden en "anchuras de hombro" para no depender de lo cerca que esté la cámara.
- Golpes: se detectan por la muñeca: el momento en que está más lejos del hombro, al que llega
  alejándose rápido (aumento de alcance + pico de velocidad). El codo solo filtra: tiene que pasar de 125°.
  Si las dos manos "golpean" a la vez (menos de 0,15 s), solo cuenta la que más se aleja.
- Tramo activo: guardia y ritmo se miden desde 1 s antes del primer golpe hasta 1 s después del
  último, para que no cuente entrar en plano ni prepararse. Bajar los brazos al terminar tampoco cuenta
  como guardia baja.
- Consejos: por reglas, sin IA generativa: rápido, gratis, explicable y siempre con el dato real.

Stack: Python 3.11 · MediaPipe · OpenCV · NumPy/pandas · Streamlit + Altair · imageio-ffmpeg.

## 6. Métricas y scoring

Cada métrica se convierte en una nota de 0 a 100 con una recta entre un umbral "malo" (0) y uno
"bueno" (100). La nota total es la media ponderada. Todo se ajusta en [`config.yaml`](config.yaml) sin tocar código.
Explicación completa, con un ejemplo paso a paso: [docs/SCORING.md](docs/SCORING.md).

| Métrica | Qué mide | 0 puntos | 100 puntos | Peso |
|---|---|---|---|---|
| Guardia | % del tiempo entre golpes con las dos manos arriba | ≤ 40% | ≥ 90% | 25 |
| Mano contraria arriba | % de golpes en los que la otra mano protege la cara | ≤ 40% | ≥ 90% | 20 |
| Extensión | % de golpes con el codo a ≥ 160° en el pico | ≤ 30% | ≥ 80% | 20 |
| Vuelta a la guardia | Segundos medios desde el pico hasta volver a la guardia (mano arriba y codo < 90°) | ≥ 0,8 s | ≤ 0,4 s | 15 |
| Volumen y ritmo | Golpes por minuto en el tramo activo | ≤ 20 | ≥ 70 | 10 |
| ~~Base~~ | Separación de pies y rodillas flexionadas | - | - | 0 (ver limitaciones) |

Mano "arriba": la muñeca está a menos de 0,8 anchuras de hombro de la nariz y por encima del codo.

Consejos: se eligen las 3 métricas que más restan a la nota, `(100 − nota) × peso`. Con nota ≥ 85
el consejo es de refuerzo; por debajo, de corrección y siempre con el dato (p. ej. *"Bajas la mano
izquierda en el 54% de tus directos: mantenla pegada a la barbilla mientras golpeas con la otra."*).

## 7. Validación y decisiones de calibración

Grabé 5 clips con el iPhone (casi de perfil, 60 fps), cada uno pensado como **caso de prueba**:
si el sistema no baja la nota en la métrica correcta, algo falla.

| Clip | Qué hice | Golpes detectados (izq. / der.) | Nota (v2) |
|---|---|---|---|
| Jabs | Solo jabs | 10 / 0 | 92 |
| Directos | Solo directos | 0 / 10 | 90 |
| 1-2 bueno | Combinaciones con buena técnica | 6 / 6 | 94 |
| 1-2 vago | Las mismas combinaciones, con peor técnica a propósito | 15 / 13 | 72 |
| Sombra libre | Sombra con movimiento, curvos y esquivas | 22 / 9 rectos + 25 curvos (13 crochets y 12 uppercuts) y 11 esquivas (beta) | 82 |

Todos los conteos coinciden con los golpes reales. El 1-2 "vago" pierde 22 puntos frente al bueno, y los
pierde donde debe: guardia (100 → 65), mano contraria (87 → 70) y extensión (100 → 69).

Las notas son de la versión de puntuación v2 (curvos y esquivas en beta). Solo son comparables entre análisis
con la misma versión: con la v1 sombra daba 57 (ver `docs/DECISIONES.md`, punto 17).

Decisiones tomadas con los datos:

1. Detección por la muñeca, codo mínimo de 125° (el plan inicial pedía pasar de 110° a 150°).
   Con el criterio inicial, un golpe corto no contaba como golpe: el clip "sin extender" habría
   tenido menos golpes en vez de peor extensión. Ahora un golpe corto cuenta y baja la nota de extensión.
2. Filtro de golpes simultáneos. Al girar el tronco en un jab, la mano de atrás se mueve lo justo
   para parecer un golpe. Si las dos manos "golpean" a menos de 0,15 s, solo cuenta la que más se aleja.
3. Tramo activo. Los primeros 10 s del clip de jabs eran entrar en plano y prepararse: bajaban la
   guardia (44 puntos) y el ritmo sin motivo.
4. Base con peso 0. Grabando de perfil, un pie tapa al otro y los tobillos salen "juntos" en la
   imagen (18-31 px frente a 80 px de hombros). Medirlo daba 0% en todos los clips: no es mala técnica,
   es que la cámara no lo puede ver.
5. Regla de guardia: codo en vez de hombros. La regla inicial ("muñeca por encima de la línea de
   hombros") castigaba la buena técnica: al meter la barbilla o agacharse para esquivar, la mano está
   en la cara pero por debajo de los hombros. Comparé dos alternativas sobre los 5 clips:

   | Clip | Hombros (con margen de 0,15) | Codo (nariz < 0,8) |
   |---|---|---|
   | 1-2 bueno | 90 | 94 |
   | 1-2 vago | 59 | 71 |
   | Sombra (nota de guardia) | 0 | 14 |

   Cifras del momento de la decisión; con las reglas actuales la guardia de sombra sale en 16.

   Elegí la del codo aunque separa algo menos el bueno del vago (23 puntos frente a 31). Revisando
   fotogramas de sombra entre golpes, la de hombros marcaba "guardia baja" cuando estaba agachado con
   las manos en la cara, y daba 0 en guardia a una sombra en la que las manos están arriba casi la
   mitad del tiempo. La del codo no depende de la inclinación del cuerpo, que es lo que cambia
   en cuanto el usuario se mueve.
6. Los curvos no se filtran subiendo el codo mínimo a 140°. Eso filtraba algunos ganchos, pero también
   golpes rectos cortos del clip "vago", que deben contar y penalizar. En su lugar, los curvos se detectan
   aparte (beta, ver abajo) y solo entonces dejan de contar como rectos.
7. Vuelta a la guardia con el brazo recogido. De perfil, el puño del jab estirado queda en la imagen
   delante de la cara y la regla de guardia lo daba por "arriba": salían vueltas de 0,0 s, imposibles.
   Ahora la mano tiene que estar arriba y con el codo a menos de 90°, y antes del siguiente golpe.
   En sombra, los golpes con vuelta en menos de 0,1 s bajan de 17 a 3; las notas totales no cambian.

## 8. Limitaciones conocidas

- Calibrado con una sola persona y 5 clips. Falta probarlo con otros cuerpos, niveles y móviles.
- Hay que grabar de una forma concreta: cámara fija, cuerpo entero, de lado o en diagonal y una sola persona en
  imagen. Con otros ángulos de cámara habría que recalibrar; de frente no da nota.
- Ganchos, uppercuts y esquivas se detectan en modo de prueba y todavía no cuentan para la nota.
- No valora la posición de los pies: grabando de lado, un pie tapa al otro.
- Los resultados pueden variar un poco: con vídeos a menos de 50 fps la nota sale como orientativa, y la app
  publicada puede contar 1-2 golpes distintos que el análisis en local.

Detalle de cada limitación en [docs/DECISIONES.md](docs/DECISIONES.md#limitaciones-en-detalle).

## 9. Siguientes pasos

1. Piloto de validación con un gimnasio de boxeo local (en preparación) para medir el acierto con otros boxeadores.
2. Validar con 5-10 usuarios reales (otros cuerpos, niveles y ángulos de cámara) y recalibrar umbrales.
3. Evolución entre sesiones: guardar cada análisis y enseñar la tendencia de la nota y de cada métrica.
   Es lo que convierte un análisis puntual en un hábito.
4. Base medible: pedir un ángulo de cámara en diagonal o estimar la profundidad (pose 3D de MediaPipe).
5. Sacar de beta los curvos y las esquivas: validarlos con otros boxeadores y decidir si puntúan.
6. Rondas guiadas: "3 minutos de jab-directo" con objetivos, y comparar la sesión con la anterior.
7. Consejos redactados con IA solo si las pruebas con usuarios muestran que las reglas se quedan cortas.

---

## Instalación y uso

Requiere Python 3.11.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/download_model.py   # descarga el modelo de pose en models/ (la app también lo hace sola)
```

App:

```bash
streamlit run app.py
```

Se abre en http://localhost:8501. Para enseñar un ejemplo sin subir nada: http://localhost:8501/?demo=1
(el ejemplo se prepara con `python scripts/make_demo.py outputs/<clip>`).

Terminal:

```bash
python scripts/analyze.py data/mi_video.mov [--stance southpaw]
```

Genera en `outputs/mi_video/`: `annotated.mp4` (H.264), `metrics.json` (métricas, notas, consejos,
golpes y línea de tiempo) y `landmarks.csv` (puntos del cuerpo por frame).

Cómo grabar (el mismo texto en toda la app, en `boxeo/recording.py`): móvil en vertical y fijo, a 1,2 m del
suelo y recto, con la cámara trasera; a unos 2 m, en guardia mirando al móvil y girando un poco hasta que quede
entre la frente y el hombro adelantado (golpeando siempre hacia donde se mira); cuerpo entero con un palmo de
margen por encima de los brazos y por debajo de los pies; una prueba de 5 segundos que se graba, se mira y se borra
antes de grabar de verdad (cara y dos puños a la vista, nada fuera de la imagen); sombra libre y quieto en el sitio, sin saco, sin guantes y sin vendas;
de 20 a 60 s a 60 fotogramas por segundo; solo una persona en la imagen, con buena luz y sin espejos detrás.

Despliegue: ver [docs/DESPLIEGUE.md](docs/DESPLIEGUE.md).

## Estructura

```
app.py                 interfaz Streamlit
config.yaml            umbrales y pesos (editable sin tocar código)
boxeo/
  pose.py              vídeo -> puntos del cuerpo por frame, suavizado
  metrics.py           ángulos, guardia, base, tramo activo, línea de tiempo
  punches.py           detección de golpes
  scoring.py           notas 0-100 y total ponderado
  tips.py              consejos por reglas
  render.py            vídeo anotado en H.264
  card.py, charts.py   ficha visual y gráfica de la sesión
  pipeline.py          todo junto (lo usan la app y el CLI)
scripts/               analyze.py, download_model.py, make_demo.py
demo/                  análisis de ejemplo para el modo demo (metrics.json y annotated.mp4,
                       el único vídeo en git)
docs/                  plan, roadmap, decisiones y despliegue
```
