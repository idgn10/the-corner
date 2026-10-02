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

### Paso 1. Grabar vídeos de prueba (en `data/`, .MOV del iPhone, casi de perfil)
- [x] Jabs: solo mano izquierda
- [x] Directos: solo mano derecha
- [x] Combinaciones 1-2 con buena técnica
- [x] Combinaciones 1-2 "vagas" (peor técnica a propósito)
- [x] Sombra libre con movimiento y curvos

Cómo grabar: móvil fijo, cuerpo entero, buena luz, 60 fps si se puede, solo tú en el plano.

## Viernes: versión funcional de punta a punta

### Prompt 1. Pipeline
- [x] `scripts/download_model.py` y descarga del modelo
- [x] `config.yaml` con los valores iniciales
- [x] `boxeo/pose.py`
- [x] `boxeo/metrics.py`
- [x] `boxeo/punches.py`
- [x] `boxeo/scoring.py`
- [x] `boxeo/tips.py`
- [x] `boxeo/render.py`
- [x] `scripts/analyze.py` (genera `annotated.mp4`, `metrics.json`, `landmarks.csv`)
- [x] Probar con los vídeos reales de `data/` y tabla de métricas y puntuación
- [x] Commit y push

### Prompt 2. App local
- [x] `app.py` con Streamlit: subir vídeo, barra de progreso, vídeo anotado, ficha y 3 consejos
- [x] Instrucciones para arrancarla en local
- [x] Commit y push
- [ ] Probarla con un vídeo real en el navegador

**Hito:** subes un vídeo a la app en local y devuelve esqueleto, puntuación y consejos.

## Sábado: calibración

- [x] Contar a mano los golpes de cada clip y compararlos con los detectados (coinciden)
- [x] Detección basada en la muñeca, codo mínimo 125° (golpe corto = golpe que baja la extensión)
- [x] Comprobar que el 1-2 "vago" puntúa peor que el bueno (guardia, mano contraria, extensión)
- [x] Comprobar golpes cortos con el boxeador sintético (extensión baja, golpes contados)
- [x] Ajustes aprobados: filtro de golpes simultáneos, tramo activo, base con peso 0, regla de guardia del codo
- [x] Commit y push
- [ ] (Opcional) Gráficas de ángulo del codo y velocidad de muñeca: no hicieron falta, se calibró con hojas de frames

## Domingo: experiencia

- [x] Ficha visual tipo tarjeta deportiva: total grande, subscores con barras, golpes por mano y por minuto
- [x] Vídeo anotado: contador de golpes, indicador de guardia verde/rojo, destello al detectar golpe
- [x] Consejos más naturales con el dato concreto de la sesión
- [x] Probar con todos los clips, commit y push

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
