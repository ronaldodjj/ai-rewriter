"""Lectura de EPUB conservando el HTML.

Solo se modifican nodos de texto. Para que spaCy vea la oración completa
(y no fragmentos como "El ", "rey", " miró" cuando hay un ``<b>``), los nodos
se agrupan por su elemento de bloque más cercano (``<p>``, ``<li>``…).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import ebooklib
from bs4 import BeautifulSoup, NavigableString
from bs4.element import Comment, Declaration, Doctype, ProcessingInstruction
from ebooklib import epub

from ..nlp.languages import normalizar_codigo

ETIQUETAS_BLOQUE = {
    "p", "div", "li", "dd", "dt", "td", "th", "blockquote", "figcaption",
    "caption", "section", "article", "aside", "header", "footer", "body",
    "h1", "h2", "h3", "h4", "h5", "h6",
}
ETIQUETAS_TITULO = {"h1", "h2", "h3", "h4", "h5", "h6"}
ETIQUETAS_IGNORADAS = {"head", "title", "script", "style", "code", "pre", "ruby", "rt", "math", "svg"}
TIPOS_NO_TEXTO = (Comment, Declaration, Doctype, ProcessingInstruction)


def _nombre(tag) -> str:
    # Con el parser XML los nombres pueden llevar prefijo ("html:p").
    return tag.name.split(":")[-1].lower()


@dataclass
class Capitulo:
    item: epub.EpubItem
    soup: BeautifulSoup


@dataclass
class LibroEpub:
    book: epub.EpubBook
    idioma: str | None  # código normalizado desde dc:language, si se reconoce
    capitulos: list[Capitulo] = field(default_factory=list)


def leer_epub(ruta: str | Path) -> LibroEpub:
    book = epub.read_epub(str(ruta), {"ignore_ncx": True})
    idioma = None
    for valor, _ in book.get_metadata("DC", "language"):
        idioma = normalizar_codigo(valor)
        if idioma:
            break

    capitulos = []
    for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        if isinstance(item, epub.EpubNav):
            continue  # índice de navegación: no se convierte
        soup = BeautifulSoup(item.get_content(), "lxml-xml")
        capitulos.append(Capitulo(item=item, soup=soup))
    return LibroEpub(book=book, idioma=idioma, capitulos=capitulos)


def bloques_de_texto(soup: BeautifulSoup, convertir_titulos: bool = False) -> list[list[NavigableString]]:
    """Nodos de texto convertibles, agrupados por elemento de bloque, en orden de documento."""
    grupos: dict[int, list[NavigableString]] = {}
    for nodo in soup.find_all(string=True):
        if isinstance(nodo, TIPOS_NO_TEXTO) or not nodo.strip():
            continue
        bloque = None
        ignorar = False
        for padre in nodo.parents:
            if padre.name is None or padre is soup:
                break
            nombre = _nombre(padre)
            if nombre in ETIQUETAS_IGNORADAS or (nombre in ETIQUETAS_TITULO and not convertir_titulos):
                ignorar = True
                break
            if bloque is None and nombre in ETIQUETAS_BLOQUE:
                bloque = padre
        if ignorar or bloque is None:
            continue
        grupos.setdefault(id(bloque), []).append(nodo)
    return list(grupos.values())
