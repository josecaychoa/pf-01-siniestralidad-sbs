"""Paquete 2.1 de PF-01: descarga los archivos de la SBS y los lleva a formato largo.

Uso (desde la raíz del repositorio):
    uv run python scripts/descargar_sbs.py                  # descarga y extracción
    uv run python scripts/descargar_sbs.py --sin-extraccion # solo descarga y manifiesto
    uv run python scripts/descargar_sbs.py --sin-descarga   # solo extracción (data/raw completo)

Entradas y salidas:
    data/raw/                 archivos originales (inmutables, fuera de Git)
    data/raw/manifest.csv     URL, fecha de descarga, Last-Modified, bytes y SHA-256 (en Git)
    data/interim/*.csv        estados_financieros, indicadores y riesgos en formato largo
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pf_01_siniestralidad_sbs.descarga import ArchivoReemplazadoError, DescargaError, descargar
from pf_01_siniestralidad_sbs.extraccion import EstructuraError, extraer
from pf_01_siniestralidad_sbs.fuentes import catalogo

RAIZ = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada; devuelve 0 si todo terminó bien."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sin-descarga", action="store_true", help="omitir la descarga")
    parser.add_argument("--sin-extraccion", action="store_true", help="omitir la extracción")
    parser.add_argument("--pausa", type=float, default=2.0, help="segundos entre descargas")
    args = parser.parse_args(argv)

    dir_raw = RAIZ / "data" / "raw"
    dir_interim = RAIZ / "data" / "interim"
    try:
        if not args.sin_descarga:
            print("Descarga (SBS, intranet2.sbs.gob.pe):")
            registros = descargar(catalogo(), dir_raw, pausa=args.pausa)
            print(f"  manifiesto: {len(registros)} archivos en data/raw/manifest.csv")
        if not args.sin_extraccion:
            print("Extracción a formato largo:")
            conteo = extraer(dir_raw, dir_interim)
            for nombre, filas in conteo.items():
                print(f"  data/interim/{nombre}: {filas:,} filas".replace(",", " "))
    except (DescargaError, ArchivoReemplazadoError, EstructuraError, FileNotFoundError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
