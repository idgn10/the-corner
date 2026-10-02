# Boxeo MVP: plan y prompts para Claude Code

Objetivo: un MVP de análisis de boxeo con IA listo para enseñar el lunes o martes.

| Cuándo | Objetivo |
|---|---|
| **Hoy (jueves)** | Proyecto montado en GitHub + vídeos de prueba grabados |
| **Mañana (viernes)** | Versión funcional de punta a punta (CLI + app local) |
| **Sábado** | Calibración: que detecte bien los golpes y puntúe con sentido |
| **Domingo** | Ficha visual, overlays del vídeo y consejos |
| **Lunes** | App online + README como caso de producto |
| **Martes** | Vídeo demo y margen para arreglos |

No hace falta conectar nada de Google: MediaPipe es una librería de Google, pero funciona sin cuenta.

---

## PASO 0. Montar el proyecto (hoy, 15 minutos)

**Necesitas:** Claude Code instalado y una cuenta de GitHub. Lo demás lo instala o te lo explica Claude Code.

1. Descarga `CLAUDE.md` (el otro archivo que te he pasado).
2. Abre la terminal y crea la carpeta con el archivo dentro.

   **Mac:**
   ```
   mkdir -p ~/Documents/boxeo-mvp && mv ~/Downloads/CLAUDE.md ~/Documents/boxeo-mvp/
   cd ~/Documents/boxeo-mvp && claude
   ```
   **Windows (PowerShell):**
   ```
   mkdir $HOME\Documents\boxeo-mvp; Move-Item $HOME\Downloads\CLAUDE.md $HOME\Documents\boxeo-mvp\
   cd $HOME\Documents\boxeo-mvp; claude
   ```
3. Con Claude Code abierto, pega el **Prompt 0**.
4. Si te pide iniciar sesión en GitHub, escribe dentro de Claude Code:
   ```
   ! gh auth login
   ```
   Elige: GitHub.com → HTTPS → Login with a web browser. Copia el código que te da y pégalo en el navegador.

### Prompt 0: setup
```
Lee CLAUDE.md. Vamos a preparar el proyecto desde cero en esta carpeta:
1. Comprueba si tengo instalados git, GitHub CLI (gh) y Python 3.11. Si falta algo, instálalo tú si puedes o dime exactamente cómo hacerlo en mi sistema.
2. Crea un entorno virtual .venv con Python 3.11, un requirements.txt con el stack de CLAUDE.md, e instala las dependencias.
3. Crea la estructura de carpetas de CLAUDE.md, un .gitignore (.venv, data/, outputs/, models/, cualquier vídeo) y un README básico.
4. Inicializa git y haz el primer commit.
5. Comprueba con `gh auth status` si estoy logueado en GitHub. Si no, para y dime que ejecute `! gh auth login`.
6. Crea el repositorio público boxeo-mvp en mi cuenta con gh y sube el commit.
Al terminar, dame el enlace del repo y un resumen breve en español.
```

---

## PASO 1. Grabar los vídeos de prueba (hoy)

Graba 4 clips de 20-40 segundos y guárdalos en la carpeta `data/` del proyecto:

| Archivo | Qué haces |
|---|---|
| `bueno.mp4` | Sombra con tu mejor técnica |
| `guardia_baja.mp4` | Bajando a propósito la mano que no golpea |
| `sin_extender.mp4` | Golpes cortos, sin estirar el brazo |
| `libre.mp4` | Sombra normal o saco, como entrenas siempre |

**Cómo grabar:**
- Móvil fijo (trípode o apoyado), en diagonal a unos 45 grados.
- Cuerpo entero en plano, de pies a cabeza.
- Buena luz y 60 fps si tu móvil lo permite.
- Solo tú en el plano.

**Por qué los clips "malos":** son tus casos de prueba. Si el sistema no les baja la nota en la métrica correcta, algo falla. Eso es QA funcional.

---

## PASO 2. Versión funcional (hoy y mañana)

