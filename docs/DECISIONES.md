# Decisiones para revisar

Decisiones tomadas mientras trabajaba solo (2 oct 2026). Cada una dice qué hice, por qué y cómo cambiarla.

## 1. Orden de los consejos

- **Qué:** los consejos se ordenan por lo que cada métrica resta a la nota total, `(100 − subscore) × peso`.
  Si hay empate (p. ej. varias métricas a 100), va primero la de más peso.
- **Efecto:** en `uno_dos_vago` el primer consejo pasa de "sube el ritmo" a la guardia; en jab y directo
  sigue saliendo el ritmo primero porque es lo único que falla.
- **Cambiarlo:** `make_tips` en `boxeo/tips.py`.

## 2. Rediseño de la app

- **Nombre: "The Corner"** (antes "Esquina"; decidido por Ignacio). Se cambia en `APP_NAME` de `app.py`.
- **Tema oscuro propio** con acento dorado (`.streamlit/config.toml`) y la misma paleta en la ficha,
  la gráfica y el vídeo: azul = mano izquierda, naranja = mano derecha, rojo = guardia baja.
- **Flujo en 3 pasos visibles** (sube, analizamos, mejora). La guardia se elige en la propia pantalla
  (no en la barra lateral, que en el móvil queda escondida) y el análisis empieza con un botón explícito.
- **Jerarquía de resultados:** 1) nota y cifras clave, 2) los 3 consejos, 3) vídeo + gráfica de la sesión +
  momentos para revisar, 4) detalle de cada métrica con "¿Cómo se calcula?" (textos generados con los
  umbrales reales de `config.yaml`, así no se desactualizan).
- **"Pesa X% de la nota"** se muestra normalizado sobre los pesos activos (con la base a 0 suman 90).
- **Momentos para revisar:** tramos con la guardia baja fuera de los golpes, de al menos 0,4 s (uniendo
  huecos de menos de 0,25 s); se muestran los 3 más largos ordenados por tiempo. El botón lleva el vídeo
  medio segundo antes. Se calcula en `metrics.guard_timeline` y se guarda en `metrics.json`.
- **Errores amables:** vídeo ilegible, falta el modelo, fallo genérico (con "Detalle técnico" plegado),
  persona poco visible, y un estado propio cuando no hay golpes.
- **En el móvil** las columnas se apilan y el vídeo vertical tiene un alto máximo del 72% de la pantalla.
- **Pendiente menor:** el botón "Upload" y el texto "1GB per file" del selector de archivos salen en
  inglés; los pone Streamlit y no se pueden traducir con una opción.

## 3. Modo demo

- **Cómo se usa:** botón "Ver un ejemplo" en la pantalla de subida, o el enlace directo `?demo=1`
  (p. ej. `http://localhost:8501/?demo=1`), útil para enseñarlo sin pasos. No sube ni procesa nada.
- **Clip elegido: sombra libre (56/100).** Es el uso real del producto y el que más enseña: los 3 momentos
  de guardia baja, una gráfica con mucha actividad y consejos de corrección. Alternativa si prefieres una
  nota alta para la demo: `python scripts/make_demo.py outputs/uno_dos` (94/100, pero con un solo momento
  y consejos casi todos de refuerzo). Ojo: en sombra hay curvos contados como rectos (limitación conocida).
- **Qué hay en git:** solo `demo/metrics.json` (datos, sin imagen). `demo/annotated.mp4` existe en tu
  ordenador pero no se sube (los vídeos están en `.gitignore`).
- **Sin el vídeo** (lo que pasará online tal cual) el ejemplo muestra ficha, consejos, gráfica y
  momentos, y en lugar del vídeo un aviso de que no está disponible.
- **Para tener el vídeo en la versión online**, tres opciones (decides tú):
  1. **YouTube no listado (recomendada):** sube `demo/annotated.mp4` a YouTube como "No listado" y pon la
     URL en los *secrets* de Streamlit Cloud como `DEMO_VIDEO_URL = "https://youtu.be/..."`. La app ya lo
     lee y los botones de "Momentos para revisar" también saltan al segundo exacto. El vídeo no queda en el repo.
  2. **Adjunto de una Release de GitHub** con la URL directa al .mp4 en `DEMO_VIDEO_URL`. Tampoco va al
     código, pero el enlace es público.
  3. **Subirlo al repo** (13 MB) añadiendo `!demo/annotated.mp4` al `.gitignore`. Es lo más simple pero
     rompe la regla de no subir vídeos y tu cara queda en un repo público.

