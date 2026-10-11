"""Paquete 2.2 de PF-01: valida data/interim y escribe reports/validacion_datos.md.

Uso (desde la raíz del repositorio, después de scripts/descargar_sbs.py):
    uv run python scripts/validar_datos.py

Devuelve 1 si algún control falla. Las diferencias de la fuente documentadas en
src/pf_01_siniestralidad_sbs/catalogos/excepciones.csv se informan aparte y no fallan.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from pf_01_siniestralidad_sbs import validacion as v

RAIZ = Path(__file__).resolve().parents[1]


def miles(n: float) -> str:
    """Entero con separador de millares de espacio (RAE)."""
    return f"{n:,.0f}".replace(",", " ")


def tabla_md(df: pd.DataFrame) -> str:
    """Tabla Markdown sin dependencias adicionales."""
    columnas = [str(c) for c in df.columns]
    lineas = ["| " + " | ".join(columnas) + " |", "|" + "---|" * len(columnas)]
    for fila in df.itertuples(index=False):
        celdas = [f"{x:,.3f}".replace(",", " ") if isinstance(x, float) else str(x) for x in fila]
        lineas.append("| " + " | ".join(celdas) + " |")
    return "\n".join(lineas)


def ejecutar() -> list[v.Resultado]:
    """Ejecuta todos los controles sobre data/interim y data/raw."""
    tablas = v.leer_interim(RAIZ / "data" / "interim")
    cortes = v.leer_catalogo("cortes")
    return [
        v.validar_estructura(tablas, cortes),
        v.cuadre_totales(pd.concat(tablas.values(), ignore_index=True)),
        v.jerarquia_riesgos(tablas["riesgos"]),
        v.balance(tablas["estados_financieros"]),
        v.monedas(tablas["estados_financieros"]),
        v.consistencia_cuadros(tablas["riesgos"]),
        v.cifras_acumuladas(tablas, cortes),
        v.plan_de_cuentas(v.leer_notas_plan(RAIZ / "data" / "raw"), cortes),
    ]


def informe(resultados: list[v.Resultado]) -> str:
    """Informe en Markdown con el resumen y el detalle de fallas y excepciones."""
    ahora = datetime.now(ZoneInfo("America/Lima")).strftime("%Y-%m-%d")
    filas = [
        f"| {r.control} | {miles(r.revisados)} | {r.fallas} | {r.excepciones} | "
        f"{'Conforme' if r.ok else 'Con fallas'} |"
        for r in resultados
    ]
    partes = [
        "# Validación de datos · PF-01 · Paquete 2.2",
        "",
        f"`Portafolio · PF-01` · Generado con `scripts/validar_datos.py` el {ahora} "
        "· Tolerancia: 1 mil soles",
        "",
        "| Control | Revisados | Fallas | Excepciones de la fuente | Resultado |",
        "|---|---|---|---|---|",
        *filas,
        "",
        "*Nota.* Elaboración propia con datos de SBS (s. f.-a, s. f.-b, s. f.-c, s. f.-d). "
        "«Revisados» cuenta filas, celdas o combinaciones según el control. Las excepciones "
        "son diferencias de la propia fuente, documentadas en "
        "`src/pf_01_siniestralidad_sbs/catalogos/excepciones.csv`.",
    ]
    acumuladas = next(r for r in resultados if r.control == "Cifras acumuladas en el año")
    partes += [
        "",
        "## Cifras acumuladas en el año",
        "",
        "| Serie | Agosto de 2025 | Diciembre de 2025 | Razón | Esperada (12 / 8) |",
        "|---|---|---|---|---|",
        *[
            f"| {f.serie} | {miles(f.agosto_2025)} | {miles(f.diciembre_2025)} | "
            f"{f.razon:.3f} | {f.razon_esperada:.3f} |"
            for f in acumuladas.detalle.itertuples()
        ],
        "",
        "*Nota.* En miles de soles. Elaboración propia con datos de SBS (s. f.-a).",
    ]
    for r in resultados:
        if r.fallas or r.excepciones:
            partes += ["", f"## Detalle: {r.control}", "", tabla_md(r.detalle.head(50))]
    partes += [
        "",
        "## Referencias",
        "",
        "Superintendencia de Banca, Seguros y AFP. (s. f.-a). *Boletín mensual* [Conjunto de "
        "datos]. Recuperado el 11 de octubre de 2026, de "
        "https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-367",
        "",
        "Superintendencia de Banca, Seguros y AFP. (s. f.-b). *Índice de siniestralidad directa "
        "y retenida según riesgos* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de "
        "https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-403",
        "",
        "Superintendencia de Banca, Seguros y AFP. (s. f.-c). *Primas de seguros netas, cedidas "
        "y retenidas según riesgos* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de "
        "https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-401",
        "",
        "Superintendencia de Banca, Seguros y AFP. (s. f.-d). *Siniestros de primas de seguros "
        "netas, cedidas y retenidas según riesgos* [Conjunto de datos]. Recuperado el 11 de "
        "octubre de 2026, de "
        "https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-402",
        "",
    ]
    return "\n".join(partes)


def main() -> int:
    """Punto de entrada; devuelve 0 si todos los controles están conformes."""
    resultados = ejecutar()
    destino = RAIZ / "reports" / "validacion_datos.md"
    destino.write_text(informe(resultados), encoding="utf-8", newline="\n")
    for r in resultados:
        estado = "ok   " if r.ok else "FALLA"
        print(
            f"  {estado} {r.control}: {miles(r.revisados)} revisados, {r.fallas} fallas, "
            f"{r.excepciones} excepciones"
        )
    print(f"Informe: {destino.relative_to(RAIZ)}")
    return 0 if all(r.ok for r in resultados) else 1


if __name__ == "__main__":
    sys.exit(main())
