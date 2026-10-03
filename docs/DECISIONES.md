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
  **Actualizado (decidido por Ignacio): opción 3.** `demo/annotated.mp4` se sube al repo como única excepción
  (`!demo/annotated.mp4` en `.gitignore`), así el ejemplo online tiene vídeo sin configurar nada. Recodificado
  de 12,7 MB a **4,7 MB** (H.264, CRF 24, misma resolución 404×720 y 59,94 fps; SSIM 0,985 frente al original,
  sin diferencias visibles en el esqueleto ni en los textos).
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
  **Actualizado en el punto 13:** el primer clip real de frente da 0,62, no 0,75-0,8; umbral sin cambiar.
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
   así que habría que validarlo con clips grabados a 30 fps. **Validado en el punto 12: no cumple.**
2. Limitar la duración recomendada a 20-30 s.

## 10. Vuelta a la guardia: la mano tiene que volver con el brazo recogido (decidido por Ignacio)

- **Problema:** en sombra salían vueltas a la guardia de 0,0-0,05 s (de 0 a 3 fotogramas), media 0,16 s y
  nota 100, con la guardia en el 47%. Físicamente imposible.
- **Causa:** la vuelta se medía desde el pico del golpe hasta que esa mano cumplía la regla de guardia (muñeca
  a menos de 0,8 anchuras de hombro de la nariz y por encima del codo). Grabando de perfil, **el puño del jab
  estirado queda en la imagen justo delante de la cara**, a la altura de la nariz, así que la regla lo daba
  por "arriba" con el brazo todavía extendido. Ejemplo: el jab del segundo 11,6 de sombra contaba como
  "arriba" ya en el pico (codo a 152°), y el brazo siguió estirado (170-178°) 10 fotogramas más. En sombra,
  22 de los 40 golpes se daban por recuperados con el codo todavía por encima de 100°.
- **Primera propuesta, descartada:** medir hasta que la mano esté "arriba" según la regla del codo, como mucho
  hasta el siguiente golpe. No cambiaba nada en los 5 clips: la mano contaba como "arriba" casi en el acto,
  mucho antes del siguiente golpe.
- **Regla nueva:** la mano ha vuelto cuando está arriba **y con el brazo recogido: codo a menos de 90°**
  (`recovery.max_elbow_angle`). 90° queda en medio: en guardia el codo suele estar a 30-60° y en el pico de los
  golpes detectados siempre pasa de 125°. Tiene que volver **antes del pico del siguiente golpe** (de cualquier
  mano); si no, el golpe queda como no recuperado (`recovered: false` en `metrics.json`) y cuenta **1,5 s**,
  igual que ya pasaba si no volvía en 1,5 s. La escala (0,8 s / 0,4 s) y los pesos no cambian.

| Clip | Golpes | Vuelta antes (nota) | Vuelta ahora (nota) | Golpes con vuelta < 0,1 s | Nota total |
|---|---|---|---|---|---|
| Jabs | 10 | 0,19 s (100) | 0,23 s (100) | 0 → 0 | 92 → 92 |
| Directos | 10 | 0,46 s (85) | 0,46 s (85) | 0 → 0 | 90 → 90 |
| 1-2 bueno | 12 | 0,29 s (100) | 0,29 s (100) | 2 → 1 | 94 → 94 |
| 1-2 vago | 28 | 0,35 s (100) | 0,37 s (100) | 4 → 1 | 71 → 71 |
| Sombra | 40 | 0,16 s (100) | 0,21 s (100) | **17 → 3** | 56 → 56 |

- **Sombra:** los golpes con vuelta en menos de 0,1 s bajan **de 17 a 3**, y la vuelta más rápida pasa de
  0,0 a 0,05 s. En los 3 que quedan el codo baja de 145-175° a menos de 90° en 3-5 fotogramas: muy rápidos,
  pero ya con el brazo recogido. En los 5 clips solo hay un golpe no recuperado, y ya lo era antes: un jab
  del 1-2 vago (segundo 11,6) tras el que la mano no vuelve a la guardia en 1,5 s.
- **Efecto secundario:** la guardia baja un poco (sombra 46,9% → 45,7%; 1-2 vago 71,6% → 71,1%, nota de
  guardia 63 → 62), porque los fotogramas en que la mano está volviendo ya no cuentan como tiempo entre golpes
  con la mano arriba. Ninguna nota total cambia.
