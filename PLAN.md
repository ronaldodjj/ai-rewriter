# 📚 EmojiLibro: lectura visual con emojis

> Aplicación que convierte libros EPUB y PDF en una versión más visual, sustituyendo sustantivos por emojis elegidos **según su contexto**, para facilitar la comprensión lectora sin perder el sentido original del texto.

---

## 1. Idea general

El objetivo no es llenar el libro de emojis al azar. La app identifica qué palabras son sustantivos, entiende qué significan **en esa oración** y solo las reemplaza cuando existe un emoji que las represente bien.

| Palabra   | Emoji | Comentario |
|-----------|-------|------------|
| rey       | 👑    | Concepto claro y visual |
| pueblo    | 👥    | En el sentido de "gente" |
| pueblo    | 🏘️    | En el sentido de "aldea" |
| ciudad    | 🏙️    | |
| tristeza  | 😔    | Sustantivo abstracto con emoji claro |
| banco     | 🏦 / 🪑 | Depende del contexto: entidad financiera o asiento |

**Ejemplo de transformación:**

- Original: *"El rey miró la ciudad desde la torre y sintió una profunda tristeza."*
- Convertido: *"El 👑 miró la 🏙️ desde la 🗼 y sintió una profunda 😔."*

---

## 2. Objetivos

### Objetivo general
Construir una aplicación que reciba un libro en EPUB o PDF y genere una versión enriquecida con emojis, conservando estructura, formato y significado.

### Objetivos específicos
1. Extraer el texto del libro manteniendo capítulos, párrafos y estilos.
2. Detectar sustantivos mediante análisis gramatical (NLP).
3. Resolver el significado de cada palabra según su contexto (desambiguación).
4. Asignar el emoji más adecuado, o no asignar ninguno si no hay buena opción.
5. Controlar la densidad de emojis para no saturar la lectura.
6. Exportar el resultado en EPUB, PDF y/o HTML.

### Público objetivo
- Niños en etapa de aprendizaje lector.
- Personas con dificultades de comprensión lectora o dislexia.
- Estudiantes de español como segunda lengua.
- Lectores que quieren una experiencia más visual o lúdica.

---

## 3. Reglas de conversión

Estas reglas son el corazón del proyecto: definen cuándo **sí** y cuándo **no** reemplazar.

1. **Solo sustantivos comunes.** Verbos, adjetivos y artículos se mantienen.
2. **Nombres propios no se tocan** (Juan, Madrid, Quijote), salvo configuración explícita.
3. **Umbral de confianza.** Si el sistema no está seguro del emoji (ej. confianza < 0.7), deja la palabra original.
4. **Contexto primero.** Una misma palabra puede tener emojis distintos según la oración ("banco", "pueblo", "carta", "planta").
5. **Plurales:** opción configurable:
   - `👑` (mismo emoji), o
   - `👑👑` (duplicado), o
   - `👑ˢ` / `👑×` (marcador de plural).
6. **Densidad máxima** configurable (ej. máximo 1 emoji cada 5 palabras o 30 % de sustantivos por párrafo).
7. **Expresiones fijas** no se descomponen: "tomar el pelo", "ojo de buey", "a pie de página".
8. **Diálogos y títulos** pueden tener reglas propias (ej. no convertir títulos de capítulos).

---

## 4. Modos de lectura

Para no perder el sentido original, la app ofrece varios modos:

| Modo | Resultado | Uso ideal |
|------|-----------|-----------|
| **Reemplazo** | `El 👑 miró la 🏙️` | Lectura lúdica |
| **Acompañado** | `El rey 👑 miró la ciudad 🏙️` | Aprendizaje, más claro |
| **Anotado (ruby)** | Emoji encima de la palabra, como subíndice | Niños y ELE |
| **Interactivo (HTML)** | Emoji visible, palabra original al tocar o pasar el cursor | Lectura digital |

---

## 5. Arquitectura

```
┌────────────┐   ┌──────────────┐   ┌──────────────┐   ┌───────────────┐   ┌────────────┐
│  Entrada   │──▶│  Extracción  │──▶│  Análisis    │──▶│  Asignación   │──▶│  Exportar  │
│ EPUB / PDF │   │  de texto    │   │  NLP         │   │  de emojis    │   │ EPUB/PDF/  │
└────────────┘   └──────────────┘   └──────────────┘   └───────────────┘   │ HTML       │
                                                                            └────────────┘
```

