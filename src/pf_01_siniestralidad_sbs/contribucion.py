"""Contribución de cada riesgo al cambio de la siniestralidad del sistema (paquete 4.4, #56).

El índice del sistema es la suma de los siniestros de los 48 riesgos entre la suma de sus
primas. Entre dos cortes, el cambio del índice se reparte sin residuo entre los riesgos:

    contribución del riesgo i = S_i,fin / P_fin − S_i,inicio / P_inicio   (en p. p.)

donde S son los siniestros del riesgo y P, las primas del sistema en cada corte. La suma de las
contribuciones es exactamente el cambio del índice del sistema (prueba en
``tests/test_contribucion.py``). Lee ``data/processed/indicadores_riesgo.csv`` (D-PF01-23) y,
para la figura del quiebre, ``data/processed/serie_mensual_riesgos.csv`` (CC-PF-01-02).

Las figuras siguen la identidad visual de la marca JC. v2.3 igual que ``serie_sistema.py``:
titular en dos tonos que afirma el hallazgo, hallazgo en Azul y contexto en Gris de contexto,
etiquetas directas, nota APA 7 y cajetín «JC.». Solo usa la biblioteca estándar para el SVG.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import NamedTuple
from xml.sax.saxutils import escape

from pf_01_siniestralidad_sbs.serie_sistema import MESES_CORTOS, mes_largo
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
    rectangulo,
    texto,
)

ANCHO, MARGEN = 1200, 56
FECHA_FIGURA = "2026-10-27"
VIDA_LARGO_PLAZO = "Vida Individual de Largo Plazo"
INCENDIO = "Incendio"
HALLAZGOS = (VIDA_LARGO_PLAZO, INCENDIO)
NORMA = "Resolución SBS N.º 00085-2026"
MES_NORMA = date(2026, 3, 31)  # la norma rige desde la información de marzo de 2026
TITULO_CONTRIBUCION = (
    "PF-01 · Contribución de cada riesgo al cambio de la siniestralidad directa del sistema, "
    "agosto de 2025 a agosto de 2026"
)
TITULO_MENSUAL = (
    "PF-01 · Siniestros mensuales de Vida Individual de Largo Plazo, enero de 2025 a agosto de 2026"
)
NOTA_CONTRIBUCION = (
    "Nota. Elaboración propia con datos de SBS (s. f.-a, s. f.-c, s. f.-d). Contribución de "
    "cada riesgo = sus siniestros entre las primas del sistema en agosto de 2026 menos lo mismo "
    "en agosto de 2025; las contribuciones suman el cambio del índice del sistema. Cortes de 8 "
    "meses acumulados. Desde marzo de 2026, los siniestros incluyen «otras obligaciones» por la "
    "Resolución SBS N.º 00085-2026 (SBS, 2026)."
)
NOTA_MENSUAL = (
    "Nota. Elaboración propia con datos de SBS (s. f.-c, s. f.-d, 2026). Siniestros del "
    "mes = acumulado del mes menos el del mes anterior del mismo año, en millones de soles. "
    "Desde marzo de 2026 el cuadro S-402 se titula «Siniestros de Primas de Seguros y Otras "
    "Obligaciones Netos» y su nota 1/ remite a la Resolución SBS N.º 085-2026."
)


class Riesgo(NamedTuple):
    """Primas y siniestros de un riesgo en un corte (miles de soles)."""

    riesgo: str
    ramo: str
    primas_netas: float
    primas_retenidas: float
    siniestros_netos: float
    siniestros_retenidos: float


class Contribucion(NamedTuple):
    """Aporte de un riesgo al cambio del índice del sistema entre dos cortes."""

    riesgo: str
    ramo: str
    indice_inicio: float  # índice propio del riesgo, en porcentaje
    indice_fin: float
    contribucion: float  # puntos porcentuales del índice del sistema


class Descomposicion(NamedTuple):
    """Índice del sistema en dos cortes y aporte de cada riesgo a su cambio."""

    inicio: date
    fin: date
    medida: str  # «directa» o «retenida»
    indice_inicio: float
    indice_fin: float
    contribuciones: list[Contribucion]  # de mayor a menor contribución

    @property
    def cambio(self) -> float:
        return self.indice_fin - self.indice_inicio

    def de(self, riesgo: str) -> Contribucion:
        return next(c for c in self.contribuciones if c.riesgo == riesgo)


def leer_cortes(ruta: Path) -> dict[date, list[Riesgo]]:
    """Riesgos de cada corte de ``indicadores_riesgo.csv`` (una fila por riesgo comparable)."""
    cortes: dict[date, list[Riesgo]] = {}
    with ruta.open(encoding="utf-8", newline="") as archivo:
        for fila in csv.DictReader(archivo):
            corte = date.fromisoformat(fila["fecha_corte"])
            cortes.setdefault(corte, []).append(
                Riesgo(
                    fila["riesgo_comparable"],
                    fila["ramo"],
                    float(fila["primas_netas"]),
                    float(fila["primas_retenidas"]),
                    float(fila["siniestros_netos"]),
                    float(fila["siniestros_retenidos"]),
                )
            )
    return cortes


def _montos(riesgo: Riesgo, medida: str) -> tuple[float, float]:
    """Siniestros y primas de la medida pedida."""
    if medida == "directa":
        return riesgo.siniestros_netos, riesgo.primas_netas
    if medida == "retenida":
        return riesgo.siniestros_retenidos, riesgo.primas_retenidas
    raise ValueError(f"medida desconocida: {medida}")


def indice(riesgos: list[Riesgo], medida: str = "directa", excluir: tuple[str, ...] = ()) -> float:
    """Índice agregado (%) de los riesgos, sin los de `excluir`."""
    pares = [_montos(r, medida) for r in riesgos if r.riesgo not in excluir]
    return 100 * sum(s for s, _ in pares) / sum(p for _, p in pares)


def descomponer(
    cortes: dict[date, list[Riesgo]], inicio: date, fin: date, medida: str = "directa"
) -> Descomposicion:
    """Contribución de cada riesgo al cambio del índice del sistema entre `inicio` y `fin`."""
    primas_inicio = sum(_montos(r, medida)[1] for r in cortes[inicio])
    primas_fin = sum(_montos(r, medida)[1] for r in cortes[fin])
    previos = {r.riesgo: r for r in cortes[inicio]}
    nombres = [r.riesgo for r in cortes[fin]] + [
        n for n in previos if n not in {r.riesgo for r in cortes[fin]}
    ]
    actuales = {r.riesgo: r for r in cortes[fin]}
    lista: list[Contribucion] = []
    for nombre in nombres:
        antes, despues = previos.get(nombre), actuales.get(nombre)
        s0, p0 = _montos(antes, medida) if antes else (0.0, 0.0)
        s1, p1 = _montos(despues, medida) if despues else (0.0, 0.0)
        lista.append(
            Contribucion(
                nombre,
                (despues or antes).ramo,
                100 * s0 / p0 if p0 else float("nan"),
                100 * s1 / p1 if p1 else float("nan"),
                100 * (s1 / primas_fin - s0 / primas_inicio),
            )
        )
    lista.sort(key=lambda c: c.contribucion, reverse=True)
    return Descomposicion(
        inicio, fin, medida, indice(cortes[inicio], medida), indice(cortes[fin], medida), lista
    )


def principales(d: Descomposicion, positivos: int = 4, negativos: int = 2) -> list[Contribucion]:
    """Mayores aportes al alza y a la baja; el resto se agrupa en una fila."""
    altas = d.contribuciones[:positivos]
    bajas = sorted(d.contribuciones, key=lambda c: c.contribucion)[:negativos]
    elegidos = {c.riesgo for c in altas + bajas}
    resto = [c for c in d.contribuciones if c.riesgo not in elegidos]
    fila_resto = Contribucion(
        f"Resto ({len(resto)} riesgos)",
        "",
        float("nan"),
        float("nan"),
        sum(c.contribucion for c in resto),
    )
    return altas + [fila_resto] + sorted(bajas, key=lambda c: c.contribucion, reverse=True)


def tabla_markdown(directa: Descomposicion, retenida: Descomposicion) -> str:
    """Tabla del informe: índices propios y contribución a la directa y a la retenida."""
    inicio, fin = mes_largo(directa.inicio), mes_largo(directa.fin)
    lineas = [
        f"| Riesgo | Directa, {inicio} (%) | Directa, {fin} (%) | Contribución a la directa "
        "(p. p.) | Contribución a la retenida (p. p.) |",
        "|---|---:|---:|---:|---:|",
    ]
    retenidas = {c.riesgo: c.contribucion for c in retenida.contribuciones}
    for c in principales(directa):
        if c.riesgo.startswith("Resto"):
            elegidos = {x.riesgo for x in principales(directa) if not x.riesgo.startswith("Resto")}
            aporte_retenida = sum(v for k, v in retenidas.items() if k not in elegidos)
            celdas = [c.riesgo, "", "", _signo(c.contribucion), _signo(aporte_retenida)]
        else:
            celdas = [
                c.riesgo,
                _numero(c.indice_inicio),
                _numero(c.indice_fin),
                _signo(c.contribucion),
                _signo(retenidas[c.riesgo]),
            ]
        lineas.append("| " + " | ".join(celdas) + " |")
    lineas.append(
        "| **Sistema** | **"
        + numero(directa.indice_inicio)
        + "** | **"
        + numero(directa.indice_fin)
        + "** | **"
        + _signo(directa.cambio)
        + "** | **"
        + _signo(retenida.cambio)
        + "** |"
    )
    return "\n".join(lineas)


def _numero(valor: float) -> str:
    """Número con un decimal y el signo menos tipográfico (RAE) si es negativo."""
    return ("−" if valor < 0 else "") + numero(abs(valor))


def _signo(valor: float, decimales: int = 2) -> str:
    """Número con signo explícito («+5.12», «−0.83»), con el signo menos tipográfico."""
    texto_numero = numero(abs(valor), decimales)
    return ("+" if valor >= 0 else "−") + texto_numero


# --------------------------------------------------------------------------------------
# Figuras
# --------------------------------------------------------------------------------------


def _nota_y_cajetin(piezas: list[str], y: float, nota: str, etiqueta: str) -> float:
    """Nota APA 7 («Nota.» en cursiva) y cajetín «JC.»; devuelve el alto total de la figura."""
    for j, renglon in enumerate(partir(nota, 158)):
        if j == 0 and renglon.startswith("Nota."):
            contenido = f'<tspan font-style="italic">Nota.</tspan>{escape(renglon[5:])}'
        else:
            contenido = escape(renglon)
        piezas.append(texto(MARGEN, y, contenido, 13, GRIS))
        y += 20
    y += 24
    piezas.append(linea(MARGEN, y, ANCHO - MARGEN, y, GRIS, "1"))
    y += 46
    marca = f'JC<tspan fill="{AZUL}">.</tspan>'
    piezas.append(texto(MARGEN + 4, y, marca, 32, GRAFITO, 700, extra=' letter-spacing="-1.6"'))
    piezas.append(texto(MARGEN + 70, y - 14, escape(etiqueta), 14, GRAFITO, 700))
    piezas.append(texto(MARGEN + 70, y + 4, FECHA_FIGURA, 12, GRIS))
    repositorio = "github.com/josecaychoa/pf-01-siniestralidad-sbs"
    piezas.append(texto(ANCHO - MARGEN, y - 4, repositorio, 12, GRIS, 400, "end"))
    return y + 34


def _envolver(piezas: list[str], alto: float, titulo: str, descripcion: str) -> str:
    """Documento SVG con título y descripción accesibles."""
    cabecera = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ANCHO}" height="{alto:g}" '
        f'viewBox="0 0 {ANCHO} {alto:g}" font-family="{FUENTE}" role="img" '
        f'aria-labelledby="t d">'
    )
    return "\n".join(
        [
            cabecera,
            f'<title id="t">{escape(titulo)}</title>',
            f'<desc id="d">{escape(descripcion)}</desc>',
            f'<rect width="{ANCHO}" height="{alto:g}" fill="{BLANCO}"/>',
            *piezas,
            "</svg>",
            "",
        ]
    )


def _titular(piezas: list[str], idea: str, continuacion: str, bajada: str) -> float:
    """Titular en dos tonos (Grafito y Gris) y bajada; devuelve la ordenada siguiente."""
    extra = ' letter-spacing="-0.4"'
    piezas.append(texto(MARGEN, 64, escape(idea), 28, GRAFITO, 600, extra=extra))
    piezas.append(texto(MARGEN, 102, escape(continuacion), 28, GRIS, 600, extra=extra))
    piezas.append(texto(MARGEN, 138, escape(bajada), 15, GRIS))
    return 138


def construir_svg_contribucion(d: Descomposicion) -> str:
    """Barras horizontales: aporte de cada riesgo al cambio del índice directo del sistema."""
    vida, incendio = d.de(VIDA_LARGO_PLAZO), d.de(INCENDIO)
    piezas: list[str] = []
    y = _titular(
        piezas,
        f"Dos riesgos explican el alza de {numero(d.cambio)} puntos de la siniestralidad.",
        f"Vida Individual de Largo Plazo aporta {numero(vida.contribucion)} tras un cambio "
        f"contable; Incendio, {numero(incendio.contribucion)}.",
        f"Contribución al cambio del índice directo del sistema, {mes_largo(d.inicio)} a "
        f"{mes_largo(d.fin)}, en puntos porcentuales.",
    )
    filas = principales(d)
    x_etiqueta = MARGEN + 330  # las etiquetas de riesgo terminan aquí
    cero = x_etiqueta + 220
    escala = (ANCHO - MARGEN - 150 - cero) / max(
        abs(d.cambio), *(abs(c.contribucion) for c in filas)
    )
    alto_barra, paso = 30, 50
    arriba = y + 40
    piezas.append(linea(cero, arriba - 12, cero, arriba + paso * (len(filas) + 1), GRIS, "1"))
    for i, c in enumerate([*filas, None]):
        fila_y = arriba + i * paso
        if c is None:  # barra del sistema
            valor, nombre, color, peso = d.cambio, "Sistema (48 riesgos)", GRAFITO, 700
        else:
            valor, nombre = c.contribucion, c.riesgo
            color = AZUL if c.riesgo in HALLAZGOS else GRIS_CONTEXTO
            peso = 600 if c.riesgo in HALLAZGOS else 400
        ancho = abs(valor) * escala
        x = cero if valor >= 0 else cero - ancho
        piezas.append(rectangulo(round(x, 1), fila_y, round(ancho, 1), alto_barra, color))
        piezas.append(texto(x_etiqueta, fila_y + 21, escape(nombre), 15, GRAFITO, peso, "end"))
        x_valor = x + ancho + 10 if valor >= 0 else x - 10
        ancla = "start" if valor >= 0 else "end"
        tono = AZUL if color == AZUL else GRAFITO
        piezas.append(texto(x_valor, fila_y + 21, _signo(valor), 15, tono, 600, ancla))
    # Anotaciones directas sobre los dos hallazgos
    nota_vida = f"Cambio contable desde marzo de 2026 ({NORMA})"
    nota_incendio = (
        f"Sin quiebre en marzo: siniestros altos en abril, julio y agosto; índice directo de "
        f"{numero(incendio.indice_fin)} %"
    )
    for k, anotacion in ((0, nota_vida), (1, nota_incendio)):
        piezas.append(texto(cero + 8, arriba + k * paso - 6, escape(anotacion), 12, AZUL))
    y = arriba + (len(filas) + 1) * paso + 30
    descripcion = (
        f"El índice directo del sistema subió {numero(d.cambio, 2)} puntos porcentuales: Vida "
        f"Individual de Largo Plazo aporta {numero(vida.contribucion, 2)} e Incendio "
        f"{numero(incendio.contribucion, 2)}; el resto de riesgos suma "
        f"{_signo(d.cambio - vida.contribucion - incendio.contribucion)}."
    )
    alto = _nota_y_cajetin(
        piezas, y, NOTA_CONTRIBUCION, "Portafolio · PF-01 · Qué explica el alza de 2026"
    )
    return _envolver(piezas, alto, TITULO_CONTRIBUCION, descripcion)


class Mes(NamedTuple):
    """Siniestros netos de un riesgo en un mes (miles de soles) y título del cuadro."""

    fecha: date
    siniestros_mes: float
    cuadro: str


def construir_svg_mensual(meses: list[Mes]) -> str:
    """Barras mensuales de los siniestros de Vida Individual de Largo Plazo con el quiebre."""
    antes = [m.siniestros_mes for m in meses if m.fecha < MES_NORMA]
    despues = [m.siniestros_mes for m in meses if m.fecha > MES_NORMA]
    quiebre = next(m for m in meses if m.fecha == MES_NORMA)
    promedio_antes, promedio_despues = sum(antes) / len(antes), sum(despues) / len(despues)
    piezas: list[str] = []
    y = _titular(
        piezas,
        "Los siniestros de Vida Individual de Largo Plazo saltaron en marzo de 2026.",
        "Ese mes, la SBS empezó a incluir «otras obligaciones» por un cambio contable.",
        "Siniestros netos del mes, en millones de soles. Promedio de "
        f"{numero(promedio_antes / 1000)} antes de marzo de 2026 y de "
        f"{numero(promedio_despues / 1000)} de abril a agosto.",
    )
    x0, x1 = MARGEN + 56, ANCHO - MARGEN
    alto_grafico = 300
    arriba = y + 40
    abajo = arriba + alto_grafico
    vmax = 350_000.0
    paso = (x1 - x0) / len(meses)
    ancho = paso * 0.64

    def py(valor: float) -> float:
        return abajo - max(valor, 0.0) / vmax * alto_grafico

    for marca in range(0, 351, 100):
        piezas.append(linea(x0, py(marca * 1000), x1, py(marca * 1000), GRIS_CONTEXTO, "0.6"))
        piezas.append(texto(x0 - 10, py(marca * 1000) + 4, f"{marca}", 12, GRIS, ancla="end"))
    for i, m in enumerate(meses):
        x = x0 + i * paso + (paso - ancho) / 2
        color = AZUL if m.fecha >= MES_NORMA else GRIS_CONTEXTO
        piezas.append(
            rectangulo(
                round(x, 1),
                round(py(m.siniestros_mes), 1),
                round(ancho, 1),
                round(abajo - py(m.siniestros_mes), 1),
                color,
            )
        )
        etiqueta = MESES_CORTOS[m.fecha.month - 1]
        piezas.append(
            texto(round(x + ancho / 2, 1), abajo + 20, etiqueta, 12, GRIS, ancla="middle")
        )
        if m.fecha.month == 1:
            piezas.append(
                texto(
                    round(x + ancho / 2, 1),
                    abajo + 38,
                    str(m.fecha.year),
                    12,
                    GRAFITO,
                    600,
                    "middle",
                )
            )
    piezas.append(linea(x0, abajo, x1, abajo, GRIS, "1"))
    # Anotación del quiebre sobre la barra de marzo de 2026
    i_quiebre = meses.index(quiebre)
    xq = round(x0 + i_quiebre * paso + paso / 2, 1)
    piezas.append(
        texto(
            xq - ancho / 2 - 8,
            py(quiebre.siniestros_mes) + 18,
            f"{numero(quiebre.siniestros_mes / 1000)}",
            14,
            AZUL,
            600,
            "end",
        )
    )
    renglones = [
        f"Desde marzo de 2026: {NORMA}.",
        "El cuadro S-402 pasa a incluir",
        "«otras obligaciones».",
    ]
    for k, renglon in enumerate(renglones):
        piezas.append(
            texto(
                xq - ancho / 2 - 8,
                py(quiebre.siniestros_mes) + 40 + 18 * k,
                escape(renglon),
                12,
                AZUL,
                400,
                "end",
            )
        )
    y = abajo + 76
    descripcion = (
        f"Siniestros mensuales de Vida Individual de Largo Plazo: promedio de "
        f"{numero(promedio_antes / 1000)} millones de soles de enero de 2025 a febrero de 2026, "
        f"{numero(quiebre.siniestros_mes / 1000)} millones en marzo de 2026 y promedio de "
        f"{numero(promedio_despues / 1000)} millones de abril a agosto de 2026."
    )
    alto = _nota_y_cajetin(
        piezas, y, NOTA_MENSUAL, "Portafolio · PF-01 · Quiebre contable de marzo de 2026"
    )
    return _envolver(piezas, alto, TITULO_MENSUAL, descripcion)
