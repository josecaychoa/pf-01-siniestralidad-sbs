"""Serie del índice de siniestralidad del sistema asegurador, 2019-2026 (paquete 4.2, issue #11).

Lee ``data/processed/indicadores_riesgo.csv`` (una fila por riesgo y corte, D-PF01-23), suma las
primas y los siniestros de los 48 riesgos de cada corte y calcula el índice directo y retenido
del sistema, igual que la tabla 1 de ``reports/validacion_resultados.md``. Con esa serie arma:

- la tabla Markdown de la sección 3 del informe (``reports/informe.md``);
- la figura SVG de la serie con la identidad visual de la skill marca-jose-caycho v2.3: titular
  en dos tonos que afirma el hallazgo, serie del hallazgo en Azul y contexto en Gris de
  contexto, etiquetas directas en lugar de leyenda, nota APA 7 y cajetín «JC.».

Solo usa la biblioteca estándar; el texto del SVG queda como texto (Arial), no como trazos.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import NamedTuple
from xml.sax.saxutils import escape

from pf_01_siniestralidad_sbs.tabla_tiempos import (
    AZUL,
    BLANCO,
    FUENTE,
    GRAFITO,
    GRIS,
    GRIS_CONTEXTO,
    linea,
    numero,
    partir,
    texto,
)

ANCHO, MARGEN = 1200, 56
FECHA_FIGURA = "2026-10-26"
TITULO = "PF-01 · Índice de siniestralidad del sistema asegurador peruano, 2019-2026"
NOTA = (
    "Nota. Elaboración propia con datos de SBS (s. f.-a, s. f.-b, s. f.-c, s. f.-d): suma de "
    "las primas y los siniestros, netos y retenidos, de los 48 riesgos de "
    "data/processed/indicadores_riesgo.csv por corte (descarga del 11 de octubre de 2026). "
    "Serie igual a la tabla 1 de reports/validacion_resultados.md."
)
MESES_CORTOS = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")
MESES_LARGOS = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


class Corte(NamedTuple):
    """Totales del sistema en un corte: montos en miles de soles e índices en porcentaje."""

    fecha: date
    meses: int
    primas_netas: float
    primas_retenidas: float
    siniestros_netos: float
    siniestros_retenidos: float

    @property
    def directa(self) -> float:
        return 100 * self.siniestros_netos / self.primas_netas

    @property
    def retenida(self) -> float:
        return 100 * self.siniestros_retenidos / self.primas_retenidas


def mes_largo(fecha: date) -> str:
    """Mes y año en palabras, en minúscula («agosto de 2026»)."""
    return f"{MESES_LARGOS[fecha.month - 1]} de {fecha.year}"


def leer_serie(ruta: Path) -> list[Corte]:
    """Suma primas y siniestros por corte sobre todas las filas de riesgo del CSV."""
    sumas: dict[tuple[date, int], list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
    with ruta.open(encoding="utf-8", newline="") as archivo:
        for fila in csv.DictReader(archivo):
            clave = (date.fromisoformat(fila["fecha_corte"]), int(fila["meses_acumulados"]))
            acumulado = sumas[clave]
            acumulado[0] += float(fila["primas_netas"])
            acumulado[1] += float(fila["primas_retenidas"])
            acumulado[2] += float(fila["siniestros_netos"])
            acumulado[3] += float(fila["siniestros_retenidos"])
    return [
        Corte(fecha, meses, *valores)
        for (fecha, meses), valores in sorted(sumas.items(), key=lambda par: par[0][0])
    ]


def corte_interanual(serie: list[Corte]) -> tuple[Corte, Corte]:
    """Último corte de la serie y el corte del mismo mes del año anterior."""
    ultimo = serie[-1]
    anterior = next(c for c in serie if c.fecha == ultimo.fecha.replace(year=ultimo.fecha.year - 1))
    return ultimo, anterior


def tabla_markdown(serie: list[Corte]) -> str:
    """Tabla de la sección 3 del informe: primas en millones de soles e índices en porcentaje."""
    lineas = [
        "| Corte | Meses | Primas netas (millones de S/) | Directa (%) | Retenida (%) |",
        "|---|---:|---:|---:|---:|",
    ]
    for corte in serie:
        celdas = [
            corte.fecha.isoformat(),
            str(corte.meses),
            numero(corte.primas_netas / 1000),
            numero(corte.directa),
            numero(corte.retenida),
        ]
        lineas.append("| " + " | ".join(celdas) + " |")
    return "\n".join(lineas)


def circulo(x: float, y: float, r: float, relleno: str, borde: str = "", grosor: float = 0) -> str:
    """Elemento <circle> del SVG; con `borde` dibuja un punto hueco."""
    contorno = f' stroke="{borde}" stroke-width="{grosor:g}"' if borde else ""
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:g}" fill="{relleno}"{contorno}/>'


def polilinea(puntos: list[tuple[float, float]], color: str) -> str:
    """Elemento <polyline> del SVG con las esquinas y los extremos redondeados."""
    trazo = " ".join(f"{x:.1f},{y:.1f}" for x, y in puntos)
    return (
        f'<polyline points="{trazo}" fill="none" stroke="{color}" stroke-width="2.5" '
        'stroke-linejoin="round" stroke-linecap="round"/>'
    )


def construir_svg(serie: list[Corte]) -> str:
    """Figura SVG de la serie con la identidad visual de la marca JC."""
    ultimo, anterior = corte_interanual(serie)
    delta = ultimo.directa - anterior.directa
    maximo = max(serie, key=lambda c: c.directa)
    titular = ' letter-spacing="-0.4"'

    piezas: list[str] = []
    y = 64
    # Titular en dos tonos: la idea en Grafito y la continuación en Gris, mismo tamaño
    idea = (
        f"La siniestralidad directa del sistema subió a {numero(ultimo.directa)} % "
        f"en {mes_largo(ultimo.fecha)}."
    )
    piezas.append(texto(MARGEN, y, escape(idea), 28, GRAFITO, 600, extra=titular))
    y += 38
    continuacion = (
        f"Son {numero(delta)} puntos más que en {mes_largo(anterior.fecha)}; "
        f"la retenida llegó a {numero(ultimo.retenida)} %."
    )
    piezas.append(texto(MARGEN, y, escape(continuacion), 28, GRIS, 600, extra=titular))
    y += 36
    bajada = (
        "Índice del sistema en porcentaje: siniestros entre primas acumulados al corte. "
        "Diciembre acumula 12 meses; agosto, 8 (puntos huecos)."
    )
    piezas.append(texto(MARGEN, y, escape(bajada), 15, GRIS))

    # Área del gráfico: cuadrícula horizontal fina, eje inferior y escala de tiempo real
    x0, x1 = MARGEN + 44, ANCHO - MARGEN - 128
    alto_grafico = 300
    arriba = y + 32
    abajo = arriba + alto_grafico
    vmin, vmax = 36, 62
    dias = (serie[-1].fecha - serie[0].fecha).days

    def px(fecha: date) -> float:
        return x0 + (fecha - serie[0].fecha).days / dias * (x1 - x0)

    def py(valor: float) -> float:
        return abajo - (valor - vmin) / (vmax - vmin) * alto_grafico

    for marca in range(40, 61, 5):
        piezas.append(linea(x0, py(marca), x1, py(marca), GRIS_CONTEXTO, "0.6"))
        piezas.append(texto(x0 - 12, py(marca) + 4, f"{marca} %", 12, GRIS, ancla="end"))
    piezas.append(linea(x0, abajo, x1, abajo, GRIS, "1"))
    for corte in serie:
        etiqueta = f"{MESES_CORTOS[corte.fecha.month - 1]} {corte.fecha.year % 100:02d}"
        piezas.append(texto(px(corte.fecha), abajo + 24, etiqueta, 12, GRIS, ancla="middle"))

    # Series: la directa es el hallazgo (Azul) y la retenida, el contexto (Gris de contexto)
    piezas.append(polilinea([(px(c.fecha), py(c.retenida)) for c in serie], GRIS_CONTEXTO))
    piezas.append(polilinea([(px(c.fecha), py(c.directa)) for c in serie], AZUL))
    for corte in serie:
        for valor, color in ((corte.retenida, GRIS_CONTEXTO), (corte.directa, AZUL)):
            if corte.meses == 12:
                piezas.append(circulo(px(corte.fecha), py(valor), 4, color))
            else:
                piezas.append(circulo(px(corte.fecha), py(valor), 4, BLANCO, color, 2))

    # Etiquetas directas en lugar de leyenda, con el valor del último corte
    primera = serie[0]
    piezas.append(
        texto(
            x1 + 14, py(ultimo.directa) + 5, f"Directa · {numero(ultimo.directa)} %", 14, AZUL, 600
        )
    )
    piezas.append(
        texto(
            x1 + 14,
            py(ultimo.retenida) + 5,
            f"Retenida · {numero(ultimo.retenida)} %",
            14,
            GRIS,
            600,
        )
    )
    piezas.append(texto(x0 + 2, py(primera.directa) - 12, f"{numero(primera.directa)} %", 12, GRIS))
    piezas.append(
        texto(x0 + 2, py(primera.retenida) + 22, f"{numero(primera.retenida)} %", 12, GRIS)
    )
    piezas.append(
        texto(
            px(anterior.fecha),
            py(anterior.directa) - 14,
            f"{numero(anterior.directa)} %",
            12,
            GRIS,
            ancla="middle",
        )
    )
    piezas.append(
        texto(
            px(maximo.fecha),
            py(maximo.directa) - 14,
            f"Máximo de la serie: {numero(maximo.directa)} %",
            13,
            GRIS,
            ancla="middle",
        )
    )
    # Anotación directa sobre el hallazgo
    anotacion = f"+{numero(delta)} p. p. frente a {mes_largo(anterior.fecha)}"
    piezas.append(texto(x1, py(ultimo.directa) - 26, escape(anotacion), 13, AZUL, 600, ancla="end"))

    # Nota APA 7 («Nota.» en cursiva)
    y = abajo + 56
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
    etiqueta = escape("Portafolio · PF-01 · Siniestralidad del sistema, 2019-2026")
    piezas.append(texto(MARGEN + 70, y - 14, etiqueta, 14, GRAFITO, 700))
    piezas.append(texto(MARGEN + 70, y + 4, FECHA_FIGURA, 12, GRIS))
    repositorio = "github.com/josecaychoa/pf-01-siniestralidad-sbs"
    piezas.append(texto(ANCHO - MARGEN, y - 4, repositorio, 12, GRIS, 400, "end"))
    alto = y + 34

    descripcion = (
        f"Siniestralidad directa de {numero(serie[0].directa)} % en {mes_largo(serie[0].fecha)} a "
        f"{numero(ultimo.directa)} % en {mes_largo(ultimo.fecha)}, con un máximo de "
        f"{numero(maximo.directa)} % en {mes_largo(maximo.fecha)}; retenida de "
        f"{numero(serie[0].retenida)} % a {numero(ultimo.retenida)} %."
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
