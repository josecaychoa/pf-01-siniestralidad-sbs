"""Paquete 5.2 de PF-01: figuras del documento PDF de LinkedIn (#15).

Uso (desde la raíz del repositorio):
    uv run python scripts/figuras_linkedin.py                 # escribe las cinco figuras
    uv run python scripts/figuras_linkedin.py --sobrescribir

Lee data/processed/indicadores_riesgo.csv y data/processed/serie_mensual_riesgos.csv y
escribe linkedin/figuras/figura_N_*.svg, del tamaño de la tarjeta de la página 4:5
(856 × 650 px). No reemplaza archivos existentes sin --sobrescribir. La prueba
tests/test_pieza_linkedin.py comprueba que las figuras publicadas coinciden con las generadas.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pf_01_siniestralidad_sbs import pieza_linkedin as pl
from pf_01_siniestralidad_sbs.tabla_tiempos import escribir

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parents[1]
INDICADORES = RAIZ / "data" / "processed" / "indicadores_riesgo.csv"
MENSUAL = RAIZ / "data" / "processed" / "serie_mensual_riesgos.csv"
SALIDA = RAIZ / "linkedin" / "figuras"


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada; devuelve 0 si escribió todo lo pedido y 1 si no."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--sobrescribir", action="store_true", help="reemplaza los archivos que ya existen"
    )
    args = parser.parse_args(argv)
    cifras = pl.calcular(INDICADORES, MENSUAL)
    SALIDA.mkdir(parents=True, exist_ok=True)
    codigo = 0
    for nombre, construir in pl.FIGURAS.items():
        ruta = SALIDA / nombre
        if escribir(ruta, construir(cifras), args.sobrescribir):
            print(f"Escrito: {ruta}")
        else:
            print(f"Ya existe, no se reemplaza (use --sobrescribir): {ruta}")
            codigo = 1
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