### Prompt 1: pipeline de punta a punta
```
Construye la versión funcional de punta a punta según CLAUDE.md, lo más simple posible:
1. scripts/download_model.py y descarga el modelo.
2. pose.py, metrics.py, punches.py, scoring.py, tips.py, render.py y config.yaml con los valores iniciales de CLAUDE.md.
3. scripts/analyze.py, que procese un vídeo y genere en outputs/<nombre>/ el annotated.mp4 (H.264), metrics.json y landmarks.csv.
4. Pruébalo con todos los vídeos de data/ y enséñame una tabla con las métricas y la puntuación de cada uno.
5. Commit y push.
No pules nada todavía: quiero ver el flujo completo funcionando.
```

### Prompt 2: app local
```
Crea app.py con Streamlit: subir un vídeo, procesarlo con el mismo pipeline (con barra de progreso) y mostrar el vídeo anotado, una ficha con la puntuación total y los subscores, y los 3 consejos. Dime cómo arrancarla en local. Commit y push.
```

**Hito de mañana:** subes un vídeo a la app en tu ordenador y te devuelve esqueleto, puntuación y consejos. Aunque sea feo, ya tienes MVP.

---

## PASO 3. Calibración (sábado)

**Antes:** mira `bueno.mp4` y cuenta a mano cuántos golpes das con cada mano. Apúntalo.

### Prompt 3
```
Vamos a calibrar.
1. Para cada vídeo de data/, genera una gráfica del ángulo del codo y la velocidad de la muñeca a lo largo del tiempo, marcando los golpes detectados. Guárdalas en outputs.
2. En bueno.mp4 he contado a mano [X] golpes con la izquierda y [Y] con la derecha. Compáralo con lo detectado y ajusta la detección.
3. Comprueba que los clips malos puntúan peor que bueno.mp4 en su métrica: guardia_baja en "mano contraria arriba" y "guardia", sin_extender en "extensión". Si no es así, propón ajustes de umbrales en config.yaml y explícame cada cambio antes de aplicarlo.
4. Commit y push.
```

---

## PASO 4. Experiencia (domingo)

### Prompt 4
```
Mejora la experiencia:
1. Ficha visual tipo tarjeta deportiva, con diseño propio y sencillo: puntuación total grande, subscores con barras, golpes por mano y golpes por minuto.
2. En el vídeo anotado: contador de golpes, indicador de guardia (verde si está arriba, rojo si no) y un destello breve al detectar cada golpe.
3. Consejos más naturales, siempre con el dato concreto de la sesión.
4. Prueba con todos los clips, commit y push.
```

---

## PASO 5. Online + caso de producto (lunes)

### Prompt 5
```
1. Prepara el despliegue en Streamlit Community Cloud (requirements, packages.txt si hace falta, descarga del modelo al arrancar) y dime paso a paso qué tengo que hacer yo en la web de Streamlit.
2. Reescribe el README como un caso de producto: problema, usuario, alcance MoSCoW, cómo funciona, métricas y scoring, limitaciones conocidas y siguientes pasos. Añade capturas.
3. Commit y push.
```

En Streamlit Community Cloud entras con tu cuenta de GitHub, eliges el repo y te da un enlace público para compartir.

**Opcional (Could):** consejos redactados con la API de Claude. Solo si sobra tiempo; la versión por reglas cuenta mejor tu historia de "no usar IA donde basta una regla".

---

## PASO 6. Demo y envío (martes)

1. **Graba la pantalla (1-2 minutos):** subes un vídeo, sale el análisis y explicas dos decisiones de producto (qué dejaste fuera y por qué).
2. **Mensaje a un contacto:** lo redactamos juntos con el enlace de la app, el repo y la demo.
3. **Margen:** si algo se ha roto, se arregla hoy.

---

## Si algo falla
- **Claude Code se lía o el error se repite:** pídele que pare, resuma qué intenta y proponga la opción más simple.
- **MediaPipe no instala:** casi siempre es la versión de Python. Pide que use 3.11.
- **El vídeo no se reproduce en la app:** es el codec. Pide que lo codifique en H.264.
- **Vas justo de tiempo:** lo imprescindible es el Paso 2 y la demo. Lo demás suma, pero no es obligatorio.
