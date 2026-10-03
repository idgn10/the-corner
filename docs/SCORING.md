# Cómo puntúa la app

Explicación en lenguaje sencillo de cómo se calcula la nota, **tal y como está ahora en
[`config.yaml`](../config.yaml)**. Si cambias un valor de ese archivo, cambia lo que se explica aquí.

---

## 0. Antes de empezar: cómo "ve" la app

- La app detecta en cada fotograma del vídeo **33 puntos del cuerpo** (nariz, hombros, codos, muñecas,
  caderas, rodillas, tobillos…). Es lo que se dibuja como esqueleto.
- Si un punto se ve poco (visibilidad menor de **0,5** sobre 1), se descarta. Si un punto desaparece
  menos de **0,2 s**, se rellena uniendo el antes y el después.
- Para quitar temblores, cada punto se suaviza con la **mediana de 0,1 s** de vídeo.
- **Todas las distancias se miden en "anchuras de hombro"** (la distancia de un hombro al otro), no en
  píxeles. Así da igual si estás cerca o lejos de la cámara. La anchura de hombro se toma como la
  mediana de los últimos ~2 segundos, para que no cambie cada vez que giras el tronco al golpear.
- Los ángulos se miden en la imagen (2D). **180° es el brazo totalmente recto.**

---

## 1. Cómo se detecta un golpe

Un golpe se detecta **sobre todo por la muñeca**: es el momento en que la muñeca está más lejos del
hombro, después de haberse alejado deprisa. Para que cuente, tienen que cumplirse **todas** estas condiciones:

| # | Condición | Valor actual | En `config.yaml` |
|---|---|---|---|
| 1 | **Pico:** la muñeca está más lejos del hombro que en el ±0,125 s de alrededor | la mitad de 0,25 s | `punches.debounce_seconds` |
| 2 | **Arranque:** se busca hacia atrás el punto en que la mano estaba más recogida, como mucho **0,4 s** antes del pico | 0,4 s | `punches.max_rise_seconds` |
| 3 | **Alcance:** del arranque al pico, la muñeca se aleja del hombro al menos **0,3 anchuras de hombro** | 0,3 | `punches.min_reach_increase` |
| 4 | **Velocidad:** en ese trayecto, la muñeca alcanza al menos **3 anchuras de hombro por segundo** | 3,0 | `punches.min_peak_speed` |
| 5 | **Codo:** en el pico, el codo llega a **125° o más** (si no, es un amago o el brazo apenas se mueve) | 125° | `punches.angle_min` |
| 6 | **Altura:** en el pico, la muñeca no está más de **0,5 anchuras de hombro por debajo de los hombros** (así bajar el brazo no cuenta como golpe) | 0,5 | `punches.max_wrist_below_shoulder` |
| 7 | **Sin repetir:** no se cuentan dos golpes de la **misma mano** separados por menos de **0,25 s** | 0,25 s | `punches.debounce_seconds` |
| 8 | **Sin duplicar:** si las **dos manos** "golpean" a menos de **0,15 s** (pasa al girar el tronco), solo cuenta la que más se alejó | 0,15 s | `punches.min_gap_between_hands` |

Cada golpe se etiqueta con su mano. Con guardia **diestra** (`stance: orthodox`) la izquierda es el
**jab** y la derecha el **directo**; con guardia zurda (`southpaw`), al revés.

> Ojo: un golpe corto (codo entre 125° y 160°) **sí cuenta como golpe**, pero luego baja la nota de
> extensión. Los ganchos con el brazo bastante abierto también pasan estos filtros y se cuentan como rectos.

### Cuándo una mano está "arriba" (en guardia)

Se usa en tres métricas. Una mano está arriba si se cumplen las dos cosas:

- La muñeca está a menos de **0,8 anchuras de hombro de la nariz** (`guard.max_dist_nose`).
- La muñeca está **por encima del codo** (`guard.rule: elbow`).

### El "tramo activo"

La guardia y el ritmo se miden solo en la parte del vídeo en la que estás boxeando: desde **1 s antes
del primer golpe** hasta **1 s después de que termine el último** (`active_margin_seconds`). Así no cuenta
entrar en plano, prepararte ni ir a parar la grabación.

