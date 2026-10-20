# The Corner - Análisis de boxeo con IA

## Contexto
Proyecto personal de Ignacio, inspirado en el análisis de pádel con cámaras e IA: estimación de pose ("esqueleto digital"),
ficha del jugador y consejos. Aquí aplicado al boxeo: entra un vídeo de alguien haciendo sombra y sale
un análisis con esqueleto, métricas, nota de 0 a 100 y tres consejos.

Ignacio no es programador: explícale siempre en español, de forma breve, qué has hecho y cómo probarlo.
Las decisiones de producto (alcance, umbrales, pesos) las toma él. Recomienda, pero no decidas por él.

Principio de producto: **una nota tiene que ser verdad antes que espectacular.** Si el dato no es fiable,
mejor no dar nota que dar una falsa.

## Flujo de usuario
1. El usuario sube un vídeo corto (20-60 s) haciendo sombra o saco, casi de perfil o en diagonal.
2. La app lo procesa (barra de progreso en 4 pasos).
3. Muestra: vídeo con esqueleto, rótulo de cada golpe, contador (rectos, curvos, esquivas) e indicador de guardia;
   ficha con métricas y nota; tres consejos; momentos para revisar; fiabilidad del análisis. Con fiabilidad baja,
   "Sin nota".

## Alcance (MoSCoW)
- Must: pose, vídeo con esqueleto, detección de golpes rectos por mano, métricas, nota, fiabilidad, CLI y app.
- Should: ficha visual cuidada, consejos por reglas, app publicada (hecho).
- Could: consejos con la API de Claude, evolución entre sesiones, ficha compartible.
- Beta: crochet, uppercut y esquiva (no puntúan; ver abajo).
- Won't (por ahora): puntuar curvos/esquivas, varias personas en el plano, tiempo real, cuentas de usuario.

## Stack
- Python 3.11 (MediaPipe da problemas con versiones más nuevas).
- MediaPipe 0.10.35, Pose Landmarker (Tasks API, modo VIDEO), modelo `pose_landmarker_full`.
  El .task se descarga con `scripts/download_model.py` en `models/` (gitignored).
- OpenCV, numpy, pandas, PyYAML, Streamlit, imageio-ffmpeg (vídeo de salida H.264).
- Publicada en Streamlit Community Cloud: https://thecorner-boxeo.streamlit.app/
  **Cada push a `main` redespliega la app pública.**

## Estructura del repo
```
boxeo-mvp/
  CLAUDE.md
  README.md              # caso de producto
  requirements.txt
  packages.txt           # librerías del sistema para Streamlit Cloud
  config.yaml            # umbrales y pesos (editable por Ignacio)
  app.py                 # interfaz Streamlit ("The Corner")
  styles.css             # estilos de la app
  .streamlit/config.toml
  scripts/
    download_model.py
    analyze.py           # CLI: python scripts/analyze.py data/video.mp4
    make_demo.py         # prepara demo/ desde un análisis de outputs/
  boxeo/
    pose.py              # lectura de vídeo, landmarks por fotograma, suavizado
    metrics.py           # ángulos, guardia, mano contraria, vuelta a la guardia, base
    punches.py           # detección de golpes
    moves.py             # curvos y esquivas (beta)
    scoring.py           # subnotas 0-100 y total ponderado
    quality.py           # fiabilidad del análisis (alta / media / baja)
    tips.py              # consejos por reglas
    render.py            # esqueleto y overlays, escritura H.264
    card.py, charts.py   # ficha y gráfica de la app
    pipeline.py          # análisis completo (lo usan app.py y el CLI)
  docs/                  # SCORING, DECISIONES, DESPLIEGUE, ROADMAP, PLAN_Y_PROMPTS
  demo/                  # análisis de ejemplo: metrics.json y annotated.mp4 (único vídeo en git)
  data/, outputs/, models/   # gitignored
```

