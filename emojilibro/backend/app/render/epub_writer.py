"""Reempaqueta un EPUB con los capítulos modificados."""

from __future__ import annotations

from itertools import count
from pathlib import Path

from ebooklib import epub

from ..extract.epub_reader import LibroEpub


def _asignar_uids(toc, contador) -> None:
    """ebooklib deja ``uid=None`` en los enlaces del índice al leer un EPUB, y
    ``write_epub`` falla al generar el NCX. Les damos un id único."""
    for entrada in toc:
        if isinstance(entrada, tuple):  # (Section, [hijos])
            _asignar_uids(entrada[1], contador)
        elif isinstance(entrada, epub.Link) and not entrada.uid:
            entrada.uid = f"navpoint-{next(contador)}"


def escribir_epub(libro: LibroEpub, ruta: str | Path) -> None:
    for capitulo in libro.capitulos:
        capitulo.item.set_content(str(capitulo.soup).encode("utf-8"))
    _asignar_uids(libro.book.toc, count(1))
    epub.write_epub(str(ruta), libro.book, {})
