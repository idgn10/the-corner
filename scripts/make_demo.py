"""Prepara el ejemplo de la app (boton "Ver un ejemplo" y ?demo=1) a partir de un analisis ya hecho.

Uso: python scripts/make_demo.py outputs/sombra

Copia metrics.json (se sube a git) y annotated.mp4 (NO se sube: los videos estan en .gitignore) a demo/.
"""
import shutil
import sys
from pathlib import Path

DEMO = Path(__file__).resolve().parent.parent / "demo"


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    if not (src / "metrics.json").exists():
        sys.exit(f"No hay metrics.json en {src}. Analiza antes el video con scripts/analyze.py")
    DEMO.mkdir(exist_ok=True)
    shutil.copy(src / "metrics.json", DEMO / "metrics.json")
    if (src / "annotated.mp4").exists():
        shutil.copy(src / "annotated.mp4", DEMO / "annotated.mp4")
    print(f"Ejemplo preparado en {DEMO}/ a partir de {src}")


if __name__ == "__main__":
    main()