## Cómo se analiza
Landmarks MediaPipe: nariz 0, hombros 11/12, codos 13/14, muñecas 15/16, caderas 23/24, rodillas 25/26,
tobillos 27/28. Distancias normalizadas por la anchura de hombros. Coordenadas de imagen (y hacia abajo).
Landmarks con visibility < 0.5 se ignoran. Suavizado con mediana de 0,1 s. Guardia orthodox o southpaw.

**Tramo activo:** de 1 s antes del primer golpe a 1 s después del último. Guardia, base y ritmo se miden solo ahí.
La guardia, además, sin la entrada en guardia ni la bajada final: se mide desde la primera vez que las dos manos
están arriba ≥ 0,1 s antes del primer golpe (`guard.initial_up_seconds`, DECISIONES punto 16) hasta la última vez
que lo están ≥ 0,1 s tras el último golpe (`guard.final_up_seconds`; más alto esconde fallos reales, punto 14).

**Detección de golpes (punches.py):**
- Máximo local de la distancia muñeca-hombro, alcanzado alejándola rápido (aumento de alcance + pico de velocidad).
- En el pico, codo > 125° (solo filtra; la extensión se valora con 160°). La muñeca no puede estar muy por
  debajo de los hombros (bajar el brazo no es golpe).
- 0,25 s mínimo entre golpes de la misma mano. Si las dos manos "golpean" a menos de 0,15 s, cuenta la que
  más se aleja (giro del tronco).
- Orthodox: izquierda = jab, derecha = directo. Un "recto" que coincide con un curvo detectado de la misma mano no cuenta.

**Curvos y esquivas (moves.py, beta, sección `moves` de config.yaml):** en T = longitud del tronco de pie.
Crochet: codo a la altura del hombro (≥ −0,08 T), brazo ≤ 80° y muñeca a la altura de la cabeza. Uppercut: muñeca
desde ≥ 0,65 T bajo la nariz, sube > 6 T/s al menos 0,4 T hasta la cara con el codo ≤ 110°. Esquiva: la nariz baja
≥ 0,38 T (sin media/entera; no cuenta tras el último golpe). No son guardia baja; la nota juzga solo los rectos
salvo el volumen, que suma los curvos (no las esquivas). Se muestran en ficha y gráfica solo con fiabilidad no baja.
Sin nota por pocos rectos pero ≥ 5 curvos/esquivas (de lado o diagonal): mensaje "sobre todo curvos y esquivas".
Ver DECISIONES punto 15.

**Mano "arriba" (guard.rule = elbow):** muñeca a menos de 0,8 anchuras de hombro de la nariz y por encima del codo.

**Métricas y pesos:**

| Métrica | Qué mide | Peso |
|---|---|---|
| Guardia | % del tiempo entre golpes con las dos manos arriba (fotograma a fotograma) | 25 |
| Mano contraria | % de golpes con la otra mano arriba al menos el 50 % del golpe | 20 |
| Extensión | % de golpes con el codo a 160° o más | 20 |
| Vuelta a la guardia | Del pico hasta mano arriba y codo < 90° (`recovery.max_elbow_angle`). Si no vuelve antes del siguiente golpe ni en 1,5 s, cuenta 1,5 s. Bueno < 0,4 s | 15 |
| Volumen | Golpes por minuto, rectos + curvos detectados (≈ 20/min = 0, 70/min = 100) | 10 |
| Base | Pies y rodillas | 0 (de perfil un pie tapa al otro) |

Cada subnota es lineal entre un umbral "malo" y uno "bueno" (config.yaml). Total = media ponderada.
**Con menos de 5 golpes rectos no hay nota** (ver Fiabilidad). `metrics.json` guarda `scoring_version` (hoy v2;
v1 = antes de curvos y esquivas). Las notas solo son comparables con la misma versión: subirla (`SCORING_VERSION`
en scoring.py) cuando un cambio mueva notas a propósito (DECISIONES punto 17).

