# Roadmap

Plan de trabajo por días (de [PLAN_Y_PROMPTS.md](PLAN_Y_PROMPTS.md)). Marca cada tarea al terminarla.

## Jueves: proyecto montado + vídeos de prueba

### Paso 0. Setup
- [x] Instalar git, GitHub CLI y Python 3.11
- [x] Entorno virtual `.venv` y `requirements.txt` con el stack
- [x] Estructura de carpetas, `.gitignore` y README básico
- [x] Inicializar git y primer commit
- [x] Login en GitHub
- [x] Crear repo público `boxeo-mvp` y subir el commit

### Paso 1. Grabar vídeos de prueba (20-40 s, en `data/`)
- [ ] `bueno.mp4`: sombra con tu mejor técnica
- [ ] `guardia_baja.mp4`: bajando a propósito la mano que no golpea
- [ ] `sin_extender.mp4`: golpes cortos, sin estirar el brazo
- [ ] `libre.mp4`: sombra normal o saco, como entrenas siempre

Cómo grabar: móvil fijo en diagonal a ~45 grados, cuerpo entero, buena luz, 60 fps si se puede, solo tú en el plano.

## Viernes: versión funcional de punta a punta

### Prompt 1. Pipeline
- [ ] `scripts/download_model.py` y descarga del modelo
- [ ] `config.yaml` con los valores iniciales
- [ ] `boxeo/pose.py`
- [ ] `boxeo/metrics.py`
- [ ] `boxeo/punches.py`
- [ ] `boxeo/scoring.py`
- [ ] `boxeo/tips.py`
- [ ] `boxeo/render.py`
- [ ] `scripts/analyze.py` (genera `annotated.mp4`, `metrics.json`, `landmarks.csv`)
- [ ] Probar con los 4 vídeos de `data/` y tabla de métricas y puntuación
- [ ] Commit y push

### Prompt 2. App local
- [ ] `app.py` con Streamlit: subir vídeo, barra de progreso, vídeo anotado, ficha y 3 consejos
- [ ] Instrucciones para arrancarla en local
- [ ] Commit y push

**Hito:** subes un vídeo a la app en local y devuelve esqueleto, puntuación y consejos.

## Sábado: calibración

- [ ] Contar a mano los golpes de `bueno.mp4` (izquierda y derecha)
- [ ] Gráficas de ángulo del codo y velocidad de muñeca con los golpes detectados
- [ ] Comparar golpes detectados con el conteo manual y ajustar la detección
- [ ] Comprobar que `guardia_baja` puntúa peor en "mano contraria arriba" y "guardia"
- [ ] Comprobar que `sin_extender` puntúa peor en "extensión"
- [ ] Proponer y aplicar ajustes de umbrales en `config.yaml` (explicados antes)
- [ ] Commit y push

## Domingo: experiencia

- [ ] Ficha visual tipo tarjeta deportiva: total grande, subscores con barras, golpes por mano y por minuto
- [ ] Vídeo anotado: contador de golpes, indicador de guardia verde/rojo, destello al detectar golpe
- [ ] Consejos más naturales con el dato concreto de la sesión
- [ ] Probar con todos los clips, commit y push

## Lunes: online + caso de producto

- [ ] Preparar despliegue en Streamlit Community Cloud (requirements, packages.txt, descarga del modelo al arrancar)
- [ ] Desplegar la app desde la web de Streamlit (lo haces tú)
- [ ] README como caso de producto: problema, usuario, MoSCoW, cómo funciona, métricas, limitaciones, siguientes pasos, capturas
- [ ] Commit y push
- [ ] (Opcional) Consejos redactados con la API de Claude

## Martes: demo y envío

- [ ] Grabar demo de pantalla (1-2 min) con dos decisiones de producto explicadas
- [ ] Redactar el mensaje a un contacto con enlace a la app, al repo y a la demo
- [ ] Margen para arreglos