### 5.1 Extracción
- **EPUB:** `ebooklib` + `BeautifulSoup`. Se recorre cada capítulo XHTML y se procesan solo los nodos de texto, así se conserva el HTML (negritas, cursivas, notas).
- **PDF:** `PyMuPDF` (fitz) o `pdfplumber`. Se extrae texto por bloques y se reconstruyen párrafos (unir líneas cortadas, quitar guiones de corte, eliminar encabezados y números de página).
- **PDF escaneado:** OCR con `Tesseract` (fase posterior).

### 5.2 Análisis NLP
- Modelo `spaCy` en español (`es_core_news_lg` o `es_dep_news_trf`).
- Por cada token: categoría gramatical (`NOUN`, `PROPN`), lema (`reyes` → `rey`), número (singular/plural) y entidades nombradas.
- Detección de expresiones fijas con un diccionario de locuciones.

### 5.3 Desambiguación y asignación de emoji
Estrategia en capas, de lo más barato a lo más costoso:

1. **Diccionario curado** `lema → emoji` (ej. `rey: 👑`). Rápido y controlado.
2. **Diccionario por sentidos** para palabras ambiguas:
   ```json
   "banco": [
     {"emoji": "🏦", "pistas": ["dinero", "cuenta", "préstamo", "cajero"]},
     {"emoji": "🪑", "pistas": ["sentarse", "parque", "plaza", "madera"]}
   ]
   ```
3. **Similitud semántica** con embeddings (`sentence-transformers` multilingüe): se compara la oración con la descripción de cada emoji (anotaciones CLDR en español) y se elige el más cercano.
4. **LLM opcional** para casos difíciles: se envía la oración y la palabra y se pide un emoji o "ninguno". Con caché para no repetir consultas.

Cada asignación devuelve `emoji` + `confianza`. Si la confianza no supera el umbral, la palabra queda igual.

### 5.4 Exportación
- **EPUB:** se reescribe el XHTML de cada capítulo y se reempaqueta con `ebooklib`. Para el modo anotado se usa `<ruby>rey<rt>👑</rt></ruby>`.
- **PDF:** se genera desde HTML con `WeasyPrint`, usando una fuente con soporte de emojis a color (Noto Color Emoji).
- **HTML:** lector web con `<span title="rey">👑</span>` para el modo interactivo.

---

## 6. Stack tecnológico propuesto

| Capa | Tecnología |
|------|------------|
| Backend / procesamiento | Python 3.12, FastAPI |
| NLP | spaCy (`es_core_news_lg`), sentence-transformers |
| Lectura de libros | ebooklib, BeautifulSoup, PyMuPDF |
| Generación de salida | ebooklib, WeasyPrint |
| Datos de emojis | Unicode CLDR (anotaciones en español) + diccionario propio en JSON/PostgreSQL |
| Cola de trabajos | Celery + Redis (libros grandes) |
| Frontend | React / Next.js: subir libro, elegir modo, previsualizar y descargar |
| Base de datos | PostgreSQL: diccionario, caché de asignaciones, historial de conversiones |

---

## 7. Estructura de carpetas

```
emojilibro/
├── backend/
│   ├── app/
│   │   ├── api/                # Endpoints FastAPI
│   │   ├── extract/
│   │   │   ├── epub_reader.py
│   │   │   └── pdf_reader.py
│   │   ├── nlp/
│   │   │   ├── analyzer.py     # spaCy: POS, lemas, entidades
│   │   │   └── idioms.py       # Expresiones fijas
│   │   ├── mapping/
│   │   │   ├── dictionary.py   # Capa 1 y 2
│   │   │   ├── semantic.py     # Capa 3: embeddings
│   │   │   └── llm.py          # Capa 4: opcional
│   │   ├── render/
│   │   │   ├── epub_writer.py
│   │   │   ├── pdf_writer.py
│   │   │   └── html_writer.py
│   │   └── pipeline.py         # Orquesta todo el flujo
│   ├── data/
│   │   ├── emoji_dict.json
│   │   └── idioms_es.txt
│   └── tests/
├── frontend/
└── README.md
```

