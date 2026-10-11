"""Pruebas sobre los datos reales en data/interim (se omiten si no se ha ejecutado la descarga).

Ejecutar antes: uv run python scripts/descargar_sbs.py
"""

from pathlib import Path

import pandas as pd
import pytest

INTERIM = Path(__file__).resolve().parents[1] / "data" / "interim"
LLAVE = ["serie", "corte", "hoja", "fila", "columna"]

pytestmark = pytest.mark.skipif(
    not (INTERIM / "riesgos.csv").exists(), reason="sin data/interim: ejecutar la descarga"
)


def leer(nombre: str) -> pd.DataFrame:
    return pd.read_csv(INTERIM / nombre, dtype={"llamadas_concepto": str, "llamadas_empresa": str})


def test_cada_corte_tiene_todas_las_hojas():
    hojas = pd.concat(
        leer(n) for n in ("estados_financieros.csv", "indicadores.csv", "riesgos.csv")
    )
    boletin = hojas[hojas.serie == "S-367"].groupby("corte").hoja.nunique()
    assert len(boletin) == 9
    assert (boletin == 12).all()


def test_sin_celdas_duplicadas():
    for nombre in ("estados_financieros.csv", "indicadores.csv", "riesgos.csv"):
        assert not leer(nombre).duplicated(LLAVE).any(), nombre


def test_boletin_igual_a_cuadros_s401_s403_agosto_2026():
    r = leer("riesgos.csv")
    a = r[r.corte == "2026-08-31"]
    clave = ["hoja", "fila", "columna"]
    boletin = a[a.serie == "S-367"].set_index(clave).valor
    cuadros = a[a.serie != "S-367"].set_index(clave).valor
    comunes = boletin.index.intersection(cuadros.index)
    assert len(comunes) == len(cuadros)
    assert (boletin[comunes] - cuadros[comunes]).abs().max() == 0
