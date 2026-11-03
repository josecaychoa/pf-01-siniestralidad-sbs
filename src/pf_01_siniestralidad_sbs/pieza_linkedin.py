"""Figuras del documento PDF de LinkedIn de PF-01 (paquete 5.2, #15).

Cinco figuras para la tarjeta blanca de las páginas de 1080 × 1350 px (4:5) de la skill
``linkedin-pieza-editorial`` v1.3. El SVG mide lo mismo que el interior de la tarjeta
(856 × 650), así que una unidad del SVG equivale a un píxel de la página: los textos tienen
22 px como mínimo para que se lean en el teléfono (hallazgo LI-05 de la auditoría).

El titular, la etiqueta «Figura N» y la nota APA 7 viven en la página HTML, no en el SVG.
Cada figura conserva un subtítulo con la unidad y el período, y título y descripción
accesibles. Colores de la marca JC.: hallazgo en Azul, contexto en Gris de contexto y serie
principal sin hallazgo en Marino. Solo usa la biblioteca estándar.

    Figura 1  contribución de cada riesgo al cambio del índice directo del sistema
    Figura 2  índice del sistema con y sin Vida Individual de Largo Plazo e Incendio
    Figura 3  siniestros mensuales de Vida Individual de Largo Plazo, 2025-2026
    Figura 4  Incendio: siniestralidad directa frente a retenida, agosto de 2026
    Figura 5  índice directo en períodos de 12 meses, 2019-2026
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import NamedTuple
from xml.sax.saxutils import escape

from pf_01_siniestralidad_sbs import contribucion as co
from pf_01_siniestralidad_sbs.serie_sistema import MESES_CORTOS, leer_serie
from pf_01_siniestralidad_sbs.tabla_tiempos import (
    AZUL,
    BLANCO,
    GRAFITO,
    GRIS,
    GRIS_CONTEXTO,
    MARINO,
    linea,
    numero,
    rectangulo,
    texto,
)

ANCHO, ALTO = 856, 650
FUENTE = "Geist, Arial, 'Liberation Sans', Helvetica, sans-serif"
INICIO, FIN = date(2025, 8, 31), date(2026, 8, 31)
DICIEMBRE_PREVIO = date(2025, 12, 31)
TAM_TEXTO, TAM_CIFRA, TAM_EJE = 24, 30, 22  # px de la página; mínimo 22 (LI-05)


class Cifras(NamedTuple):
    """Cifras de las cinco figuras, calculadas desde los CSV versionados."""

    directa: co.Descomposicion
    sin_dos_inicio: float  # índice directo sin Vida Individual ni Incendio, agosto de 2025
    sin_dos_fin: float  # ídem, agosto de 2026
    incendio_directa: float
    incendio_retenida: float
    incendio_cedido: float  # % de los siniestros acumulados cedido en reaseguro
    anuales: list[tuple[int, float]]  # (año, índice directo) de los cortes de diciembre
    doce_meses: float  # índice directo de los 12 meses a agosto de 2026
    vida_mensual: list[tuple[date, float]]  # siniestros del mes, millones de soles


def calcular(indicadores: Path, mensual: Path) -> Cifras:
    """Calcula todas las cifras de las figuras desde los CSV de ``data/processed``."""
    cortes = co.leer_cortes(indicadores)
    directa = co.descomponer(cortes, INICIO, FIN, "directa")
    excluir = co.HALLAZGOS
    incendio = next(r for r in cortes[FIN] if r.riesgo == co.INCENDIO)

    serie = {c.fecha: c for c in leer_serie(indicadores)}
    anuales = [(f.year, c.directa) for f, c in serie.items() if f.month == 12]
    # 12 meses a agosto de 2026 = diciembre de 2025 + enero-agosto de 2026 − enero-agosto de 2025
    dic, ago_fin, ago_ini = serie[DICIEMBRE_PREVIO], serie[FIN], serie[INICIO]
    siniestros = dic.siniestros_netos + ago_fin.siniestros_netos - ago_ini.siniestros_netos
    primas = dic.primas_netas + ago_fin.primas_netas - ago_ini.primas_netas

    vida: list[tuple[date, float]] = []
    with mensual.open(encoding="utf-8", newline="") as archivo:
        for fila in csv.DictReader(archivo):
            if fila["riesgo_comparable"] == co.VIDA_LARGO_PLAZO:
                mes = date.fromisoformat(fila["fecha_corte"])
                vida.append((mes, float(fila["siniestros_netos_mes"]) / 1000))
    vida.sort()

    return Cifras(
        directa,
        co.indice(cortes[INICIO], "directa", excluir),
        co.indice(cortes[FIN], "directa", excluir),
        100 * incendio.siniestros_netos / incendio.primas_netas,
        100 * incendio.siniestros_retenidos / incendio.primas_retenidas,
        100 * (1 - incendio.siniestros_retenidos / incendio.siniestros_netos),
        anuales,
        100 * siniestros / primas,
        vida,
    )


# --------------------------------------------------------------------------------------
# Utilidades de formato y de SVG
# --------------------------------------------------------------------------------------


def signo(valor: float, decimales: int = 2) -> str:
    """Número con signo explícito y signo menos tipográfico (RAE): «+5.12», «−0.49»."""
    return ("+" if valor >= 0 else "−") + numero(abs(valor), decimales)


def porcentaje(valor: float) -> str:
    """«48.9 %» con espacio fino no separable antes del signo (RAE)."""
    return f"{numero(valor)} %"


def _documento(piezas: list[str], titulo: str, descripcion: str) -> str:
    """SVG del tamaño de la tarjeta, con título y descripción accesibles."""
    cabecera = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ANCHO}" height="{ALTO}" '
        f'viewBox="0 0 {ANCHO} {ALTO}" font-family="{FUENTE}" role="img" '
        f'aria-labelledby="t d">'
    )
    return "\n".join(
        [
            cabecera,
            f'<title id="t">{escape(titulo)}</title>',
            f'<desc id="d">{escape(descripcion)}</desc>',
            f'<rect width="{ANCHO}" height="{ALTO}" fill="{BLANCO}"/>',
            *piezas,
            "</svg>",
            "",
        ]
    )


def _subtitulo(piezas: list[str], contenido: str) -> None:
    """Subtítulo con unidad y período, arriba a la izquierda."""
    piezas.append(texto(0, 26, escape(contenido), TAM_EJE, GRIS))


def _circulo(x: float, y: float, r: float, relleno: str, borde: str = "") -> str:
    extra = f' stroke="{borde}" stroke-width="3"' if borde else ""
    return f'<circle cx="{x:g}" cy="{y:g}" r="{r:g}" fill="{relleno}"{extra}/>'


def _trazo(x1: float, y1: float, x2: float, y2: float, color: str, grosor: float = 4) -> str:
    return (
        f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{color}" '
        f'stroke-width="{grosor:g}" stroke-linecap="round"/>'
    )


# --------------------------------------------------------------------------------------
# Figura 1 · Contribución por riesgo
# --------------------------------------------------------------------------------------


def figura_contribucion(c: Cifras) -> str:
    """Barras horizontales: aporte de cada riesgo al cambio del índice directo del sistema."""
    d = c.directa
    vida, incendio = d.de(co.VIDA_LARGO_PLAZO), d.de(co.INCENDIO)
    renta = d.contribuciones[2]  # tercer aporte al alza (Renta Particular)
    otros = [
        x for x in d.contribuciones if x.riesgo not in {vida.riesgo, incendio.riesgo, renta.riesgo}
    ]
    filas = [
        (vida.riesgo, vida.contribucion, AZUL),
        (incendio.riesgo, incendio.contribucion, AZUL),
        (renta.riesgo, renta.contribucion, GRIS_CONTEXTO),
        (f"Otros {len(otros)} riesgos", sum(x.contribucion for x in otros), GRIS_CONTEXTO),
    ]
    minimo, maximo = -4.0, 8.5
    izquierda, derecha = 0.0, 700.0
    x0 = izquierda + (derecha - izquierda) * (-minimo) / (maximo - minimo)

    def px(valor: float) -> float:
        return x0 + (derecha - izquierda) * valor / (maximo - minimo)

    piezas: list[str] = []
    _subtitulo(piezas, "Contribución al cambio del índice directo, en p. p.")
    y = 92.0
    alto_barra, paso = 40.0, 104.0
    for nombre, valor, color in filas:
        piezas.append(texto(0, y, escape(nombre), TAM_TEXTO, GRAFITO, 600))
        inicio, fin = sorted((px(0), px(valor)))
        piezas.append(
            rectangulo(round(inicio, 1), y + 14, round(fin - inicio, 1), alto_barra, color)
        )
        piezas.append(linea(round(x0, 1), y + 6, round(x0, 1), y + 62, GRIS, "1.5"))
        color_cifra = AZUL if color == AZUL else GRAFITO
        if valor >= 0:
            piezas.append(texto(fin + 12, y + 46, signo(valor), TAM_CIFRA, color_cifra, 600))
        else:
            piezas.append(
                texto(inicio - 12, y + 46, signo(valor), TAM_CIFRA, color_cifra, 600, "end")
            )
        y += paso
    # Llave de los 46 riesgos que no son Vida Individual ni Incendio
    resto = sum(v for _, v, col in filas if col == GRIS_CONTEXTO)
    llave_x, y_sup, y_inf = 716.0, 92.0 + 2 * paso + 14, 92.0 + 3 * paso + 54
    piezas.append(linea(llave_x, y_sup, llave_x, y_inf, GRIS, "2"))
    piezas.append(linea(llave_x - 12, y_sup, llave_x, y_sup, GRIS, "2"))
    piezas.append(linea(llave_x - 12, y_inf, llave_x, y_inf, GRIS, "2"))
    piezas.append(texto(llave_x + 14, (y_sup + y_inf) / 2 - 6, "46 riesgos", TAM_EJE, GRIS))
    piezas.append(texto(llave_x + 14, (y_sup + y_inf) / 2 + 22, signo(resto), TAM_EJE, GRIS, 600))
    # Total del sistema, separado por una línea
    y_total = y + 6
    piezas.append(linea(0, y_total - 40, ANCHO, y_total - 40, GRIS_CONTEXTO, "2"))
    piezas.append(texto(0, y_total, "Sistema", TAM_TEXTO, GRAFITO, 600))
    piezas.append(
        rectangulo(round(x0, 1), y_total + 14, round(px(d.cambio) - x0, 1), alto_barra, MARINO)
    )
    piezas.append(texto(px(d.cambio) + 12, y_total + 46, signo(d.cambio), TAM_CIFRA, MARINO, 600))
    piezas.append(linea(round(x0, 1), y_total + 6, round(x0, 1), y_total + 62, GRIS, "1.5"))
    descripcion = (
        f"El índice directo del sistema subió {signo(d.cambio)} p. p.: Vida Individual de Largo "
        f"Plazo aporta {signo(vida.contribucion)} e Incendio {signo(incendio.contribucion)}; "
        f"Renta Particular {signo(renta.contribucion)} y los otros {len(otros)} riesgos "
        f"{signo(filas[3][1])}."
    )
    return _documento(
        piezas, "Contribución de cada riesgo al cambio del índice directo", descripcion
    )


# --------------------------------------------------------------------------------------
# Figura 2 · Índice con y sin los dos riesgos
# --------------------------------------------------------------------------------------


def figura_con_sin(c: Cifras) -> str:
    """Pendiente entre agosto de 2025 y agosto de 2026: sistema completo y sin los dos riesgos."""
    d = c.directa
    minimo, maximo = 35.0, 55.0
    arriba, abajo = 70.0, 590.0
    xa, xb = 150.0, 520.0

    def py(valor: float) -> float:
        return abajo - (abajo - arriba) * (valor - minimo) / (maximo - minimo)

    piezas: list[str] = []
    _subtitulo(piezas, "Índice de siniestralidad directa acumulado a agosto, en %")
    for marca in range(35, 56, 5):
        piezas.append(linea(60, py(marca), ANCHO, py(marca), GRIS_CONTEXTO, "1"))
        piezas.append(texto(0, py(marca) + 8, str(marca), TAM_EJE, GRIS))
    for x, etiqueta in ((xa, "Ago. 2025"), (xb, "Ago. 2026")):
        piezas.append(texto(x, ALTO - 16, etiqueta, TAM_EJE, GRIS, 400, "middle"))
    series = [
        (d.indice_inicio, d.indice_fin, AZUL, ("Sistema", "completo")),
        (c.sin_dos_inicio, c.sin_dos_fin, MARINO, ("Sin Vida Individual", "ni Incendio")),
    ]
    for inicio, fin, color, nombre in series:
        piezas.append(_trazo(xa, py(inicio), xb, py(fin), color))
        piezas.append(_circulo(xa, py(inicio), 9, color))
        piezas.append(_circulo(xb, py(fin), 9, color))
        piezas.append(
            texto(xa - 22, py(inicio) + 10, porcentaje(inicio), TAM_CIFRA, color, 600, "end")
        )
        piezas.append(texto(xb + 22, py(fin) + 10, porcentaje(fin), TAM_CIFRA, color, 600))
        piezas.append(texto(xb + 22, py(fin) + 42, escape(nombre[0]), TAM_EJE, color, 400))
        piezas.append(texto(xb + 22, py(fin) + 68, escape(nombre[1]), TAM_EJE, color, 400))
    piezas.append(
        texto(
            (xa + xb) / 2 - 20,
            py((d.indice_inicio + d.indice_fin) / 2) - 24,
            f"{signo(d.cambio, 1)} p. p.",
            TAM_TEXTO,
            AZUL,
            600,
            "end",
        )
    )
    cambio_resto = c.sin_dos_fin - c.sin_dos_inicio
    piezas.append(
        texto(
            (xa + xb) / 2,
            py((c.sin_dos_inicio + c.sin_dos_fin) / 2) + 40,
            f"{signo(cambio_resto, 1)} p. p.",
            TAM_TEXTO,
            MARINO,
            600,
            "middle",
        )
    )
    descripcion = (
        f"De agosto de 2025 a agosto de 2026, el índice directo del sistema pasa de "
        f"{porcentaje(d.indice_inicio)} a {porcentaje(d.indice_fin)}; sin Vida Individual de "
        f"Largo Plazo ni Incendio, pasa de {porcentaje(c.sin_dos_inicio)} a "
        f"{porcentaje(c.sin_dos_fin)}."
    )
    return _documento(piezas, "Índice directo con y sin los dos riesgos", descripcion)


# --------------------------------------------------------------------------------------
# Figura 3 · Siniestros mensuales de Vida Individual de Largo Plazo
# --------------------------------------------------------------------------------------


def figura_vida_mensual(c: Cifras) -> str:
    """Barras mensuales; desde marzo de 2026 (vigencia de la norma) en Azul."""
    meses = c.vida_mensual
    antes = [v for m, v in meses if m < co.MES_NORMA]
    despues = [v for m, v in meses if m > co.MES_NORMA]
    marzo = next(v for m, v in meses if m == co.MES_NORMA)
    maximo = 350.0
    arriba, abajo = 150.0, 560.0
    izquierda = 56.0
    paso = (ANCHO - izquierda) / len(meses)
    ancho_barra = paso * 0.66

    def py(valor: float) -> float:
        return abajo - (abajo - arriba) * valor / maximo

    piezas: list[str] = []
    _subtitulo(piezas, "Siniestros del mes, en millones de soles")
    for marca in (0, 100, 200, 300):
        piezas.append(linea(izquierda, py(marca), ANCHO, py(marca), GRIS_CONTEXTO, "1"))
        piezas.append(texto(0, py(marca) + 8, str(marca), TAM_EJE, GRIS))
    for i, (mes, valor) in enumerate(meses):
        x = izquierda + i * paso + (paso - ancho_barra) / 2
        color = AZUL if mes >= co.MES_NORMA else GRIS_CONTEXTO
        piezas.append(
            rectangulo(
                round(x, 1),
                round(py(valor), 1),
                round(ancho_barra, 1),
                round(abajo - py(valor), 1),
                color,
            )
        )
        if mes.month in (1, 7) or mes == co.MES_NORMA:
            etiqueta = MESES_CORTOS[mes.month - 1].capitalize() + "."
            piezas.append(
                texto(x + ancho_barra / 2, abajo + 32, etiqueta, TAM_EJE, GRIS, 400, "middle")
            )
        if mes.month == 1:
            piezas.append(texto(x, abajo + 62, str(mes.year), TAM_EJE, GRAFITO, 600))
    # Vigencia de la norma
    i_marzo = next(i for i, (m, _) in enumerate(meses) if m == co.MES_NORMA)
    x_norma = izquierda + i_marzo * paso - 2
    piezas.append(linea(round(x_norma, 1), 60, round(x_norma, 1), abajo, GRIS, "1.5"))
    piezas.append(texto(x_norma - 12, 72, "Marzo de 2026: rige la", TAM_EJE, GRAFITO, 400, "end"))
    piezas.append(
        texto(x_norma - 12, 100, "Resolución SBS N.º 00085-2026", TAM_EJE, GRAFITO, 400, "end")
    )
    # Anotaciones directas
    piezas.append(texto(x_norma + 8, py(marzo) - 12, numero(marzo), TAM_TEXTO, AZUL, 600))
    promedio_antes = sum(antes) / len(antes)
    promedio_despues = sum(despues) / len(despues)
    piezas.append(
        texto(izquierda, py(60), f"Promedio: {numero(promedio_antes)}", TAM_TEXTO, GRAFITO, 600)
    )
    piezas.append(texto(izquierda, py(60) + 28, "enero de 2025 a febrero de 2026", TAM_EJE, GRIS))
    piezas.append(
        texto(
            ANCHO,
            py(max(despues)) - 52,
            f"Promedio: {numero(promedio_despues)}",
            TAM_TEXTO,
            AZUL,
            600,
            "end",
        )
    )
    piezas.append(texto(ANCHO, py(max(despues)) - 24, "abril a agosto", TAM_EJE, GRIS, 400, "end"))
    descripcion = (
        f"Los siniestros mensuales de Vida Individual de Largo Plazo promedian "
        f"{numero(promedio_antes)} millones de soles de enero de 2025 a febrero de 2026, saltan a "
        f"{numero(marzo)} millones en marzo de 2026 y promedian {numero(promedio_despues)} "
        f"millones de abril a agosto."
    )
    return _documento(piezas, "Siniestros mensuales de Vida Individual de Largo Plazo", descripcion)


# --------------------------------------------------------------------------------------
# Figura 4 · Incendio, directa frente a retenida
# --------------------------------------------------------------------------------------


def figura_incendio(c: Cifras) -> str:
    """Dos barras horizontales con la referencia del 100 %."""
    maximo = 250.0
    izquierda, derecha = 0.0, 760.0

    def px(valor: float) -> float:
        return izquierda + (derecha - izquierda) * valor / maximo

    piezas: list[str] = []
    _subtitulo(piezas, "Incendio, índice de siniestralidad acumulado a agosto de 2026, en %")
    filas = [
        ("Directa: siniestros sobre primas netas", c.incendio_directa, AZUL),
        ("Retenida: sin la parte cedida en reaseguro", c.incendio_retenida, MARINO),
    ]
    y = 130.0
    for nombre, valor, color in filas:
        piezas.append(texto(0, y, escape(nombre), TAM_TEXTO, GRAFITO, 600))
        piezas.append(rectangulo(0, y + 16, round(px(valor), 1), 72, color))
        piezas.append(texto(px(valor) + 14, y + 66, porcentaje(valor), 36, color, 600))
        y += 170
    x100 = px(100)
    for fila in range(len(filas)):
        y_barra = 130.0 + 170 * fila + 6
        piezas.append(linea(round(x100, 1), y_barra, round(x100, 1), y_barra + 92, GRIS, "2"))
    piezas.append(linea(round(x100, 1), y - 22, round(x100, 1), y - 2, GRIS, "2"))
    piezas.append(
        texto(x100, y + 26, "100\u202f%: siniestros iguales a primas", TAM_EJE, GRIS, 400, "middle")
    )
    y += 50
    piezas.append(
        texto(
            0,
            y + 20,
            f"El {porcentaje(c.incendio_cedido)} de los siniestros",
            TAM_TEXTO,
            GRAFITO,
            600,
        )
    )
    piezas.append(
        texto(0, y + 52, "acumulados del año se cedió en reaseguro.", TAM_TEXTO, GRAFITO, 600)
    )
    descripcion = (
        f"En agosto de 2026, Incendio tiene una siniestralidad directa de "
        f"{porcentaje(c.incendio_directa)} y una retenida de {porcentaje(c.incendio_retenida)}; "
        f"el {porcentaje(c.incendio_cedido)} de los siniestros se cedió en reaseguro."
    )
    return _documento(piezas, "Incendio: siniestralidad directa frente a retenida", descripcion)


# --------------------------------------------------------------------------------------
# Figura 5 · Serie en períodos de 12 meses
# --------------------------------------------------------------------------------------


# Posición de la etiqueta de cada punto para que no la cruce la línea
POSICION_ETIQUETA = {
    "2020": "abajo",
    "2022": "derecha",
    "2023": "derecha",
    "2024": "derecha",
    "2025": "abajo",
}


def figura_serie_12_meses(c: Cifras) -> str:
    """Índice directo de los años 2019-2025 y de los 12 meses a agosto de 2026."""
    puntos = [(str(a), v) for a, v in c.anuales] + [("12 m", c.doce_meses)]
    minimo, maximo = 30.0, 65.0
    arriba, abajo = 90.0, 560.0
    izquierda = 70.0
    paso = (ANCHO - izquierda - 170) / (len(puntos) - 2)

    def py(valor: float) -> float:
        return abajo - (abajo - arriba) * (valor - minimo) / (maximo - minimo)

    piezas: list[str] = []
    _subtitulo(piezas, "Índice de siniestralidad directa del sistema, 12 meses, en %")
    for marca in range(30, 66, 10):
        piezas.append(linea(izquierda - 20, py(marca), ANCHO, py(marca), GRIS_CONTEXTO, "1"))
        piezas.append(texto(0, py(marca) + 8, str(marca), TAM_EJE, GRIS))
    coordenadas = [(izquierda + i * paso, py(v)) for i, (_, v) in enumerate(puntos[:-1])]
    coordenadas.append((ANCHO - 24, py(puntos[-1][1])))
    for (x1, y1), (x2, y2) in zip(coordenadas[:-2], coordenadas[1:-1], strict=True):
        piezas.append(_trazo(x1, y1, x2, y2, MARINO))
    (x1, y1), (x2, y2) = coordenadas[-2], coordenadas[-1]
    piezas.append(
        f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{GRIS}" '
        f'stroke-width="3" stroke-dasharray="8 8"/>'
    )
    for i, ((etiqueta, valor), (x, y)) in enumerate(zip(puntos, coordenadas, strict=True)):
        ultimo = i == len(puntos) - 1
        color = AZUL if ultimo else MARINO
        piezas.append(_circulo(x, y, 10 if ultimo else 8, color))
        posicion = POSICION_ETIQUETA.get(etiqueta, "arriba")
        if posicion == "abajo":
            piezas.append(texto(x, y + 42, numero(valor), TAM_TEXTO, color, 600, "middle"))
        elif posicion == "derecha":
            piezas.append(texto(x + 16, y - 14, numero(valor), TAM_TEXTO, color, 600))
        else:
            piezas.append(texto(x, y - 22, numero(valor), TAM_TEXTO, color, 600, "middle"))
        if ultimo:
            piezas.append(texto(ANCHO, abajo + 36, "12 meses", TAM_EJE, AZUL, 600, "end"))
            piezas.append(texto(ANCHO, abajo + 62, "a ago. 2026", TAM_EJE, AZUL, 600, "end"))
        else:
            piezas.append(texto(x, abajo + 36, etiqueta, TAM_EJE, GRIS, 400, "middle"))
    i_2021 = next(i for i, (e, _) in enumerate(puntos) if e == "2021")
    x21, y21 = coordenadas[i_2021]
    piezas.append(texto(x21 + 22, y21 + 8, "Pandemia de COVID-19", TAM_EJE, GRIS))
    descripcion = (
        "Índice directo del sistema en períodos de 12 meses: "
        + "; ".join(f"{e} {porcentaje(v)}" for e, v in puntos[:-1])
        + f"; 12 meses a agosto de 2026, {porcentaje(c.doce_meses)}."
    )
    return _documento(piezas, "Índice directo del sistema en períodos de 12 meses", descripcion)


FIGURAS = {
    "figura_1_contribucion.svg": figura_contribucion,
    "figura_2_con_sin.svg": figura_con_sin,
    "figura_3_vida_mensual.svg": figura_vida_mensual,
    "figura_4_incendio.svg": figura_incendio,
    "figura_5_serie_12_meses.svg": figura_serie_12_meses,
}