- **Sombra sigue con 100 en esta métrica:** 0,21 s está por debajo del umbral "bueno" (0,4 s) y es un tiempo
  creíble para recoger un jab rápido. Ya no contradice el 46% de guardia: recoge rápido después de golpear,
  pero entre golpes lleva las manos bajas. Si se quiere que la métrica distinga más, habría que endurecer la
  escala (pendiente de decidir, no tocada).

## 11. App publicada frente a análisis en local

- **En un mismo equipo el análisis es determinista:** sombra analizado tres veces en local (dos con
  `scripts/analyze.py` y el análisis guardado en `outputs/`) da los mismos puntos del esqueleto bit a bit, los
  mismos 40 golpes en los mismos fotogramas y las mismas notas.
- **La app publicada puede variar ±1-2 golpes frente al análisis en local** en clips con golpes dudosos: el
  servidor decodifica el vídeo de forma ligeramente distinta y algún golpe al límite de los umbrales cae al
  otro lado. Ejemplo: **sombra da 27/13 golpes (izq./der.) en local y 27/12 online.** Es el mismo tipo de
  efecto que se vio al probar la reducción con ffmpeg (punto 9 (a)).
- Anotado en las limitaciones del README.

## 12. Validación a 30 fps: no cumple, se recomienda grabar a 60 fps (decidido por Ignacio)

- **Por qué:** el iPhone graba por defecto en 1080p a 30 fps y todos los clips de calibración están a 60 fps.
- **Cómo:** los 5 clips, convertidos a 30 fps con ffmpeg quitando un fotograma de cada dos (misma resolución,
  HEVC a ~8 Mbit/s, aprox. lo que usa el iPhone en 1080p a 30 fps). **Control:** el mismo vídeo recodificado a
  60 fps sin quitar fotogramas, para separar el efecto de recodificar del de los fps.
  Regla: golpes idénticos y nota total ±2.

| Clip | Golpes 60 → 30 | Nota 60 → 30 | Control: 60 recodificado | Qué cambia a 30 fps | ¿Cumple? |
|---|---|---|---|---|---|
| Jabs | 10/0 → 10/0 | 92 → 92 | 10/0 · 92 | nada | Sí |
| Directos | 0/10 → 0/10 | 90 → 90 | 0/10 · 89 | nada | Sí |
| 1-2 bueno | 6/6 → 6/6 | **94 → 86** | 6/6 · 97 | mano contraria 87 → 53 | **No** |
| 1-2 vago | 15/13 → 15/13 | 71 → 73 | 14/13 · 73 | extensión 69 → 83 | Sí (+2) |
| Sombra | **27/13 → 28/13** | **56 → 64** | 27/12 · 54 | extensión 75 → 96, mano contraria 43 → 60 | **No** |

| Los 5 clips juntos | 60 fps | 30 fps |
|---|---|---|
| Tamaño de archivo | 202 MB | 138 MB (−31%) |
| Tiempo de análisis (local) | 233 s | 111 s (−52%) |

**Causas** (reglas que dependen de los fotogramas por segundo):

1. **Suavizado (sesgo nuestro, la causa principal).** La mediana de 0,1 s son 7 fotogramas a 60 fps y solo 3 a
   30: a 30 recorta menos los picos, el codo sale más estirado en el pico del golpe y la extensión se infla.
   Comprobado con la misma pose de 60 fps quitando un fotograma de cada dos: la extensión de sombra sube de 75
   a 100. Una ventana de 5 fotogramas a 30 fps se pasa al otro lado (sombra pierde 6 directos).
2. **Mano contraria (azar).** Hay golpes con la otra mano arriba justo el ~50% del tiempo; con la mitad de
   fotogramas caen a un lado u otro. En el 1-2 bueno (12 golpes) cada uno de esos golpes vale ~3,7 puntos de nota total.
3. **Otras reglas por fotogramas, con poco efecto aquí:** la velocidad de la muñeca (entre fotogramas vecinos),
   las ventanas en segundos redondeadas a fotogramas (0,4 / 0,25 / 0,15 s), el fotograma extra tras el pico al
   medir el codo y la resolución del tiempo de vuelta a la guardia (17 frente a 33 ms).
4. **MediaPipe** sigue a la persona de un fotograma al siguiente: a 30 fps los puntos salen algo distintos.

