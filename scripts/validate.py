"""Validacion automatica de los clips de referencia y de control (la regla de CLAUDE.md).

Uso:
  python scripts/validate.py                       analiza los clips y los compara con la referencia guardada
  python scripts/validate.py --guardar-referencia  ademas guarda el resultado de ahora como nueva referencia
                                                   (solo cuando Ignacio ha aprobado el cambio)
  python scripts/validate.py --recalcular          vuelve a calcular la pose aunque este en la cache

Regla: golpes identicos (rectos por mano, curvos y esquivas) en los 4 clips de rectos y nota +-2 en todos;
un clip que era "Sin nota" tiene que seguir sin nota. Los cambios de golpes en sombra y en los clips de control
salen como aviso, pero no deciden. Sale con 0 si cumple (SI) y con 1 si no (NO).

La referencia (scripts/validate_reference.json) solo tiene numeros: se puede subir al repo.
La pose de cada clip se guarda fuera del repo, en ~/TheCorner-datos/cache/pose (o en $THECORNER_DATOS/cache/pose).
Se vuelve a calcular si cambia el video, el modelo de pose, MediaPipe, OpenCV, los ajustes de video y pose de
config.yaml o el codigo que lee el video y saca la pose (boxeo/pose.py). El analisis es el de la app
(boxeo.pipeline.analyze), con la pose de la cache y sin generar el video de salida, que no interviene en el
analisis (docs/DECISIONES.md, punto 18).
"""
import argparse
import hashlib
import inspect
import json
import os
import sys
import tempfile
import time
import unicodedata
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

REFERENCIA = Path(__file__).resolve().parent / "validate_reference.json"
DATOS = Path(os.environ.get("THECORNER_DATOS", Path.home() / "TheCorner-datos")).expanduser()
CACHE = DATOS / "cache" / "pose"
CACHE_VERSION = 1  # subir si cambia el formato de la cache
MARGEN_NOTA = 2

# (clave, archivo en data/, grupo). "rectos": deciden por golpes y nota; "sombra" y "control": solo por nota
CLIPS = [
    ("jab", "Jabs(1).MOV", "rectos"),
    ("directo", "Directos(2).MOV", "rectos"),
    ("uno_dos", "Combinaciones 1-2.MOV", "rectos"),
    ("uno_dos_vago", '"Vago".MOV', "rectos"),
    ("sombra", "Sombra normal.MOV", "sombra"),
    ("frente_1,5m", "1,5m.MOV", "control"),
] + [(f"{mov.lower()}_{p}", f"{mov}_{a}.MOV", "control")
     for mov in ("Crochet", "Upper", "Medias", "Enteras")
     for p, a in (("frente", "frente"), ("45", "45º"), ("90", "90º"))]
CAMPOS = ("rectos_izq", "rectos_der", "crochets", "uppercuts", "esquivas", "nota")


# ---------- Clips ----------

def _nfc(s):
    return unicodedata.normalize("NFC", s)


def localizar(carpeta):
    """{clave: ruta del video} y la lista de los que faltan."""
    archivos = {_nfc(p.name): p for p in carpeta.iterdir()} if carpeta.is_dir() else {}
    encontrados = {k: archivos.get(_nfc(nombre)) for k, nombre, _ in CLIPS}
    return encontrados, [nombre for k, nombre, _ in CLIPS if encontrados[k] is None]


# ---------- Cache de la pose ----------

