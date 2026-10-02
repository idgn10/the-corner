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
