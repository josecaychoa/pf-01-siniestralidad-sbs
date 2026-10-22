"""Paquete 3.4 de PF-01: tabla de tiempos AS-IS frente a TO-BE (issue #25, D-PF01-19).

Uso (desde la raíz del repositorio):
    uv run python scripts/figura_tiempos.py --tabla          # tabla Markdown del README
    uv run python scripts/figura_tiempos.py --salida tmp/PF-01_tiempos.svg
    uv run python scripts/figura_tiempos.py --salida tmp/PF-01_tiempos.svg --html tmp/t.html

Lee docs/procesos/PF-01_tiempos.csv y escribe la figura SVG con la marca JC.
(src/pf_01_siniestralidad_sbs/tabla_tiempos.py). No reemplaza un archivo existente sin
--sobrescribir: docs/procesos/PF-01_tiempos.svg lleva un manifiesto de procedencia (Content
Credentials) que se pierde si se genera encima. La prueba tests/test_tabla_tiempos.py
comprueba que la figura publicada coincide con la que produce este script.

El PDF publicado se imprimió desde la página de --html con Microsoft Edge 155 sin interfaz
(--headless y --print-to-pdf) y después se le quitaron las propiedades del documento.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pf_01_siniestralidad_sbs import tabla_tiempos as tt

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parents[1]
CSV = RAIZ / "docs" / "procesos" / "PF-01_tiempos.csv"
SVG = RAIZ / "docs" / "procesos" / "PF-01_tiempos.svg"


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada; devuelve 0 si escribió todo lo pedido y 1 si no."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--csv", type=Path, default=CSV, help="tiempos por tarea")
    parser.add_argument("--salida", type=Path, default=SVG, help="figura SVG")
    parser.add_argument("--html", type=Path, help="página para imprimir el PDF (opcional)")
    parser.add_argument("--tabla", action="store_true", help="solo imprime la tabla Markdown")
    parser.add_argument(
        "--sobrescribir", action="store_true", help="reemplaza los archivos que ya existen"
    )
    args = parser.parse_args(argv)

    totales = tt.leer_totales(args.csv)
    if args.tabla:
        print(tt.tabla_markdown(totales))
        return 0

    svg = tt.construir_svg(totales)
    destinos = [(args.salida, svg)]
    if args.html:
        destinos.append((args.html, tt.pagina_impresion(svg)))
    codigo = 0
    for ruta, contenido in destinos:
        if tt.escribir(ruta, contenido, args.sobrescribir):
            print(f"Escrito: {ruta}")
        else:
            print(f"Ya existe, no se reemplaza (use --sobrescribir): {ruta}")
            codigo = 1
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