**Fiabilidad (quality.py, sección `quality` de config.yaml):** la peor de cuatro medidas. Golpes detectados
(< 5 = baja, `min_punches`). Y, en el tramo activo ampliado a un mínimo de 10 s o al vídeo entero si dura menos
(`min_seconds`): puntos clave visibles (≥ 75 % alta, < 50 % baja), mano fuera del encuadre (≤ 3 % alta, > 10 %
baja; una muñeca a menos de 0,3 anchuras de hombro del borde cuenta como fuera, porque el detector la "pega" al
borde) y orientación hombros ÷ tronco (≤ 0,60 alta, > 0,70 baja; de frente real midió 0,62, umbral pendiente de
un segundo clip de frente). **Con fiabilidad baja no hay nota** (total: null): pantalla "Sin nota", claves para
grabar de nuevo y detalle en gris como "orientativo". Clip de control: `1,5m.MOV` (de frente) = Sin nota.

**Consejos:** por reglas, sin IA. Las 3 métricas que más restan, (100 − subnota) × peso, con el dato
concreto. Con 85 o más, consejo de refuerzo. La API de Claude solo si Ignacio lo pide.

## Reglas de trabajo (importantes)
- **Validación obligatoria** en cualquier cambio del análisis u optimización: pasar los 5 clips de prueba
  (jab, directo, uno_dos, uno_dos_vago, sombra). Golpes idénticos y nota total ±2. Si no se cumple, no se
  sube: se descarta o se presenta a Ignacio una tabla de antes y después.
- Referencia actual (local, 60 fps): jab 10/0 · 92, directo 0/10 · 90, uno_dos 6/6 · 94,
  uno_dos_vago 15/13 · 72, sombra 22/9 · 82 (25 curvos: 13 crochets y 12 uppercuts en la app; `moves_beta` de metrics.json
  dice 15 y 12 porque cuenta dos veces los 2 golpes que salen como los dos; 11 esquivas). Todos con fiabilidad alta
  (puntuación v2).
  Los 4 clips de rectos no deben tener ningún curvo ni esquiva. Clips de curvos y esquivas: `data/Crochet_*`,
  `Upper_*`, `Medias_*`, `Enteras_*` (frente, 45º, 90º).
- **El análisis lee el vídeo con OpenCV.** Leer con ffmpeg es más rápido pero cambia golpes dudosos;
  la lectura rápida (`iter_frames_fast`) es solo para el vídeo de salida.
- Si un cambio mueve notas, tabla de antes y después **antes** del push (cada push publica la app).
- Antes de añadir una dependencia pesada, preguntar.
- Commits pequeños con mensajes claros. Al terminar: resumen breve en español de qué se hizo, cómo probarlo y qué falta.
- Documentar las decisiones en docs/DECISIONES.md y mantener README y docs/SCORING.md al día.
- **Privacidad de las subidas:** la app no guarda nada en disco. Cada subida va a una carpeta temporal con
  nombre aleatorio que se borra al terminar (también si falla); el nombre del archivo nunca se usa como ruta,
  solo se muestra en la ficha (DECISIONES punto 20).
- No subir nunca vídeos, salvo demo/annotated.mp4 (vídeo del ejemplo, menos de 10 MB). Tampoco outputs,
  modelos ni documentos privados.
- MVP: si algo se complica, proponer la versión más simple.

## Problemas conocidos
- OpenCV con códec mp4v genera vídeos que el navegador no reproduce: codificar en H.264 con imageio-ffmpeg.
- Se procesa a 720 px de alto como máximo y solo el primer minuto. Subida máx. 300 MB.
- Calibrado con vídeos a 60 fps: a 30 fps la nota puede variar unos puntos (validado, no pasa). La app
  recomienda 1080p a 60 fps y avisa con menos de 50 fps. Soportar 30 fps requeriría interpolar la pose.
- En golpes dudosos, recodificar o analizar en otra máquina puede cambiar ±1 golpe (la app publicada da
  sombra 27/12, antes de la beta de curvos). En un mismo equipo el análisis es determinista.
- Medición 2D: los ángulos dependen de la cámara. Grabar con cámara fija, cuerpo entero, de lado o en
  diagonal (de frente da fiabilidad baja).
- Calibrado con un solo usuario, en casa y sin guantes.
