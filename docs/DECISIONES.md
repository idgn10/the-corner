# Decisiones para revisar

Decisiones tomadas mientras trabajaba solo (2 oct 2026). Cada una dice qué hice, por qué y cómo cambiarla.

## 1. Orden de los consejos

- **Qué:** los consejos se ordenan por lo que cada métrica resta a la nota total, `(100 − subscore) × peso`.
  Si hay empate (p. ej. varias métricas a 100), va primero la de más peso.
- **Efecto:** en `uno_dos_vago` el primer consejo pasa de "sube el ritmo" a la guardia; en jab y directo
  sigue saliendo el ritmo primero porque es lo único que falla.
- **Cambiarlo:** `make_tips` en `boxeo/tips.py`.

## 2. Rediseño de la app

- **Nombre: "Esquina"** (la esquina del boxeador es donde el entrenador da los consejos entre asaltos).
  Es provisional: se cambia en una línea (`APP_NAME` y `TAGLINE` en `app.py`).
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