---

## 2. Las métricas

Cada métrica produce un valor (un %, unos segundos…) que se convierte en una **nota de 0 a 100** con una
regla de tres entre un valor **"malo"** (0 puntos) y uno **"bueno"** (100 puntos). Por debajo del malo es 0;
por encima del bueno es 100; entre medias, proporcional.

| Métrica | Qué mide | Malo (0) | Bueno (100) | Peso | Peso real en la nota |
|---|---|---|---|---|---|
| Guardia | % del tiempo con las dos manos arriba | 40% | 90% | 25 | 28% |
| Mano contraria arriba | % de golpes con la otra mano arriba | 40% | 90% | 20 | 22% |
| Extensión | % de golpes con el codo a 160° o más | 30% | 80% | 20 | 22% |
| Vuelta a la guardia | segundos medios en volver a la guardia | 0,8 s | 0,4 s | 15 | 17% |
| Volumen y ritmo | golpes por minuto | 20 | 70 | 10 | 11% |
| Base | % del tiempo con buena base | 30% | 80% | **0** | **0%** (no cuenta) |

Los pesos suman 90 (la base está a 0), así que el "peso real" es cada peso dividido entre 90.

### Guardia (peso 25)

- **Qué mide:** si mantienes las dos manos protegiendo la cara cuando no estás golpeando.
- **Cómo:** se cogen los fotogramas del tramo activo que **no** están dentro de un golpe (un golpe va
  desde su arranque hasta que la mano vuelve a la guardia). En cada uno se mira si **las dos manos
  están arriba**. El valor es el % de esos fotogramas en los que sí.
- **Escala:** 40% o menos = 0 puntos · 90% o más = 100.

### Mano contraria arriba (peso 20)

- **Qué mide:** si, mientras golpeas con una mano, la otra se queda protegiendo la cara.
- **Cómo:** en cada golpe se mira la otra mano desde el arranque hasta el pico. Si está arriba en al
  menos la mitad de esos fotogramas, ese golpe "cumple". El valor es el % de golpes que cumplen.
- **Escala:** 40% o menos = 0 · 90% o más = 100.

### Extensión (peso 20)

- **Qué mide:** si terminas los golpes con el brazo estirado.
- **Cómo:** en cada golpe se toma el ángulo máximo del codo entre el arranque y el pico. El golpe está
  **bien extendido si llega a 160° o más** (`extension.good_angle`). El valor es el % de golpes bien extendidos.
- **Escala:** 30% o menos = 0 · 80% o más = 100.

### Vuelta a la guardia (peso 15)

- **Qué mide:** lo rápido que recoges la mano después de golpear.
- **Cómo:** desde el pico del golpe se cuenta el tiempo hasta que esa mano vuelve a estar arriba **y con el
  brazo recogido** (codo a menos de **90°**, `recovery.max_elbow_angle`). Hace falta lo segundo porque, grabando
  de perfil, el puño estirado queda delante de la cara y por sí solo ya contaría como "arriba". Si la mano no
  vuelve antes del siguiente golpe, o en **1,5 s** (`recovery.max_seconds`), se apunta 1,5 s. El valor es la
  media de todos los golpes.
- **Escala:** aquí **menos es mejor**: 0,8 s o más = 0 · 0,4 s o menos = 100.

### Volumen y ritmo (peso 10)

- **Qué mide:** cuántos golpes lanzas.
- **Cómo:** número de golpes ÷ duración del tramo activo, pasado a golpes por minuto.
- **Escala:** 20 golpes/min o menos = 0 · 70 o más = 100.

### Base (peso 0: no cuenta)

- **Qué mediría:** pies separados entre 1,0 y 1,6 anchuras de hombro y rodillas algo flexionadas
  (ángulo cadera-rodilla-tobillo medio por debajo de 170°).
- **Por qué no cuenta:** grabando de perfil un pie tapa al otro en la imagen y la separación sale falsa.
  Se calcula, pero no aparece en la app, no suma a la nota y no genera consejos.

---

## 3. La nota total