def _sha256(path):
    with open(path, "rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def ajustes_pose(cfg):
    """Lo que, ademas del video, cambia la pose que sale de boxeo.pose.extract_landmarks."""
    import cv2
    import mediapipe

    from boxeo import pose

    model = Path(cfg["pose"]["model"])
    model = model if model.is_absolute() else ROOT / model
    codigo = "".join(inspect.getsource(f) for f in (pose.video_info, pose.iter_frames, pose.extract_landmarks))
    return {
        "modelo": model.name,
        "modelo_sha256": _sha256(model),
        "mediapipe": mediapipe.__version__,
        "opencv": cv2.__version__,
        "max_height": cfg["video"]["max_height"],
        "max_seconds": cfg["video"]["max_seconds"],
        "min_visibility": cfg["pose"]["min_visibility"],
        "codigo_pose": hashlib.sha256((codigo + repr(pose.LANDMARKS)).encode()).hexdigest(),
        "formato": CACHE_VERSION,
    }


def clave(video, ajustes):
    partes = {"video_sha256": _sha256(video), **ajustes}
    return hashlib.sha256(json.dumps(partes, sort_keys=True).encode()).hexdigest()[:24]


def ruta_cache(key):
    return CACHE / f"{key}.npz"


def guardar_pose(path, df, info, video):
    import numpy as np

    meta = {"columnas": list(df.columns), "info": {**info, "size": list(info["size"])}, "video": Path(video).name}
    tmp = path.with_name(path.stem + ".tmp.npz")
    np.savez_compressed(tmp, datos=df.to_numpy(np.float64), meta=json.dumps(meta))
    tmp.replace(path)


def cargar_pose(path):
    """(DataFrame, info) exactamente como los devuelve boxeo.pose.extract_landmarks."""
    import numpy as np
    import pandas as pd

    with np.load(path, allow_pickle=False) as z:
        datos, meta = z["datos"], json.loads(str(z["meta"]))
    df = pd.DataFrame(datos, columns=meta["columnas"])
    df["frame"] = df["frame"].astype("int64")
    info = meta["info"]
    info["size"] = tuple(info["size"])
    return df, info


def _silenciar():
    """MediaPipe escribe avisos en la salida de errores: en los procesos que calculan la pose no se ven."""
    os.dup2(os.open(os.devnull, os.O_WRONLY), 2)


def calcular_pose(video, destino):
    """En un proceso aparte: la pose del video con boxeo.pose (como la app), guardada en la cache."""
    from boxeo.pipeline import load_config
    from boxeo.pose import extract_landmarks

    t0 = time.monotonic()
    df, info = extract_landmarks(video, load_config())
    destino = Path(destino)
    guardar_pose(destino, df, info, video)
    copia, info2 = cargar_pose(destino)
    if not (copia.equals(df) and list(copia.dtypes) == list(df.dtypes) and info2 == info):
        destino.unlink()
        raise RuntimeError(f"la pose guardada de {Path(video).name} no es idéntica a la calculada")
    return time.monotonic() - t0, info["n_frames"] / info["fps"]


# ---------- Analisis ----------

def analizar(video, df, info, cfg, out_dir):
    """boxeo.pipeline.analyze con la pose de la cache y sin video de salida. Devuelve los numeros que se comparan."""
    import boxeo.pipeline as pl
    from boxeo.moves import curved_summary

    original = pl.extract_landmarks, pl.render_video
    pl.extract_landmarks = lambda path, cfg, progress=None: (df.copy(), dict(info))
    pl.render_video = lambda *a, **k: None
    try:
        r = pl.analyze(video, out_dir, cfg)
    finally:
        pl.extract_landmarks, pl.render_video = original
    curvos = curved_summary(r["moves"], r["fps"])  # como los cuenta la app (cada curvo una vez)
    numeros = {"rectos_izq": r["metrics"]["n_left"], "rectos_der": r["metrics"]["n_right"],
               "crochets": curvos["crochet"], "uppercuts": curvos["uppercut"], "esquivas": curvos["esquiva"],
               "nota": r["total"]}
    return numeros, r["quality"]["level"]


# ---------- Comparacion y tabla ----------

def juzgar(grupo, antes, ahora):
    """(fallos que deciden, avisos que no deciden)."""
    if antes is None:
        return ["no está en la referencia"], []
    fallos, avisos = [], []
    a, b = antes["nota"], ahora["nota"]
    if (a is None) != (b is None):
        fallos.append(f"nota {_nota(a)} → {_nota(b)}")
    elif a is not None and abs(a - b) > MARGEN_NOTA:
        fallos.append(f"nota {a} → {b}, más de ±{MARGEN_NOTA}")
    golpes = [c for c in CAMPOS[:-1] if antes[c] != ahora[c]]
    if golpes:
        texto = "cambian " + ", ".join(c.replace("_", " ") for c in golpes)
        (fallos if grupo == "rectos" else avisos).append(texto)
    return fallos, avisos


def _nota(n):
    return "Sin nota" if n is None else str(n)


def _celda(antes, ahora, fmt):
    a, b = (fmt(antes) if antes else None), fmt(ahora)
    return b if a in (None, b) else f"{a} → {b}"


def tabla(filas):
    head = ("Clip", "Rectos I/D", "Crochets+Uppers", "Esquivas", "Nota", "Fiabilidad", "Pose", "Cumple")
    widths = [max(len(str(x)) for x in col) for col in zip(head, *filas)]
    line = lambda r: "  ".join(str(x).ljust(w) for x, w in zip(r, widths)).rstrip()
    return "\n".join([line(head), "  ".join("-" * w for w in widths)] + [line(r) for r in filas])


def _seg(s):
    if s >= 90:
        return f"{s / 60:.1f} min".replace(".", ",")
    return f"{s:.1f} s".replace(".", ",")


# ---------- Principal ----------

def main():
    ap = argparse.ArgumentParser(description="Validación de los clips de referencia y de control")
    ap.add_argument("--guardar-referencia", action="store_true",
                    help="guarda el resultado de ahora como referencia (solo con el visto bueno de Ignacio)")
    ap.add_argument("--recalcular", action="store_true", help="calcula la pose aunque esté en la caché")
    ap.add_argument("--videos", default=str(ROOT / "data"), help="carpeta de los clips (por defecto, data/)")
    ap.add_argument("--procesos", type=int, default=min(4, os.cpu_count() or 1),
                    help="clips cuya pose se calcula a la vez (por defecto, 4)")
    args = ap.parse_args()
    t0 = time.monotonic()

    videos, faltan = localizar(Path(args.videos).expanduser())
    if faltan:
        print(f"Faltan {len(faltan)} clips en {args.videos}: " + ", ".join(faltan))
        print("No se valida nada.")
        return 1
    ref = json.loads(REFERENCIA.read_text(encoding="utf-8")) if REFERENCIA.exists() else None
    if ref is None and not args.guardar_referencia:
        print(f"No hay referencia ({REFERENCIA.name}). Se crea con: python scripts/validate.py --guardar-referencia")
        return 1

    from boxeo.pipeline import load_config
    from boxeo.scoring import SCORING_VERSION

    cfg = load_config()
    ajustes = ajustes_pose(cfg)
    CACHE.mkdir(parents=True, exist_ok=True)
    claves = {k: clave(videos[k], ajustes) for k, _, _ in CLIPS}
    pendientes = [k for k, _, _ in CLIPS if args.recalcular or not ruta_cache(claves[k]).exists()]

    origen = {k: "caché" for k, _, _ in CLIPS}
    if pendientes:
        print(f"Calculando la pose de {len(pendientes)} clips ({args.procesos} a la vez). "
              "La primera vez tarda unos minutos…", flush=True)
        t_pose = time.monotonic()
        with ProcessPoolExecutor(args.procesos, initializer=_silenciar) as ex:
            fut = {ex.submit(calcular_pose, str(videos[k]), str(ruta_cache(claves[k]))): k for k in pendientes}
            for f in as_completed(fut):
                k = fut[f]
                secs, dur = f.result()
                origen[k] = "calculada"
                print(f"  {k}: {_seg(dur)} de vídeo, pose en {_seg(secs)} "
                      f"(van {_seg(time.monotonic() - t_pose)})", flush=True)

    print("Analizando…", flush=True)
    ahora, fiab = {}, {}
    with tempfile.TemporaryDirectory(prefix="validacion-") as tmp:
        for k, _, _ in CLIPS:
            df, info = cargar_pose(ruta_cache(claves[k]))
            ahora[k], fiab[k] = analizar(videos[k], df, info, cfg, Path(tmp) / k)

    antes = (ref or {}).get("clips", {})
    version_ref = (ref or {}).get("scoring_version")
    filas, fallan, avisos = [], [], []
    for k, _, grupo in CLIPS:
        a, b = antes.get(k), ahora[k]
        f, av = juzgar(grupo, a, b) if ref is not None else ([], [])
        if f:
            fallan.append(f"{k}: {', '.join(f)}")
        avisos += [f"{k}: {x}" for x in av]
        filas.append((k,
                      _celda(a, b, lambda n: f"{n['rectos_izq']}/{n['rectos_der']}"),
                      _celda(a, b, lambda n: f"{n['crochets']}+{n['uppercuts']}"),
                      _celda(a, b, lambda n: str(n["esquivas"])),
                      _celda(a, b, lambda n: _nota(n["nota"])),
                      fiab[k], origen[k], "—" if ref is None else "NO" if f else "SÍ"))
    if version_ref and version_ref != SCORING_VERSION:
        fallan.insert(0, f"La puntuación es {SCORING_VERSION} y la referencia es {version_ref}: las notas no son "
                         "comparables")

    print(f"\nPuntuación {SCORING_VERSION} · referencia {version_ref or '(ninguna)'} · regla: golpes idénticos en "
          f"los 4 clips de rectos y nota ±{MARGEN_NOTA}")
    print("Cada celda enseña la referencia → ahora cuando cambia (si no cambia, un solo número).\n")
    print(tabla(filas))
    if avisos:
        print("\nAvisos (no deciden):\n  " + "\n  ".join(avisos))
    calculadas = sum(o == "calculada" for o in origen.values())
    print(f"\n{len(CLIPS)} clips en {_seg(time.monotonic() - t0)} (pose de la caché: {len(CLIPS) - calculadas}, "
          f"calculada: {calculadas}).")

    if ref is not None:
        if fallan:
            print("\nRESULTADO: NO cumple la regla. " + "; ".join(fallan) + ".")
            print("No se sube: se descarta el cambio o decide Ignacio con esta tabla de antes y después.")
        else:
            print(f"\nRESULTADO: SÍ cumple la regla (golpes idénticos en los 4 clips de rectos y nota ±{MARGEN_NOTA}).")
    if args.guardar_referencia:
        nueva = {"scoring_version": SCORING_VERSION,
                 "clips": {k: {c: ahora[k][c] for c in CAMPOS} for k, _, _ in CLIPS}}
        REFERENCIA.write_text(json.dumps(nueva, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"\nReferencia guardada en scripts/{REFERENCIA.name} (puntuación {SCORING_VERSION}).")
        return 0
    return 1 if fallan else 0


if __name__ == "__main__":
    sys.exit(main())
