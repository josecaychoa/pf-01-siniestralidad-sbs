"""Verifica un PDF para LinkedIn antes de publicarlo (skill linkedin-pieza-editorial).
Uso: python verificar_pdf.py documento.pdf
Requiere: pypdf (uv add --dev pypdf o pip install pypdf)."""

import os
import re
import sys
from pathlib import Path

from pypdf import PdfReader

# Regla pública: piezas del portafolio usan "Portafolio · PF-XX", nunca esta etiqueta.
PROHIBIDOS_BASE = [r"Confidencial\s*·\s*Cliente"]

# Términos sensibles (empleadores, clientes, teléfono): SOLO en un archivo privado del equipo,
# fuera de todo repositorio. Un patrón regex por línea; "#" inicia un comentario.
ARCHIVO_PRIVADO = Path(
    os.environ.get("JC_TERMINOS_PROHIBIDOS", Path.home() / ".jc_terminos_prohibidos.txt")
)


def cargar_prohibidos():
    """Une la regla pública con los patrones del archivo privado, si existe."""
    patrones = list(PROHIBIDOS_BASE)
    if ARCHIVO_PRIVADO.exists():
        for linea in ARCHIVO_PRIVADO.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if linea and not linea.startswith("#"):
                patrones.append(linea)
    return patrones


def fuentes_sin_incrustar(reader):
    """Devuelve los nombres de fuentes que no traen el archivo incrustado."""
    faltan = set()
    for page in reader.pages:
        fonts = (page.get("/Resources") or {}).get("/Font") or {}
        for ref in fonts.values():
            f = ref.get_object()
            if f.get("/Subtype") == "/Type3":
                continue
            desc = f.get("/FontDescriptor")
            if desc is None and "/DescendantFonts" in f:
                desc = f["/DescendantFonts"][0].get_object().get("/FontDescriptor")
            desc = desc.get_object() if desc is not None else {}
            if not any(k in desc for k in ("/FontFile", "/FontFile2", "/FontFile3")):
                faltan.add(str(f.get("/BaseFont")))
    return sorted(faltan)


def main(ruta):
    p = Path(ruta)
    reader = PdfReader(p)
    errores, avisos = [], []
    prohibidos = cargar_prohibidos()
    if not ARCHIVO_PRIVADO.exists():
        avisos.append(f"No existe la lista privada {ARCHIVO_PRIVADO}: solo se revisó la etiqueta")
    n = len(reader.pages)
    tiene_referencias = False
    mb = p.stat().st_size / 1_048_576
    # Límites oficiales de LinkedIn: 100 MB y 300 páginas; criterio editorial: 8 a 12 páginas
    if mb >= 100 or n > 300:
        errores.append(f"Supera los límites de LinkedIn: {mb:.1f} MB, {n} páginas")
    if not 8 <= n <= 12:
        avisos.append(f"{n} páginas (criterio editorial: 8 a 12)")
    for i, page in enumerate(reader.pages, 1):
        w, h = float(page.mediabox.width), float(page.mediabox.height)
        if abs(w / h - 0.8) > 0.01:
            errores.append(f"Página {i}: proporción {w:.0f}×{h:.0f} pt, se esperaba 4:5")
        texto = page.extract_text() or ""
        for patron in prohibidos:
            if re.search(patron, texto, re.IGNORECASE):
                errores.append(f"Página {i}: contiene un término prohibido de la lista")
        tiene_cifra = re.search(r"\d", texto) is not None
        if 1 < i < n and tiene_cifra and not re.search(r"Nota\.|Elaboración propia", texto):
            avisos.append(f"Página {i}: tiene cifras pero no nota APA 7")
        if re.search(r"\b[Nn]\.?\s?°|\d%|\b\d{1,3}(?:,\d{3})+\b", texto):
            avisos.append(f"Página {i}: revisar «N.º», porcentajes y millares (RAE)")
        if re.search(r"(?m)^\s*Referencias\s*$", texto):
            tiene_referencias = True
    if not tiene_referencias:
        avisos.append("No se encontró la página «Referencias» (APA 7)")
    faltan = fuentes_sin_incrustar(reader)
    if faltan:
        errores.append("Fuentes sin incrustar: " + ", ".join(faltan))
    print(f"Archivo: {p.name} · {n} páginas · {mb:.2f} MB")
    for e in errores:
        print("ERROR  ", e)
    for a in avisos:
        print("AVISO  ", a)
    print("Resultado:", "NO PUBLICAR" if errores else "Listo para revisión final")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
