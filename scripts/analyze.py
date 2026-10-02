"""Analiza un video de boxeo desde la terminal.

Uso: python scripts/analyze.py data/video.mp4 [--stance southpaw] [--out outputs/carpeta]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from boxeo.pipeline import analyze, load_config  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Análisis de boxeo con IA")
    parser.add_argument("video", help="ruta del vídeo (mp4, mov...)")
    parser.add_argument("--stance", choices=["orthodox", "southpaw"], help="guardia (por defecto, la de config.yaml)")
    parser.add_argument("--out", help="carpeta de salida (por defecto outputs/<nombre del vídeo>)")
    args = parser.parse_args()

    if not Path(args.video).exists():
        sys.exit(f"No existe el vídeo: {args.video}")

    last = [-1]

    def progress(p, msg):
        pct = int(p * 100)
        if pct // 10 != last[0] // 10:
            print(f"  {pct:3d}%  {msg}", flush=True)
            last[0] = pct

    print(f"Analizando {args.video} ...")
    r = analyze(args.video, args.out, load_config(stance=args.stance), progress)
    m = r["metrics"]
    out = Path(args.out) if args.out else Path("outputs") / Path(args.video).stem

    print(f"\nPuntuación total: {r['total'] if r['total'] is not None else '-'} / 100")
    print(f"Golpes: {m['n_punches']} (izq. {m['n_left']}, der. {m['n_right']}) en {m['duration_s']} s"
          f" | persona detectada en el {m['pose_detected_pct']}% de los frames")
    for s in r["subscores"].values():
        score = s["score"] if s["score"] is not None else "-"
        print(f"  {s['label']:<24} {str(score):>4}   ({s['metric']} = {s['value']})")
    print("\nConsejos:")
    for t in r["tips"]:
        print(f"  - {t}")
    print(f"\nResultados en {out}/ (annotated.mp4, metrics.json, landmarks.csv)")


if __name__ == "__main__":
    main()