## 4. README como caso de producto

- **Estructura:** problema, usuario, qué hace, MoSCoW con estado, cómo funciona, métricas y scoring,
  validación y decisiones de calibración (con la tabla codo frente a hombros), limitaciones y siguientes pasos.
  La instalación y el uso van al final: el README lo leerá antes alguien de producto que un desarrollador.

  Si quieres nombrarla, es una línea al principio.
- **Usuario objetivo que he escrito:** boxeador amateur o de fitness boxing que entrena solo. Revísalo:
  es la hipótesis principal del producto.
- **Capturas:** 3 huecos marcados con "📸 CAPTURA PENDIENTE" (resultados, subida y móvil). Las rutas
  esperadas son `docs/img/resultados.png`, `docs/img/subida.png` y `docs/img/movil.png`. No las he puesto
  yo porque salen tu cara y tu casa: decide tú qué enseñar. Para hacerlas, abre la app con `?demo=1`.
- **Siguientes pasos:** los he ordenado poniendo primero validar con usuarios y la evolución entre sesiones.

## 5. Despliegue (preparado, no publicado)

- **Versiones fijadas en `requirements.txt`** (las que funcionan en local). Así un cambio de versión de
  una librería no rompe la app online sin avisar. He comprobado que todas tienen versión para Linux y
  Python 3.11, pero **no he podido probar la instalación en un Linux real**.
- **`packages.txt`:** `libgl1` y `libglib2.0-0` (OpenCV) y `libportaudio2` (MediaPipe carga `sounddevice`
  al importarse; en Linux sin PortAudio podría fallar).
- **Límite de subida: de 1 GB a 300 MB**, porque el servidor gratuito tiene poca memoria. Afecta también
  a local. Un minuto de iPhone en 1080p son ~90 MB; en 4K no cabría (mejor grabar en 1080p).
- **El modelo se descarga al arrancar la app.** Si falla, se reintenta al analizar.
- **Riesgo de velocidad:** el servidor gratuito es más lento que tu Mac y el análisis puede tardar varios
  minutos. Si hiciera falta, una opción sin tocar umbrales es analizar uno de cada dos fotogramas en los
  vídeos de 60 fps (habría que revisar que la detección sigue igual). No lo he hecho.
- Los pasos de la web están en `docs/DESPLIEGUE.md`.

## 6. Rediseño visual "The Corner" (inspirado en un gimnasio de boxeo de Madrid, sin su marca)

- **Solo aspecto:** tema en `.streamlit/config.toml` y un único `styles.css` que carga `app.py`. No cambia
  nada del análisis, la detección ni la puntuación (la nota de los clips sale igual).
- **Orden de secciones:** (01) Tu nota, (02) Consejos, (03) Tu sesión (la gráfica), (04) Momentos para revisar
  y (05) Detalle. Los momentos van con el **vídeo al lado** (en el móvil, justo debajo del vídeo), porque sus
  botones mueven el vídeo: si estuvieran al final de la página habría que subir para ver el salto.
- **Gráfica:** izquierda en negro, derecha en cobre, guardia baja en el rojo apagado de los niveles (es un
  aviso, igual que en los momentos y las notas bajas). Los golpes cortos, más claros.
- **El esqueleto del vídeo mantiene sus colores** (azul izquierda, naranja derecha): cambiarlos exigiría
  regenerar los vídeos y no es parte del rediseño de la interfaz.
- **Franja:** "Tu entrenador entre asaltos" en movimiento suave; se queda quieta si el sistema pide reducir animaciones.
- **No se puede desde la app:** traducir "Upload" y "300MB per file" del selector de archivos (los pone
  Streamlit), ni ocultar el botón "Manage app" y la insignia que añade Streamlit Community Cloud fuera de la app.

## 7. Control de calidad de la grabación (fiabilidad del análisis)