- **Ruido de fondo:** solo recodificar a 60 fps ya rompe la regla en el 1-2 vago (pierde un golpe) y en sombra
  (27/12, igual que la app publicada, punto 11), y el 1-2 bueno sube 3 puntos. La regla es más estricta que la
  estabilidad actual con golpes dudosos, pero la extensión inflada a 30 fps es un sesgo real, no ruido.
- **Aplicado:** en "Cómo grabar" se recomienda 1080p a 60 fps, con la ruta en el iPhone (Ajustes > Cámara >
  Grabar vídeo > 1080p a 60 fps). Si el vídeo tiene menos de 50 fps, la ficha avisa en tono amable de que la
  nota puede variar unos puntos. El análisis no cambia.
- **Coste de pedir 60 fps:** archivos ~45% más grandes. El clip de directos pesa 27,7 MB a 60 fps y 19 MB a 30
  (subida de ~83 s frente a ~57 s con la conexión de Ignacio, punto 9), y el análisis tarda el doble.
- **Siguiente paso:** interpolar la pose a 60 fps antes de aplicar las reglas, para que trabajen igual que en la
  calibración. Probado aparte: con la pose de 60 fps sin uno de cada dos fotogramas cumplen 4 de 5 clips; con los
  vídeos convertidos siguen fallando el 1-2 bueno (90) y sombra (48, 27/11). Hay que validarlo con 2-3 clips
  **grabados a 30 fps directamente con el iPhone** (no convertidos).

## 13. Clip real de frente: con menos de 5 golpes no hay nota y la fiabilidad se mide en al menos 10 s (decidido por Ignacio)

- **Prueba:** `1,5m.MOV`, 9 s grabados de frente a 1,5 m haciendo jabs y directos. Se esperaba "Sin nota" y salió
  **nota 21 con fiabilidad media**: 1 solo golpe detectado, "2 s analizados", vuelta a la guardia de 0,03 s y
  consejos tipo "el 100% de tus jabs".
- **Causa:** la fiabilidad se medía solo en el tramo activo, que con un único golpe son **2,3 s** alrededor de él.
  En esos 2,3 s todo parecía aceptable; en el vídeo entero, no:

  | Medida | Alta / baja | Tramo activo (2,3 s) | Vídeo entero (9,2 s) |
  |---|---|---|---|
  | Puntos visibles | ≥ 75% / < 50% | 100% (alta) | 88% (alta) |
  | Mano fuera del encuadre | ≤ 3% / > 10% | 8,1% (media) | 12,9% (baja) |
  | Orientación hombros ÷ tronco | ≤ 0,60 / > 0,70 | 0,58 (alta) | 0,62 (media) |
  | **Resultado** | | **media → nota 21** | **baja** |

  De frente los golpes van hacia la cámara y en 2D casi no se ven: por eso solo se detectó 1 golpe.
- **La orientación de frente real da 0,62, no 0,75-0,8** como se suponía en el punto 7 (proporciones típicas,
  sin validar). Por segundos va de 0,55 a 0,71 y solo el 10% de los fotogramas pasa de 0,70; los clips de
  perfil dan 0,43-0,49. **Umbral sin cambiar** (baja > 0,70): un solo clip no basta para recalibrar, falta un
  segundo clip de frente.
