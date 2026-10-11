"""Detecta rasgos de redacción típicos de IA en textos en español (post, README, informe).
Uso: python lint_texto.py archivo.md   |   python lint_texto.py - < texto.txt
Es una ayuda: un rasgo aislado no prueba nada; la acumulación sí. La revisión final es humana."""

import re
import sys

REGLAS = [
    # (categoría, patrón, explicación breve)
    ("Guion largo", r"[—–]|\s--\s", "Usar coma, punto, dos puntos o paréntesis"),
    (
        "Contraste fabricado",
        (
            r"\bno (?:es|son|se trata de|solo|sólo|solamente|únicamente)\b[^.\n]{0,80}?"
            r"(?:\bsino\b|,\s*(?:es|son)\b|\.\s*(?:Es|Son|Se trata)\b)"
        ),
        "Afirmar el punto directamente",
    ),
    (
        "Arranque escenificado",
        (
            r"(?i)\b(?:aquí está la cosa|la verdad es que|seamos honestos|"
            r"hablemos de|profundicemos|exploremos|sumérgete|te cuento|te comparto|"
            r"esto es lo que (?:nadie|necesitas)|lo que nadie te dice|"
            r"spoiler|desliza|hilo:|sin más preámbulos|vamos a desglosar)|¿sabías que"
        ),
        "Empezar por el hecho",
    ),
    (
        "Frase que suena profunda",
        (
            r"(?i)\b(?:en el fondo|la verdadera pregunta|lo que realmente importa|"
            r"en esencia|el corazón del asunto|en el dinámico mundo|en el panorama actual|"
            r"en la era de|más que nunca|en un mundo donde)"
        ),
        "Decir la afirmación concreta",
    ),
    (
        "Vocabulario inflado",
        (
            r"(?i)\b(?:crucial(?:es)?|fundamental(?:es)?|clave\b(?! de )|potenciar|"
            r"robust[oa]s?|sinergias?|transformador(?:a|es)?|revolucionari[oa]s?|"
            r"disruptiv[oa]s?|desbloquear|apasionante|panorama|ecosistema|"
            r"game changer|next level|impulsar(?:á|on)?|optimizar al máximo|"
            r"cabe destacar|es importante (?:destacar|señalar|mencionar)|vale la pena|"
            r"sin lugar a dudas|sin duda alguna|en definitiva|dicho esto|"
            r"en este sentido|a continuación|juega un papel)"
        ),
        "Palabra común en texto generado; usar la precisa o eliminar",
    ),
    (
        "Cierre de remate",
        (
            r"(?im)^\s*(?:léelo de nuevo|eso lo cambia todo|y eso es todo|así de simple|"
            r"piénsalo|ahí está la clave|esa es la diferencia|el resto es historia)\.?\s*$"
        ),
        "Eliminar el remate o reemplazarlo por un hecho",
    ),
    (
        "Pregunta genérica de cierre",
        (
            r"(?i)¿(?:y tú|qué opinas|tú qué piensas|cuál es tu experiencia|"
            r"estás de acuerdo)[^?]*\?"
        ),
        "Si hay pregunta final, que sea específica del dato",
    ),
    (
        "Negrita decorativa",
        r"\*\*[^*\n]+\*\*|[\U0001D400-\U0001D7FF]",
        "Quitar la negrita",
    ),
    (
        "Emoji o flecha",
        r"[\U0001F300-\U0001FAFF☀-➿←-⇿⬀-⯿]",
        "La marca no usa emojis ni flechas decorativas",
    ),
    ("Exclamación", r"¡[^!\n]*!", "Tono de venta; reescribir como afirmación"),
    (
        "Atribución vaga",
        (
            r"(?i)\b(?:los expertos|los especialistas|diversos estudios|"
            r"según estudios|muchos coinciden|se dice que)\b"
        ),
        "Nombrar la fuente concreta o eliminar",
    ),
    # Sección G: ortografía RAE y citas APA 7 (guía 13 del Contexto)
    ("Abreviatura con signo de grado", r"\b[Nn]\.?\s?°", "Escribir N.º (indicador ordinal)"),
    ("Porcentaje sin espacio", r"\d%", "Escribir 12.5 % (con espacio)"),
    (
        "Millares con coma o punto",
        r"\b\d{1,3}(?:,\d{3})+\b|\b\d{1,3}(?:\.\d{3}){2,}\b",
        "Separar millares con espacio; el punto es solo decimal",
    ),
    ("Coma decimal", r"\b\d+,\d{1,2}\s?%", "Usar punto decimal (decisión del portafolio)"),
    (
        "Tilde que la RAE ya no usa",
        r"\b(?:sólo|éste|ésta|éstos|éstas|ése|ésa|ésos|ésas|aquél|aquélla)\b",
        "Escribir sin tilde",
    ),
    ("Cita en formato anterior", r"\bFuente:\s", "Usar APA 7: (SBS, 2026) y «Nota.» bajo figuras"),
    (
        "Referencia en APA 6",
        r"(?i)\brecuperado de\s+https?://|\bretrieved from\b",
        "APA 7: URL directa o «Recuperado el <fecha>, de URL»",
    ),
]

CITA = r"\([^()\n]*\b(?:19|20)\d{2}[a-z]?\)|\bs\. f\.|\bNota\.|Elaboración propia"


def tríadas(linea):
    """Cuenta enumeraciones de tres elementos del tipo 'a, b y c'."""
    return len(re.findall(r"\b\w+(?: \w+)?, \w+(?: \w+)? y \w+", linea))


def main(ruta):
    if ruta == "-":
        texto = sys.stdin.read()
    else:
        with open(ruta, encoding="utf-8") as archivo:
            texto = archivo.read()
    hallazgos = []
    for n, linea in enumerate(texto.splitlines(), 1):
        if linea.strip().startswith(("```", "    ", "http")):
            continue
        for cat, patron, ayuda in REGLAS:
            for m in re.finditer(patron, linea):
                hallazgos.append((n, cat, m.group(0).strip()[:60], ayuda))
        if tríadas(linea) >= 2:
            hallazgos.append((n, "Tríadas en serie", linea.strip()[:60], "Variar la estructura"))
    if re.search(r"\d+(?:[.,]\d+)?\s?%|\bS/\s?\d", texto) and not re.search(CITA, texto):
        hallazgos.append((0, "Cifra sin cita", "—", "Agregar la cita APA 7 (regla 3.3)"))
    if re.search(CITA, texto) and not re.search(
        r"(?m)^#*\s*Referencias\b|Referencias completas", texto
    ):
        hallazgos.append((0, "Sin referencias", "—", "Agregar la sección «Referencias» (APA 7)"))
    for n, cat, frag, ayuda in hallazgos:
        print(f"L{n:>3} · {cat}: «{frag}» → {ayuda}")
    por_cat = {}
    for _, cat, _, _ in hallazgos:
        por_cat[cat] = por_cat.get(cat, 0) + 1
    print(f"\nTotal: {len(hallazgos)} rasgos en {len(por_cat)} categorías", por_cat)
    return 1 if hallazgos else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "-"))