- **Qué es:** en cada análisis se calcula la **fiabilidad: alta / media / baja**, con una frase que explica el
  motivo y cómo grabar mejor. **No cambia ninguna nota** (módulo aparte, `boxeo/quality.py`); la nota se
  muestra siempre, y si la fiabilidad es baja aparece además un aviso destacado arriba del todo.
  **Cambiado en el punto 8:** con fiabilidad baja ya no se muestra la nota.
- **Tres factores, medidos en el tramo activo.** La fiabilidad final es la del peor:

  | Factor | Alta | Media | Baja | Por qué estos valores |
  |---|---|---|---|---|
  | Puntos clave visibles (nariz, hombros, codos, muñecas) | ≥ 75% | 50-75% | < 50% | Tus clips buenos dan 81-99%: de perfil, el brazo de atrás se tapa a ratos y el análisis lo aguanta (los conteos de golpes eran correctos). Por debajo del 50%, la mitad del tiempo no vemos los brazos. |
  | Mano fuera del encuadre | ≤ 3% | 3-10% | > 10% | Tus clips: 0-0,7%. A 60 golpes/min, perder el puño en cada golpe son ~15% del tiempo: > 10% es perder la mayoría de los picos de golpe. |
  | Orientación (anchura de hombros ÷ altura del tronco) | ≤ 0,60 | 0,60-0,70 | > 0,70 | Tus clips: 0,43-0,49 (de lado o en diagonal, con lo que está calibrado). De frente ronda 0,75-0,8 y los golpes van hacia la cámara: el brazo parece más corto. |

- **Mano fuera:** cuenta si la muñeca está a menos de **0,3 anchuras de hombro del borde**, porque el puño
  sobresale más o menos eso por delante de la muñeca. Hallazgo al probarlo: cuando el puño sale de la imagen,
  MediaPipe no da la muñeca por perdida, sino que la **pega al borde** con visibilidad alta, y eso genera
  golpes dobles falsos. Si la muñeca deja de verse en el centro de la imagen se considera tapada por el
  cuerpo, no fuera.
- **Prueba hecha:** recorté 10 s del clip de jabs quitando el 35% izquierdo de la imagen. Resultado: fiabilidad
  **baja** (mano fuera el 11,3% del tiempo) y 13 golpes detectados donde había unos 7, justo el tipo de
  error que el aviso tiene que anticipar.
- **Sin validar con un vídeo real de frente:** los umbrales de orientación salen de proporciones corporales
  típicas, no de un clip tuyo. Graba el clip de prueba de frente (ver informe) para confirmarlos.
- Todos los umbrales están en la sección `quality` de `config.yaml`.

## 8. Con fiabilidad baja, no hay nota (decidido por Ignacio)

- **Regla:** si la fiabilidad es baja, el resultado sale **sin nota total**, igual que cuando no hay golpes:
  mejor ningún dato que uno falso. Se aplica en `boxeo/pipeline.py`, así que la app, la terminal y el
  `metrics.json` dicen lo mismo (`total: null`). `scoring.py` no cambia: las notas por métrica se siguen
  calculando y guardando, y las notas de los 5 clips de prueba (todos con fiabilidad alta) son idénticas.
- **Qué ve el usuario:** "(01) Sin nota" con "El vídeo no permite un análisis fiable", el motivo con el dato
  medido y cómo grabar mejor, y un botón principal "Subir otro vídeo". En "(02) Graba de nuevo así", 3 claves:
  casi de perfil o en diagonal, cuerpo entero en el plano y a 2-3 m de la cámara. El vídeo con el esqueleto y
  el detalle por métrica siguen visibles con la etiqueta **"Orientativo"** y una nota de que no cuentan para
  ninguna nota.
- **Decisión mía:** con fiabilidad baja tampoco se muestran la gráfica de la sesión ni los "Momentos para
  revisar". Son datos de guardia igual de poco fiables y no estaban en la lista de lo que sigue visible.
  Si los quieres como orientativos, es mover dos bloques en `app.py`.
- **Decisión mía:** la ficha sin nota no muestra los golpes por mano ni por minuto (en el clip recortado salían
  13 golpes donde había unos 7). El ritmo sigue en el detalle, marcado como orientativo.
- **Sustituye** al aviso rojo de "toma esta nota con cautela" del punto 7, que ya no tiene sentido porque no hay nota.
- **Terminal:** `scripts/analyze.py` imprime "Sin nota: el vídeo no permite un análisis fiable" y, en lugar
  de los consejos, las 3 claves para grabar.

