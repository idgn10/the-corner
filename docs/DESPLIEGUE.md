# Despliegue en Streamlit Community Cloud

El repo ya está preparado. Tú solo tienes que hacer los pasos de la web (unos 10 minutos más el primer arranque).

## Qué está preparado en el repo

| Archivo | Para qué |
|---|---|
| `requirements.txt` | Librerías de Python con versiones fijadas (las probadas en local y resueltas para Linux con Python 3.11) |
| `packages.txt` | Librerías del sistema que necesita el servidor Linux, sacadas de las dependencias reales de los paquetes: `libgl1`, `libglib2.0-0`, `libsm6`, `libxext6` (OpenCV), `libegl1`, `libgles2` (MediaPipe) y `libportaudio2` (`sounddevice`, que carga MediaPipe) |
| `.streamlit/config.toml` | Tema visual y límite de subida de 300 MB |
| `app.py` | Descarga el modelo de pose (9 MB) al arrancar, porque `models/` no está en git |
| `demo/metrics.json` | Datos del ejemplo para el botón "Ver un ejemplo" (sin vídeo, ver abajo) |

## Pasos en la web

1. Entra en **https://share.streamlit.io** y pulsa **Continue with GitHub**. Autoriza a Streamlit a ver tus repos
   (cuenta `idgn10`).
2. Pulsa **Create app** (arriba a la derecha) y elige **Deploy a public app from GitHub**
   (puede aparecer como "Yup, I have an app").
3. Rellena:
   - **Repository:** `idgn10/boxeo-mvp`
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **App URL:** el subdominio que quieras, por ejemplo `esquina-boxeo` → `https://esquina-boxeo.streamlit.app`
4. Abre **Advanced settings**:
   - **Python version:** elige **3.11** (es con la que está probado todo).
   - **Secrets:** déjalo vacío por ahora. Solo si quieres el vídeo en el ejemplo, pon:
     ```toml
     DEMO_VIDEO_URL = "https://youtu.be/TU_VIDEO"
     ```
     (ver "Vídeo del ejemplo" abajo). Pulsa **Save**.
5. Pulsa **Deploy**. El primer arranque instala todo y tarda **5-10 minutos**. Puedes ver el progreso en el
   panel de la derecha ("Manage app" → logs).
6. Cuando cargue, comprueba:
   - `https://TU-APP.streamlit.app/?demo=1` → debe salir el análisis de ejemplo (sin vídeo, con un aviso).
   - Sube un clip **corto (15-20 s) en 1080p** y espera al resultado. El servidor gratuito es más lento que
     tu Mac: calcula **2-4 veces lo que tarda en local** (no lo he podido medir allí).
7. Pásame el enlace y actualizo el README.

## Vídeo del ejemplo (opcional)

El vídeo del ejemplo no está en GitHub (regla: no subir vídeos). Sin él, el ejemplo funciona igual pero
sin vídeo. Para añadirlo sin meterlo en el repo:

1. Sube `demo/annotated.mp4` (está en tu ordenador) a YouTube como **No listado**.
2. Copia el enlace y ponlo en **Settings → Secrets** de la app: `DEMO_VIDEO_URL = "https://youtu.be/..."`.
3. Guarda. La app se reinicia sola y los botones de "Momentos para revisar" también saltan al segundo exacto.

Otras opciones y sus pegas: ver `docs/DECISIONES.md`, punto 3.

## Si algo falla

| Síntoma en los logs o en la app | Causa probable | Qué hacer |
|---|---|---|
| `ImportError: libGL.so.1`, `libEGL.so.1`, `libGLESv2.so.2` o `PortAudio library not found` | No se instalaron las librerías del sistema | Comprueba que `packages.txt` está en la raíz del repo y pulsa **Reboot app** |
| Error instalando `mediapipe` | Versión de Python distinta de 3.11 | **Settings → General → Python version → 3.11** (si no deja cambiarlo, borra la app y créala otra vez eligiendo 3.11) |
| La app se reinicia sola al subir un vídeo ("Oh no.") | Se queda sin memoria | Prueba con un vídeo más corto o en 1080p en vez de 4K |
| "Falta el modelo de IA en el servidor" | Falló la descarga del modelo al arrancar | **Reboot app**; si se repite, mira los logs |
| La app pide "Wake up" | Se duerme tras un tiempo sin visitas | Ábrela un rato antes de enseñarla |

## Antes de enseñarla

- Abre el enlace 5 minutos antes para despertarla.
- Ten preparado el enlace directo al ejemplo (`?demo=1`) por si el procesado online va lento.
- Lleva un clip corto ya probado en la versión online.
