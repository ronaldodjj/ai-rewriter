import pytest
import spacy

from app.nlp.languages import IDIOMAS


def _modelo_instalado(codigo: str) -> bool:
    return any(spacy.util.is_package(m) for m in IDIOMAS[codigo].modelos)


def requiere_modelo(codigo: str):
    return pytest.mark.skipif(
        not _modelo_instalado(codigo), reason=f"modelo spaCy para '{codigo}' no instalado"
    )