- **Cambios:**
  - **Con menos de 5 golpes, fiabilidad baja y sin nota** (`quality.min_punches: 5`), en la línea de "sin golpes
    no hay nota". Con 1-4 golpes cada golpe pesa más del 20% en los porcentajes ("el 100% de tus jabs"); el clip
    de prueba con menos golpes tiene 10. Motivo en la ficha: "Solo hemos detectado N golpes", con el mensaje
    "Hemos detectado muy pocos golpes para darte una nota fiable. Graba al menos 20 segundos con jabs y
    directos, de lado o en diagonal: de frente casi no vemos los golpes." Si hay varios motivos en baja, se
    muestra este primero. Un vídeo sin ningún golpe también sale ahora en la pantalla "Sin nota" ("No hemos
    detectado ningún golpe").
  - **La fiabilidad se mide en al menos 10 s** (`quality.min_seconds: 10`): el tramo activo se amplía, centrado,
    hasta 10 s, o al vídeo entero si dura menos. En los 5 clips de prueba no cambia nada (su tramo activo dura
    de 12,8 a 38 s). La ficha "Sin nota" dice los segundos en los que se ha medido (9 s en este clip, no 2).
- **Descartado:** medir la fiabilidad en todo el vídeo. El clip de jabs se quedaba con 76,2% de puntos visibles,
  a 1,2 del umbral de alta, porque cuentan los segundos de entrar y salir del plano.
- **Validación** (pipeline completo, en local):

  | Clip | Golpes (izq./der.) | Antes: fiabilidad · nota | Después: fiabilidad · nota | Segundos medidos |
  |---|---|---|---|---|
  | Jabs | 10/0 | alta · 92 | alta · 92 | 16,7 |
  | Directos | 0/10 | alta · 90 | alta · 90 | 17,8 |
  | 1-2 bueno | 6/6 | alta · 94 | alta · 94 | 12,8 |
  | 1-2 vago | 15/13 | alta · 71 | alta · 71 | 35,5 |
  | Sombra | 27/13 | alta · 56 | alta · 56 | 38,1 |
  | De frente a 1,5 m | 1/0 | media · 21 | **baja · Sin nota** (pocos golpes) | 2,3 → 9,2 |

## 14. Bajar los brazos al terminar no cuenta como guardia baja (decidido por Ignacio)

- **Problema:** la guardia se medía hasta 1 s después de la vuelta del último golpe (fin del tramo activo), así
  que bajar los brazos al terminar el ejercicio contaba como guardia baja. En el 1-2 bueno, el único "momento
  para revisar" era el segundo 12,4 ("bajas las dos manos 0,4 s"): el final del ejercicio.
- **Regla:** la guardia se mide hasta la **última vez que tienes las dos manos arriba** (al menos 0,1 s,
  `guard.final_up_seconds`) después del último golpe. Si bajas las manos y ya no las vuelves a subir, has
  terminado. Solo acorta el tramo de la guardia (nota de guardia, gráfica y momentos para revisar); ritmo,
  base, "segundos analizados" y fiabilidad siguen con el tramo activo de siempre.
- **Descartado: cortar justo en la vuelta del último golpe (o con un margen fijo).** Escondía un fallo real en
  el 1-2 vago: en 34,5-35,5 s las muñecas quedan 0,5 anchuras de hombro por debajo de los hombros, igual que en
  sus bajadas a propósito (10,6 / 20,8 / 27,7 s), y después **vuelve a subir la guardia** (35,47-35,75 s). Su
  nota pasaba de 71 a 74 (+3, fuera de la regla de ±2).
- **Por qué 0,1 s:** los parpadeos de "manos arriba" por ruido duran menos de 0,1 s (sombra tiene uno de 0,02 s
  en plena bajada final) y la última guardia real del 1-2 vago dura 0,28 s. Con 0,3 s ya se escondía su fallo.
  Si el valor se queda corto, el efecto es el de antes (cuenta la bajada final), no esconder fallos.
- **Las 4 bajadas que dejan de contar son finales:** las manos ya no vuelven a subir hasta el final del vídeo
  (1-2 bueno: muñeca derecha 1,3 anchuras de hombro por debajo de los hombros, camino de la cadera; sombra: las
  dos abajo desde 37,07 s hasta el final, 38,8 s; jabs y directos: sin momento, solo cambia el %).
- **No cambia** el texto "Guardia baja" del vídeo anotado, que se dibuja fotograma a fotograma.
- **Validación** (pipeline completo, en local):

  | Clip | Golpes | Guardia % | Nota guardia | Nota total | Momentos que desaparecen |
  |---|---|---|---|---|---|
  | Jabs | 10/0 = | 97,4 → 100 | 100 → 100 | 92 → 92 | — |
  | Directos | 0/10 = | 93,2 → 96,1 | 100 → 100 | 90 → 90 | — |
  | 1-2 bueno | 6/6 = | 91,2 → 95,5 | 100 → 100 | 94 → 94 | 12,4 s (las dos, 0,4 s) |
  | 1-2 vago | 15/13 = | 71,1 → 71,1 | 62 → 62 | 71 → 71 | — (se mantiene el 34,5 s, fallo real) |
  | Sombra | 27/13 = | 45,7 → 48,1 | 11 → 16 | 56 → 57 | ninguno de los 3; sale de la gráfica el tramo 37,1-38,0 s |

  Clip de frente (`1,5m.MOV`): sigue "Sin nota" (1 golpe). El ejemplo (`demo/metrics.json`, sombra) se ha
  regenerado: 57/100; el vídeo del ejemplo no cambia.
- **Pendiente (no incluido):** al principio de sombra hay un tramo parecido (0,0-0,75 s, mano derecha baja antes
  del primer golpe, entrando en guardia).
