"""Paquete 4.2 de PF-01: serie del índice de siniestralidad del sistema (issue #11).

Uso (desde la raíz del repositorio):
    uv run python scripts/figura_serie.py --tabla          # tabla Markdown del informe
    uv run python scripts/figura_serie.py --salida tmp/PF-01_serie.svg

Lee data/processed/indicadores_riesgo.csv y escribe la figura SVG con la marca JC.
(src/pf_01_siniestralidad_sbs/serie_sistema.py). No reemplaza un archivo existente sin
--sobrescribir: reports/figures/PF-01_serie.svg puede llevar un manifiesto de procedencia
(Content Credentials) que se pierde si se genera encima. La prueba
tests/test_figura_serie.py comprueba que la figura publicada coincide con la que produce
este script y que su serie cuadra con reports/validacion_resultados.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pf_01_siniestralidad_sbs import serie_sistema as ss
from pf_01_siniestralidad_sbs.tabla_tiempos import escribir

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parents[1]
CSV = RAIZ / "data" / "processed" / "indicadores_riesgo.csv"
SVG = RAIZ / "reports" / "figures" / "PF-01_serie.svg"


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada; devuelve 0 si escribió todo lo pedido y 1 si no."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--csv", type=Path, default=CSV, help="indicadores por riesgo y corte")
    parser.add_argument("--salida", type=Path, default=SVG, help="figura SVG")
    parser.add_argument("--tabla", action="store_true", help="solo imprime la tabla Markdown")
    parser.add_argument(
        "--sobrescribir", action="store_true", help="reemplaza los archivos que ya existen"
    )
    args = parser.parse_args(argv)

    serie = ss.leer_serie(args.csv)
    if args.tabla:
        print(ss.tabla_markdown(serie))
        return 0

    if escribir(args.salida, ss.construir_svg(serie), args.sobrescribir):
        print(f"Escrito: {args.salida}")
        return 0
    print(f"Ya existe, no se reemplaza (use --sobrescribir): {args.salida}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
