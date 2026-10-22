"""Tabla de tiempos AS-IS frente a TO-BE del paquete 3.4 (issue #25, D-PF01-19).

Lee ``docs/procesos/PF-01_tiempos.csv``, una fila por tarea: el AS-IS es una estimación del
autor (cantidad por tiempo unitario declarado) y el TO-BE, la mediana de tres corridas medidas
de cada script más la lectura estimada de las dos notas de validación (enmienda del
2026-10-19). Con esos datos arma:

- la tabla Markdown del README (tabla 1, APA 7);
- la figura SVG con la identidad visual de la skill marca-jose-caycho v2.3: titular en dos
  tonos, encabezado de tabla en Marino, filas alternas Niebla y Blanco, cifras alineadas a la
  derecha, el ahorro total en Azul (el hallazgo), nota APA 7 y cajetín «JC.»;
- la página HTML que se imprime a PDF con un navegador sin interfaz.

Solo usa la biblioteca estándar; el texto del SVG queda como texto (Arial), no como trazos.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import NamedTuple
from xml.sax.saxutils import escape

# Paleta de la marca JC. v2.3
MARINO, AZUL, BLANCO, NIEBLA = "#0F1F45", "#2A5CDA", "#FFFFFF", "#F4F6F9"
GRAFITO, GRIS, GRIS_CONTEXTO = "#141822", "#636975", "#C8CBCF"
FUENTE = "Arial, 'Liberation Sans', Helvetica, sans-serif"

PROCESOS = ("AS-IS", "TO-BE")
ACTIVIDADES = ("Obtención", "Consolidación", "Cálculo", "Control")
ANCHO, MARGEN = 1200, 56
FECHA_FIGURA = "2026-10-20"
FECHA_MEDICION = "2026-10-19"
TITULO = "PF-01 · Tiempo del reporte de siniestralidad, AS-IS frente a TO-BE"
NOTA = (
    "Nota. AS-IS: estimación del autor con las cantidades del proyecto y tiempos unitarios "
    "declarados. TO-BE: mediana de tres corridas medidas del flujo del repositorio, que "
    "reprocesa los 9 cortes e incluye la pausa de 2 s entre descargas, más 6 min estimados "
    "de lectura de las dos notas de validación. Equipo: Intel Core i7-1355U, 15.7 GB de RAM, "
    "Windows 11 Pro y Oracle Database 23ai Free 23.6. Detalle en "
    "docs/procesos/PF-01_tiempos.csv. Elaboración propia."
)


class Cifras(NamedTuple):
    """Totales en minutos de una fila de la tabla (una actividad o el total)."""

    asis: float
    tobe: float

    @property
    def ahorro(self) -> float:
        return self.asis - self.tobe

    @property
    def porcentaje(self) -> float:
        return 100 * self.ahorro / self.asis


def numero(valor: float, decimales: int = 1) -> str:
    """Número con punto decimal y millares separados con espacio (RAE)."""
    return f"{valor:,.{decimales}f}".replace(",", " ")


def leer_totales(ruta: Path) -> dict[str, dict[str, float]]:
    """Suma los minutos del CSV por proceso y actividad."""
    totales: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    with ruta.open(encoding="utf-8", newline="") as archivo:
        for fila in csv.DictReader(archivo):
            totales[fila["proceso"]][fila["actividad"]] += float(fila["minutos"])
    return totales


def filas(totales: dict[str, dict[str, float]]) -> list[tuple[str, Cifras]]:
    """Filas de la tabla en el orden de ACTIVIDADES, seguidas del total."""
    resultado = [(a, Cifras(totales["AS-IS"][a], totales["TO-BE"][a])) for a in ACTIVIDADES]
    total = Cifras(sum(c.asis for _, c in resultado), sum(c.tobe for _, c in resultado))
    return [*resultado, ("Total", total)]


def tabla_markdown(totales: dict[str, dict[str, float]]) -> str:
    """Tabla 1 del README: minutos por actividad, con el total en negrita."""
    lineas = [
        "| Actividad | AS-IS (min) | TO-BE (min) | Ahorro (min) | Ahorro (%) |",
        "|---|---:|---:|---:|---:|",
    ]
    for actividad, c in filas(totales):
        celdas = [
            actividad,
            numero(c.asis),
            numero(c.tobe),
            numero(c.ahorro),
            f"{numero(c.porcentaje)} %",
        ]
        if actividad == "Total":
            celdas = [f"**{celda}**" for celda in celdas]
        lineas.append("| " + " | ".join(celdas) + " |")
    return "\n".join(lineas)


def partir(texto: str, maximo: int) -> list[str]:
    """Parte un texto en líneas de hasta `maximo` caracteres, sin cortar palabras."""
    lineas: list[str] = []
    actual = ""
    for palabra in texto.split():
        if actual and len(actual) + 1 + len(palabra) > maximo:
            lineas.append(actual)
            actual = palabra
        else:
            actual = f"{actual} {palabra}".strip()
    return lineas + ([actual] if actual else [])


def texto(
    x: float,
    y: float,
    contenido: str,
    tam: int,
    color: str,
    peso: int = 400,
    ancla: str = "start",
    extra: str = "",
) -> str:
    """Elemento <text> del SVG; `contenido` debe llegar ya escapado."""
    return (
        f'<text x="{x:g}" y="{y:g}" font-size="{tam}" font-weight="{peso}" fill="{color}" '
        f'text-anchor="{ancla}"{extra}>{contenido}</text>'
    )


def rectangulo(x: float, y: float, ancho: float, alto: float, color: str) -> str:
    """Elemento <rect> del SVG."""
    return f'<rect x="{x}" y="{y}" width="{ancho}" height="{alto}" fill="{color}"/>'


def linea(x1: float, y1: float, x2: float, y2: float, color: str, grosor: str) -> str:
    """Elemento <line> del SVG."""
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{grosor}"/>'
    )


def construir_svg(totales: dict[str, dict[str, float]]) -> str:
    """Figura SVG de la tabla de tiempos con la identidad visual de la marca JC."""
    tabla = filas(totales)
    total = tabla[-1][1]
    titular = ' letter-spacing="-0.4"'

    piezas: list[str] = []
    y = 64
    # Titular en dos tonos: la idea en Grafito y la continuación en Gris, mismo tamaño
    idea = (
        f"La actualización con un corte nuevo pasa de {numero(total.asis)} "
        f"a {numero(total.tobe)} minutos."
    )
    piezas.append(texto(MARGEN, y, escape(idea), 28, GRAFITO, 600, extra=titular))
    y += 38
    continuacion = (
        f"Ahorro estimado de {numero(total.ahorro)} minutos "
        f"({numero(total.porcentaje)} %) con el flujo reproducible."
    )
    piezas.append(texto(MARGEN, y, escape(continuacion), 28, GRIS, 600, extra=titular))
    y += 36
    bajada = (
        "Minutos por actividad, desde la publicación del boletín hasta los indicadores "
        f"validados. AS-IS estimado por el autor; TO-BE medido el {FECHA_MEDICION}."
    )
    piezas.append(texto(MARGEN, y, escape(bajada), 15, GRIS))

    # Tabla: encabezado Marino, filas alternas, sin bordes verticales, cifras a la derecha
    y += 32
    ancho_tabla = ANCHO - 2 * MARGEN
    columnas = [  # (título, x de anclaje, ancla)
        ("Actividad", MARGEN + 20, "start"),
        ("AS-IS (min)", MARGEN + 560, "end"),
        ("TO-BE (min)", MARGEN + 730, "end"),
        ("Ahorro (min)", MARGEN + 900, "end"),
        ("Ahorro (%)", MARGEN + ancho_tabla - 20, "end"),
    ]
    alto_fila = 46
    piezas.append(rectangulo(MARGEN, y, ancho_tabla, alto_fila, MARINO))
    for titulo, x, ancla in columnas:
        piezas.append(texto(x, y + 29, titulo, 15, BLANCO, 600, ancla))
    y += alto_fila
    for i, (actividad, c) in enumerate(tabla[:-1]):
        fondo = NIEBLA if i % 2 == 0 else BLANCO
        piezas.append(rectangulo(MARGEN, y, ancho_tabla, alto_fila, fondo))
        valores = [
            actividad,
            numero(c.asis),
            numero(c.tobe),
            numero(c.ahorro),
            f"{numero(c.porcentaje)} %",
        ]
        for (_, x, ancla), valor in zip(columnas, valores, strict=True):
            piezas.append(texto(x, y + 29, escape(valor), 16, GRAFITO, 400, ancla))
        y += alto_fila
    # Fila total: línea superior Grafito y negrita; el ahorro total es el hallazgo (Azul)
    piezas.append(linea(MARGEN, y, MARGEN + ancho_tabla, y, GRAFITO, "1.5"))
    valores = [
        "Total",
        numero(total.asis),
        numero(total.tobe),
        numero(total.ahorro),
        f"{numero(total.porcentaje)} %",
    ]
    colores = [GRAFITO, GRAFITO, GRAFITO, AZUL, AZUL]
    for (_, x, ancla), valor, color in zip(columnas, valores, colores, strict=True):
        piezas.append(texto(x, y + 30, escape(valor), 17, color, 700, ancla))
    y += alto_fila + 8
    piezas.append(linea(MARGEN, y, MARGEN + ancho_tabla, y, GRIS_CONTEXTO, "1"))

    # Nota APA 7 («Nota.» en cursiva)
    y += 30
    for j, renglon in enumerate(partir(NOTA, 158)):
        if j == 0 and renglon.startswith("Nota."):
            resto = escape(renglon[len("Nota.") :])
            contenido = f'<tspan font-style="italic">Nota.</tspan>{resto}'
        else:
            contenido = escape(renglon)
        piezas.append(texto(MARGEN, y, contenido, 13, GRIS))
        y += 20

    # Cajetín: «JC.» con punto Azul, etiqueta de portafolio, fecha y repositorio
    y += 24
    piezas.append(linea(MARGEN, y, ANCHO - MARGEN, y, GRIS, "1"))
    y += 46
    marca = f'JC<tspan fill="{AZUL}">.</tspan>'
    piezas.append(texto(MARGEN + 4, y, marca, 32, GRAFITO, 700, extra=' letter-spacing="-1.6"'))
    etiqueta = escape("Portafolio · PF-01 · Tiempo del reporte, AS-IS frente a TO-BE")
    piezas.append(texto(MARGEN + 70, y - 14, etiqueta, 14, GRAFITO, 700))
    piezas.append(texto(MARGEN + 70, y + 4, FECHA_FIGURA, 12, GRIS))
    repositorio = "github.com/josecaychoa/pf-01-siniestralidad-sbs"
    piezas.append(texto(ANCHO - MARGEN, y - 4, repositorio, 12, GRIS, 400, "end"))
    alto = y + 34

    descripcion = (
        f"AS-IS {numero(total.asis)} min; TO-BE {numero(total.tobe)} min; "
        f"ahorro {numero(total.ahorro)} min ({numero(total.porcentaje)} %)."
    )
    cabecera = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ANCHO}" height="{alto}" '
        f'viewBox="0 0 {ANCHO} {alto}" font-family="{FUENTE}" role="img" '
        f'aria-labelledby="t d">'
    )
    return "\n".join(
        [
            cabecera,
            f'<title id="t">{escape(TITULO)}</title>',
            f'<desc id="d">{escape(descripcion)}</desc>',
            f'<rect width="{ANCHO}" height="{alto}" fill="{BLANCO}"/>',
            *piezas,
            "</svg>",
            "",
        ]
    )


def pagina_impresion(svg: str) -> str:
    """Página HTML del tamaño exacto de la figura, para imprimirla a PDF sin márgenes."""
    inicio = svg.index("<svg")
    ancho = svg.split('width="', 1)[1].split('"', 1)[0]
    alto = svg.split('height="', 1)[1].split('"', 1)[0]
    estilo = (
        f"@page{{size:{ancho}px {alto}px;margin:0}}"
        "html,body{margin:0;padding:0;background:#fff}svg{display:block}"
    )
    return (
        '<!doctype html><html lang="es"><head><meta charset="utf-8">'
        f"<title>{escape(TITULO)}</title>\n<style>{estilo}</style></head><body>"
        f"{svg[inicio:].rstrip()}\n</body></html>"
    )


def escribir(ruta: Path, contenido: str, sobrescribir: bool = False) -> bool:
    """Escribe `contenido` en UTF-8 con LF; no reemplaza un archivo existente sin permiso.

    La figura publicada lleva un manifiesto de procedencia (Content Credentials) que se
    pierde si se vuelve a generar encima; por eso hay que pedirlo de forma explícita.
    """
    if ruta.exists() and not sobrescribir:
        return False
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8", newline="\n") as archivo:
        archivo.write(contenido)
    return True
