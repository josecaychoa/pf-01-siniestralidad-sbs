"""Paquete 4.4 de PF-01: serie mensual de primas y siniestros por riesgo (CC-PF-01-02, #56).

Uso (desde la raíz del repositorio):
    uv run python scripts/descargar_mensual.py                  # descarga y serie
    uv run python scripts/descargar_mensual.py --sin-descarga   # solo la serie (archivos ya
                                                                # en data/raw/mensual/)

Entradas y salidas:
    data/raw/mensual/                       40 cuadros S-401 y S-402, enero de 2025 a agosto
                                            de 2026 (inmutables, fuera de Git)
    data/raw/mensual/manifest.csv           URL, fecha de descarga, Last-Modified, bytes y
                                            SHA-256 (en Git)
    data/processed/serie_mensual_riesgos.csv  una fila por mes y riesgo comparable (en Git)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pf_01_siniestralidad_sbs.descarga import ArchivoReemplazadoError, DescargaError, descargar
from pf_01_siniestralidad_sbs.extraccion import EstructuraError
from pf_01_siniestralidad_sbs.fuentes import catalogo_mensual
from pf_01_siniestralidad_sbs.serie_mensual import (
    ConceptoDesconocidoError,
    CuadreError,
    construir_serie,
    escribir_csv,
)

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parents[1]
DIR_MENSUAL = RAIZ / "data" / "raw" / "mensual"
SALIDA = RAIZ / "data" / "processed" / "serie_mensual_riesgos.csv"


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada; devuelve 0 si todo terminó bien."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sin-descarga", action="store_true", help="omitir la descarga")
    parser.add_argument("--pausa", type=float, default=2.0, help="segundos entre descargas")
    args = parser.parse_args(argv)
    try:
        if not args.sin_descarga:
            print("Descarga (SBS, intranet2.sbs.gob.pe):")
            registros = descargar(catalogo_mensual(), DIR_MENSUAL, pausa=args.pausa)
            print(f"  manifiesto: {len(registros)} archivos en data/raw/mensual/manifest.csv")
        tabla = construir_serie(DIR_MENSUAL)
        escribir_csv(tabla, SALIDA)
        meses, riesgos = tabla["fecha_corte"].nunique(), tabla["riesgo_comparable"].nunique()
        print(f"Serie: {len(tabla)} filas ({meses} meses × {riesgos} riesgos) en {SALIDA.name}")
    except (
        DescargaError,
        ArchivoReemplazadoError,
        EstructuraError,
        ConceptoDesconocidoError,
        CuadreError,
        FileNotFoundError,
    ) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