---

## 8. Flujo del pipeline (pseudocódigo)

```python
def convertir_libro(archivo, config):
    libro = leer(archivo)                       # EPUB o PDF → capítulos con nodos de texto
    for capitulo in libro.capitulos:
        for nodo in capitulo.nodos_texto:
            doc = nlp(nodo.texto)
            reemplazos = []
            for token in doc:
                if token.pos_ != "NOUN" or es_parte_de_locucion(token):
                    continue
                emoji, confianza = asignar_emoji(token.lemma_, oracion=token.sent.text)
                if emoji and confianza >= config.umbral:
                    reemplazos.append((token, emoji))
            reemplazos = limitar_densidad(reemplazos, config.densidad_max)
            nodo.texto = aplicar(nodo.texto, reemplazos, modo=config.modo)
    return exportar(libro, formato=config.formato_salida)
```

---

## 9. Configuración del usuario

```json
{
  "modo": "acompañado",
  "formato_salida": "epub",
  "umbral_confianza": 0.7,
  "densidad_max": 0.3,
  "plural": "duplicar",
  "convertir_abstractos": true,
  "convertir_titulos": false,
  "usar_llm": false
}
```

---

## 10. Hoja de ruta

### Fase 1: MVP (2-3 semanas)
- [ ] Lectura de EPUB y extracción de texto por capítulo.
- [ ] Detección de sustantivos con spaCy.
- [ ] Diccionario curado de ~500 sustantivos frecuentes.
- [ ] Modos "reemplazo" y "acompañado".
- [ ] Exportación a EPUB.
- [ ] Script de línea de comandos: `emojilibro convertir libro.epub --modo acompañado`.

### Fase 2: Contexto (3-4 semanas)
- [ ] Diccionario por sentidos para palabras ambiguas.
- [ ] Similitud semántica con embeddings.
- [ ] Umbral de confianza y control de densidad.
- [ ] Detección de expresiones fijas.

### Fase 3: PDF y web (3-4 semanas)
- [ ] Lectura de PDF con reconstrucción de párrafos.
- [ ] Exportación a PDF y HTML interactivo.
- [ ] API FastAPI + frontend para subir, previsualizar y descargar.
- [ ] Procesamiento asíncrono para libros grandes.

### Fase 4: Mejoras
- [ ] LLM opcional para casos difíciles.
- [ ] Editor manual: el usuario corrige un emoji y se aplica en todo el libro.
- [ ] Perfiles por edad (más o menos emojis).
- [ ] OCR para PDF escaneados.
- [ ] Soporte para inglés y otros idiomas.

---

## 11. Riesgos y retos

| Riesgo | Mitigación |
|--------|-----------|
| Palabras ambiguas mal interpretadas | Diccionario por sentidos + umbral de confianza + no reemplazar si hay duda |
| Saturación visual | Límite de densidad configurable |
| Sustantivos abstractos sin emoji claro ("justicia", "idea") | Reemplazar solo si hay emoji aceptado; si no, dejar texto |
| PDF con maquetación compleja (columnas, notas) | Empezar por EPUB; en PDF usar análisis por bloques |
| Emojis que se ven distinto según dispositivo | Incrustar fuente Noto Color Emoji en PDF y EPUB |
| Rendimiento en libros largos | Caché de asignaciones por lema + procesamiento en cola |
| Derechos de autor | La app transforma libros que el usuario ya posee; no distribuye contenido |

---

## 12. Cómo medir si funciona

- **Precisión del emoji:** muestra de 500 reemplazos revisada a mano; meta ≥ 90 % correctos.
- **Cobertura:** porcentaje de sustantivos convertidos (equilibrado con la densidad).
- **Comprensión lectora:** prueba con lectores reales, comparando preguntas de comprensión sobre texto original vs. texto con emojis.
- **Tiempo de conversión:** meta < 1 minuto para un libro de 300 páginas.

---

## 13. Próximo paso

Construir el MVP de la Fase 1 con un libro de dominio público (por ejemplo, *El Principito* en ediciones libres o cuentos clásicos) para validar el diccionario base y el modo "acompañado".