1. Cada métrica da su nota de 0 a 100 (redondeada).
2. Se multiplica cada nota por su peso, se suman y se divide entre la suma de los pesos (90):

   **Total = (Guardia × 25 + Mano contraria × 20 + Extensión × 20 + Vuelta × 15 + Volumen × 10) ÷ 90**

3. Se redondea al entero más cercano.

Casos especiales:
- Si una métrica no tiene datos (por ejemplo, no hay golpes con los que medir la extensión), no cuenta
  y se divide solo entre los pesos de las que sí tienen.
- **Si se detectan menos de 5 golpes (o ninguno), no hay nota total.** Con tan pocos golpes los porcentajes no
  dicen nada ("el 100% de tus jabs" con un solo jab). Cuenta como fiabilidad baja (ver abajo).
- **Si la fiabilidad del análisis es baja, tampoco hay nota total** (mejor ningún dato que uno falso). La ficha
  dice "Sin nota: el vídeo no permite un análisis fiable", con el motivo medido (p. ej. "La mano sale del
  encuadre el 11% del tiempo") y cómo grabar mejor. En vez de los consejos de técnica salen 3 claves para
  grabar: casi de perfil o en diagonal, cuerpo entero en el plano y a 2-3 m de la cámara. El vídeo y el detalle
  por métrica se ven igual, marcados como **"Orientativo"**; la gráfica de la sesión y los momentos para
  revisar no se muestran. Con fiabilidad alta o media todo funciona como siempre.

### Cuándo la fiabilidad es baja

Basta con que una de estas cosas esté en "baja". Las tres últimas se miden en el tramo activo, ampliado a un
mínimo de **10 s** (o al vídeo entero si dura menos): con uno o dos golpes, el tramo activo son 2-3 s y no
dice cómo es el resto del vídeo.

| Qué se mide | Baja si… |
|---|---|
| Golpes detectados | menos de **5** |
| Nariz, hombros, codos y muñecas visibles a la vez | menos del **50%** del tiempo |
| Mano fuera del encuadre (muñeca a menos de 0,3 anchuras de hombro del borde) | más del **10%** del tiempo |
| Orientación: anchura de hombros ÷ altura del tronco | más de **0,70** (de frente) |

(Media: entre 50% y 75% visible, entre 3% y 10% de mano fuera, o entre 0,60 y 0,70 de orientación.)

Ojo con la orientación: el primer clip real de frente dio **0,62** (se suponía 0,75-0,8), así que de frente
suele salir "media" por orientación. Lo que deja ese vídeo sin nota es que casi no se detectan golpes.
Detalle en `docs/DECISIONES.md`, punto 13.

### Los 3 consejos

Se eligen las 3 métricas que **más puntos restan a la nota**: `(100 − nota de la métrica) × peso`.
Así, un 55 en volumen (peso 10, resta 450) pesa menos que un 62 en guardia (peso 25, resta 950).
Si una métrica tiene **85 o más**, su consejo es de refuerzo ("Muy buena guardia…"); por debajo, de
corrección y siempre con tu dato. Si hay empate, va primero la de más peso.

---

## 4. Ejemplo paso a paso: `uno_dos_vago`

Combinaciones jab-directo hechas "vagas" a propósito. Vídeo de 37,1 s, guardia diestra.

**Golpes:** se detectan **28**: 15 con la izquierda (jabs) y 13 con la derecha (directos).
El tramo activo dura **35,5 s** (se quitan 1,6 s del principio y del final, en los que no boxeas).

| Métrica | Dato del vídeo | Cuenta | Nota |
|---|---|---|---|
| Guardia | dos manos arriba el **71,1%** del tiempo entre golpes | (71,1 − 40) ÷ (90 − 40) × 100 = 62,2 | **62** |
| Mano contraria | 21 de 28 golpes con la otra mano arriba = **75%** (bajas la otra mano en 2 jabs y en 5 directos) | (75 − 40) ÷ (90 − 40) × 100 = 70 | **70** |
| Extensión | 18 de 28 golpes llegan a 160° = **64,3%** (10 se quedan cortos; codo medio 163°) | (64,3 − 30) ÷ (80 − 30) × 100 = 68,6 | **69** |
| Vuelta a la guardia | **0,37 s** de media | (0,37 − 0,8) ÷ (0,4 − 0,8) × 100 = 107,5 → máximo 100 | **100** |
| Volumen | 28 golpes ÷ 35,5 s × 60 = **47,3** golpes/min | (47,3 − 20) ÷ (70 − 20) × 100 = 54,6 | **55** |
| Base | — | peso 0, no cuenta | — |

**Nota total:**

| Métrica | Nota × peso |
|---|---|
| Guardia | 62 × 25 = 1.550 |
| Mano contraria | 70 × 20 = 1.400 |
| Extensión | 69 × 20 = 1.380 |
| Vuelta a la guardia | 100 × 15 = 1.500 |
| Volumen | 55 × 10 = 550 |
| **Suma** | **6.380** |

6.380 ÷ 90 = 70,9 → **71 / 100** ("Buen nivel").

**Consejos** (lo que resta cada métrica = (100 − nota) × peso):

| Métrica | Resta | ¿Consejo? |
|---|---|---|
| Guardia | 38 × 25 = **950** | 1.º |
| Extensión | 31 × 20 = **620** | 2.º |
| Mano contraria | 30 × 20 = **600** | 3.º |
| Volumen | 45 × 10 = 450 | no |
| Vuelta a la guardia | 0 × 15 = 0 | no |

1. *"Entre golpes tienes las dos manos arriba solo el 71% del tiempo. Después de cada golpe, vuelve a
   llevar los puños a la barbilla antes de moverte."*
2. *"El 36% de tus golpes se quedan cortos (codo por debajo de 160°): termina cada golpe con el brazo
   estirado, como si quisieras atravesar el objetivo."*
3. *"Bajas la mano izquierda en el 38% de tus directos: mantenla pegada a la barbilla mientras golpeas con la otra."*

(El 38% es 5 de 13 directos. Se habla de los directos porque es donde más bajas la otra mano: en los jabs solo es el 13%.)

---

## 5. Qué puedes cambiar en `config.yaml`

**Importante:**
- Los cambios se aplican a los **análisis nuevos**. Los resultados ya guardados (`outputs/` y el ejemplo
  de `demo/`) no cambian hasta que vuelvas a analizar el vídeo (`python scripts/analyze.py ...`, y
  `python scripts/make_demo.py outputs/<clip>` para el ejemplo).
- Los valores actuales están **calibrados con tus 5 vídeos**. Si cambias algo, vuelve a analizarlos y
  comprueba que los conteos de golpes siguen cuadrando y que el 1-2 vago sigue puntuando claramente peor que el bueno.

### Puntuación (lo más seguro de tocar: no cambia qué se detecta, solo cómo se valora)

| Valor | Ahora | Si lo subes | Si lo bajas |
|---|---|---|---|
| `scoring.<métrica>.weight` | 25 / 20 / 20 / 15 / 0 / 10 | esa métrica pesa más en la nota y aparece antes en los consejos | pesa menos; con **0** desaparece de la app, de la nota y de los consejos |
| `scoring.<métrica>.bad` | ver tabla del punto 2 | más exigente: hace falta más para no sacar 0 | más permisivo |
| `scoring.<métrica>.good` | ver tabla del punto 2 | más exigente: cuesta más llegar a 100 | más fácil sacar 100 |

En **vuelta a la guardia** es al revés (menos es mejor): bajar `good` (0,4 s) la hace más exigente.

### Qué cuenta como "buena técnica"

| Valor | Ahora | Si lo subes | Si lo bajas |
|---|---|---|---|
| `guard.max_dist_nose` | 0,8 | más permisivo: manos más lejos de la cara cuentan como "arriba" (sube guardia, mano contraria y vuelta) | más estricto. Con 0,7 o menos ya castigaba al 1-2 bueno |
| `guard.rule` | `elbow` | `shoulders` usa la línea de hombros en vez del codo; castiga agacharse o meter la barbilla con las manos en la cara | — |
| `guard.max_below_shoulder` | 0,15 | solo con `rule: shoulders`: más margen por debajo de los hombros | — |
| `extension.good_angle` | 160° | más exigente: menos golpes cuentan como bien extendidos | más permisivo |
| `recovery.max_seconds` | 1,5 s | un golpe sin recoger "cuesta" más en la media | castiga menos los golpes que no vuelven a la guardia |
| `active_margin_seconds` | 1,0 s | entra más tiempo de antes y después de boxear en guardia y ritmo | se ajusta más a los golpes |
| `base.*` y `scoring.base.weight` | 1,0-1,6 · 170° · peso 0 | solo tiene sentido activarla grabando en diagonal o de frente | — |

### Qué cuenta como golpe (lo más delicado: cambia el conteo)

| Valor | Ahora | Si lo subes | Si lo bajas |
|---|---|---|---|
| `punches.angle_min` | 125° | deja de contar golpes cortos y algunos ganchos (con 140° el 1-2 vago perdía 2 golpes cortos que deberían penalizar) | cuenta movimientos con el brazo más doblado (más riesgo de contar amagos) |
| `punches.min_reach_increase` | 0,3 | solo cuentan golpes que se alejan más | cuentan movimientos más pequeños |
| `punches.min_peak_speed` | 3,0 | solo cuentan golpes rápidos (podría perder golpes lentos o "vagos") | cuentan movimientos más lentos (riesgo de contar recolocar la guardia) |
| `punches.max_rise_seconds` | 0,4 s | admite golpes que tardan más en salir | solo golpes muy explosivos |
| `punches.max_wrist_below_shoulder` | 0,5 | admite golpes más bajos (y más riesgo de contar bajar el brazo) | solo golpes a la altura de la cabeza |
| `punches.debounce_seconds` | 0,25 s | dos golpes seguidos de la misma mano (doble jab rápido) pueden contar como uno | más riesgo de contar un golpe dos veces |
| `punches.min_gap_between_hands` | 0,15 s | más agresivo eliminando "golpes" de la otra mano (podría comerse un 1-2 muy rápido) | más riesgo de contar el giro del tronco como golpe |

### Vídeo y detección del esqueleto

| Valor | Ahora | Qué hace |
|---|---|---|
| `stance` | `orthodox` | guardia por defecto (en la app se elige en pantalla) |
| `video.max_height` | 720 | resolución a la que se analiza; más alto = más lento, no necesariamente mejor |
| `video.max_seconds` | 60 | duración máxima analizada |
| `pose.min_visibility` | 0,5 | más alto descarta más puntos dudosos (más huecos); más bajo acepta puntos poco fiables |
| `pose.smooth_seconds` | 0,1 s | más alto = esqueleto más estable pero picos de golpe más "aplastados" |
| `pose.max_gap_seconds` | 0,2 s | huecos más largos que esto no se rellenan |

### Fiabilidad del análisis (no cambia cómo se puntúa, pero con fiabilidad baja no hay nota total)

Sección `quality`: decide cuándo la fiabilidad es alta, media o baja. Subir los mínimos de visibilidad o bajar
los máximos de "mano fuera" y de orientación hace el control más estricto (más vídeos se quedan **sin nota**);
al revés, más permisivo. Ojo: `min_visible_medium`, `max_wrist_out_medium` y `max_front_medium` son ahora la
frontera entre tener nota y no tenerla.
`edge_margin` (0,3 anchuras de hombro) es lo cerca del borde que tiene que estar la muñeca para contar como
"mano fuera del encuadre". `min_punches` (5) es el mínimo de golpes para dar nota y `min_seconds` (10 s) el
mínimo de vídeo en el que se mide la fiabilidad. Detalle y motivos en `docs/DECISIONES.md`, puntos 7 y 13.

### Lo que no está en `config.yaml` (está en el código)

- A partir de qué nota el consejo es de refuerzo: **85** (`GOOD_SCORE` en `boxeo/tips.py`).
- Los "Momentos para revisar": tramos con la guardia baja de **al menos 0,4 s**, uniendo cortes de menos
  de 0,25 s; se enseñan los **3 más largos** (`guard_timeline` en `boxeo/metrics.py`).
- Los colores de la ficha (verde ≥ 80, ámbar ≥ 60, rojo < 60) y los veredictos ("Técnica sólida" ≥ 85,
  "Buen nivel" ≥ 70, "En progreso" ≥ 50, "A trabajar" < 50), en `boxeo/card.py`.