## 9. Velocidad del análisis (objetivo: clip de 20 s en menos de 1 minuto en el servidor gratuito)

**Medido** con el clip de directos (18,6 s, 1.116 fotogramas a 60 fps, vertical). Modelo de pose:
**pose_landmarker_full** (el intermedio de lite / full / heavy).

| Fase (local, M1 Pro en modo bajo consumo) | Antes | Después |
|---|---|---|
| Lectura, decodificación y reducción a 404×720 | 8,1 s | 7,9 s (sin cambios: ver (a)) |
| Detección de pose | 21,3 s | 21,2 s |
| Métricas, nota y fiabilidad | 0,0 s | 0,0 s |
| Vídeo de salida | 9,4 s | **2,8 s** |
| **Total** | **39,3 s** | **32,4 s** |

| En el servidor (thecorner-boxeo.streamlit.app) | Antes | Después |
|---|---|---|
| Análisis, desde pulsar "Analizar" hasta ver la ficha | 48,2 s | **41,7 s** |
| de ello, vídeo de salida | ~12 s | ~4 s |
| Subida del archivo (27,7 MB, desde la conexión de Ignacio) | 89 s | 83 s |

Un clip de 20 s a 60 fps queda en unos 44 s de análisis en el servidor: **cumple el objetivo para el análisis**.

**Optimizaciones, una a una, con la regla "mismos golpes en los 5 clips y la nota como mucho ±2":**

- **(a) Reducir los fotogramas antes de la pose: descartada.** Los vídeos verticales ya se analizaban a 720 px
  en el lado largo, y bajar a 640 no acelera nada (18,6 ms por fotograma en ambos casos: MediaPipe reduce la
  imagen por su cuenta). Lo caro no era el tamaño sino *cómo* se reducía: OpenCV tarda 5 s en reducir los
  fotogramas de 1080p; ffmpeg lo hace durante la decodificación en 1,7 s en total. Pero con esa reducción la
  imagen cambia mínimamente (1,7 sobre 255 de diferencia media) y en **sombra pasan de 27/13 a 29/12 golpes**
  (y el 1-2 vago sube 2 puntos): dos golpes dudosos, probablemente curvos, cruzan el umbral. Rompe la regla.
  Limitar el lado largo en vídeos horizontales tampoco compensa: haría más pequeña a la persona sin ganar velocidad.
- **(b) Vídeo de salida a 720p como máximo: aplicada.** Ya salía al tamaño de análisis (404×720); su coste era
  volver a decodificar y reducir el original de 1080p. Ahora el vídeo de salida (y solo él) se lee con
  ffmpeg y se codifica con el ajuste `veryfast` de x264. Como no interviene en el análisis, los 5 `metrics.json`
  salen **idénticos bit a bit**.
- **(c) Modelo de pose lite: no aplicada, no hace falta.** Sería un 39% más rápido en la pose (11,4 frente a
  18,6 ms por fotograma), pero cambia los puntos detectados; viendo lo sensible que fue (a), es probable que
  cambiara algún conteo. Queda como palanca si algún día hace falta, previa validación con los 5 clips.
- **(d) Analizar uno de cada dos fotogramas: no aplicada, no hace falta.** Mismo riesgo que (c).

**Barra de progreso:** 4 pasos visibles (Leyendo el vídeo · Detectando tu postura · Calculando tu nota ·
Preparando el vídeo) con "Paso X de 4" y el porcentaje. El reparto de la barra sigue lo que tarda cada fase
(la detección de postura es el ~86% del tiempo).

**Lo que queda fuera de estas optimizaciones: la subida.** Con 27,7 MB y la conexión de Ignacio (~2,7 Mbit/s
de subida) son ~85 s, más que todo el análisis. Depende de la red de cada usuario (con buena wifi o 5G suele
ser bastante menos). Opciones a valorar, no aplicadas:
1. Pedir en la app grabar en **1080p a 30 fps** (Ajustes → Cámara → Grabar vídeo): archivo de aprox. la mitad y
   la mitad de fotogramas que analizar. Pero equivale a (d): los umbrales están calibrados con vídeos a 60 fps,
   así que habría que validarlo con clips grabados a 30 fps.
2. Limitar la duración recomendada a 20-30 s.
