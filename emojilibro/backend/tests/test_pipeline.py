import pytest
from ebooklib import epub

from app.cli import main
from app.config import Config
from app.extract.epub_reader import leer_epub
from app.pipeline import Conversor, convertir_libro
from conftest import requiere_modelo


@requiere_modelo("es")
def test_convertir_texto_es():
    c = Conversor(Config(modo="reemplazo"), "es")
    salida = c.convertir_texto("El rey miró la ciudad desde la torre y sintió una profunda tristeza.")
    assert salida == "El 👑 miró la 🏙️ desde la 🗼 y sintió una profunda 😔."


@requiere_modelo("en")
def test_convertir_texto_en_acompanado():
    c = Conversor(Config(modo="acompañado"), "en")
    salida = c.convertir_texto("The king looked at the city.")
    assert salida == "The king 👑 looked at the city 🏙️."


@requiere_modelo("es")
def test_umbral_deja_palabras_ambiguas():
    c = Conversor(Config(modo="reemplazo"), "es")
    assert "banco" in c.convertir_texto("Se sentó en el banco del parque.")


def _crear_epub(ruta, idioma, cuerpo, titulo):
    book = epub.EpubBook()
    book.set_identifier("test")
    book.set_title("Test")
    book.set_language(idioma)
    cap = epub.EpubHtml(title="Cap 1", file_name="cap1.xhtml", lang=idioma)
    cap.content = f"<html><body><h1>{titulo}</h1>{cuerpo}</body></html>"
    book.add_item(cap)
    book.toc = (cap,)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", cap]
    epub.write_epub(str(ruta), book)


def _cuerpo(ruta):
    libro = leer_epub(ruta)
    return str(libro.capitulos[0].soup)


@requiere_modelo("es")
def test_epub_es_conserva_html(tmp_path):
    entrada, salida = tmp_path / "libro.epub", tmp_path / "salida.epub"
    _crear_epub(entrada, "es", "<p>El <b>rey</b> miró la <i>ciudad</i> desde la torre.</p>", "El rey")
    stats = convertir_libro(entrada, salida, Config(modo="acompañado"))
    html = _cuerpo(salida)
    assert "<b>rey 👑</b>" in html
    assert "<i>ciudad 🏙️</i>" in html
    assert "torre 🗼" in html
    assert "<h1>El rey</h1>" in html  # los títulos no se convierten por defecto
    assert stats.reemplazos == 3
    assert leer_epub(salida).idioma == "es"


@requiere_modelo("en")
def test_epub_en_detecta_idioma_y_titulos(tmp_path):
    entrada, salida = tmp_path / "book.epub", tmp_path / "out.epub"
    _crear_epub(entrada, "en-US", "<p>The dog sleeps under the tree.</p>", "The King")
    convertir_libro(entrada, salida, Config(modo="reemplazo", convertir_titulos=True))
    html = _cuerpo(salida)
    assert "The 🐕 sleeps under the 🌳." in html
    assert "The 👑" in html


@requiere_modelo("es")
def test_cli(tmp_path, capsys):
    entrada = tmp_path / "libro.epub"
    _crear_epub(entrada, "es", "<p>El gato duerme.</p>", "Uno")
    assert main(["convertir", str(entrada), "--modo", "reemplazo"]) == 0
    assert (tmp_path / "libro.emoji.epub").exists()
    assert "El 🐈 duerme." in _cuerpo(tmp_path / "libro.emoji.epub")


def test_cli_rechaza_no_epub(tmp_path, capsys):
    f = tmp_path / "libro.pdf"
    f.write_bytes(b"%PDF")
    assert main(["convertir", str(f), "--idioma", "es"]) == 1
    assert "epub" in capsys.readouterr().err
