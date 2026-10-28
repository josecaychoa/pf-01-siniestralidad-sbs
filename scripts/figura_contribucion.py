"""Paquete 4.4 de PF-01: contribución por riesgo y quiebre contable (CC-PF-01-02, #56).

Uso (desde la raíz del repositorio):
    uv run python scripts/figura_contribucion.py --tabla     # tabla Markdown del informe
    uv run python scripts/figura_contribucion.py             # escribe las dos figuras
    uv run python scripts/figura_contribucion.py --sobrescribir

Lee data/processed/indicadores_riesgo.csv (cortes de agosto de 2025 y de 2026) y
data/processed/serie_mensual_riesgos.csv, y escribe con la marca JC.:
    reports/figures/PF-01_contribucion.svg   aporte de cada riesgo al cambio del índice
    reports/figures/PF-01_quiebre_vida.svg   siniestros mensuales de Vida Individual de
                                             Largo Plazo, enero de 2025 a agosto de 2026
No reemplaza archivos existentes sin --sobrescribir (manifiesto de procedencia). La prueba
tests/test_contribucion.py comprueba que las figuras publicadas coinciden con las generadas.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from pf_01_siniestralidad_sbs import contribucion as co
from pf_01_siniestralidad_sbs.serie_mensual import leer_csv
from pf_01_siniestralidad_sbs.tabla_tiempos import escribir

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parents[1]
INDICADORES = RAIZ / "data" / "processed" / "indicadores_riesgo.csv"
MENSUAL = RAIZ / "data" / "processed" / "serie_mensual_riesgos.csv"
FIGURAS = RAIZ / "reports" / "figures"
INICIO, FIN = date(2025, 8, 31), date(2026, 8, 31)


def meses_vida(ruta: Path) -> list[co.Mes]:
    """Serie mensual de Vida Individual de Largo Plazo para la figura del quiebre."""
    tabla = leer_csv(ruta)
    vida = tabla[tabla["riesgo_comparable"] == co.VIDA_LARGO_PLAZO]
    return [
        co.Mes(f.fecha_corte, f.siniestros_netos_mes, f.cuadro_siniestros)
        for f in vida.itertuples()
    ]


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada; devuelve 0 si escribió todo lo pedido y 1 si no."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tabla", action="store_true", help="solo imprime la tabla Markdown")
    parser.add_argument(
        "--sobrescribir", action="store_true", help="reemplaza los archivos que ya existen"
    )
    args = parser.parse_args(argv)

    cortes = co.leer_cortes(INDICADORES)
    directa = co.descomponer(cortes, INICIO, FIN, "directa")
    retenida = co.descomponer(cortes, INICIO, FIN, "retenida")
    if args.tabla:
        print(co.tabla_markdown(directa, retenida))
        return 0

    salidas = {
        FIGURAS / "PF-01_contribucion.svg": co.construir_svg_contribucion(directa),
        FIGURAS / "PF-01_quiebre_vida.svg": co.construir_svg_mensual(meses_vida(MENSUAL)),
    }
    codigo = 0
    for ruta, svg in salidas.items():
        if escribir(ruta, svg, args.sobrescribir):
            print(f"Escrito: {ruta}")
        else:
            print(f"Ya existe, no se reemplaza (use --sobrescribir): {ruta}")
            codigo = 1
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
