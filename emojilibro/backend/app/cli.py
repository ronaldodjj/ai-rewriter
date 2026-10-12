"""Línea de comandos: ``emojilibro convertir libro.epub --modo acompañado``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import PLURALES, Config, normalizar_modo
from .nlp.languages import IDIOMAS
from .pipeline import convertir_libro


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="emojilibro", description="Lectura visual con emojis.")
    sub = parser.add_subparsers(dest="comando", required=True)

    conv = sub.add_parser("convertir", help="Convierte un libro EPUB")
    conv.add_argument("archivo", type=Path, help="Libro de entrada (.epub)")
    conv.add_argument("-o", "--salida", type=Path, help="Archivo de salida (por defecto <nombre>.emoji.epub)")
    conv.add_argument("--modo", default="acompañado", type=normalizar_modo,
                      help="reemplazo | acompañado (por defecto: acompañado)")
    conv.add_argument("--idioma", choices=sorted(IDIOMAS),
                      help="Idioma del libro; por defecto se detecta de los metadatos")
    conv.add_argument("--plural", choices=PLURALES, default="mismo")
    conv.add_argument("--umbral", type=float, default=0.7, help="Confianza mínima (0-1)")
    conv.add_argument("--convertir-titulos", action="store_true", help="Convertir también los títulos")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    salida = args.salida or args.archivo.with_name(f"{args.archivo.stem}.emoji.epub")
    try:
        config = Config(
            modo=args.modo,
            idioma=args.idioma,
            umbral_confianza=args.umbral,
            plural=args.plural,
            convertir_titulos=args.convertir_titulos,
        )
        stats = convertir_libro(args.archivo, salida, config)
    except (ValueError, RuntimeError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    print(f"{stats.reemplazos} de {stats.sustantivos} sustantivos convertidos → {salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
