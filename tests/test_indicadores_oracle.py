"""Pruebas cruzadas del módulo indicadores contra las vistas de 04_vistas_analisis.sql.

Solo leen la base. Se omiten si el entorno no tiene ORACLE_USER, ORACLE_PASSWORD y
ORACLE_DSN, como en GitHub Actions. Ejecutar antes la carga: uv run python
scripts/cargar_oracle.py. Cada regla de las decisiones D-PF01-11 a D-PF01-16 debe dar lo
mismo en Python y en SQL.
"""

import os

import oracledb
import pandas as pd
import pytest

from pf_01_siniestralidad_sbs.indicadores import (
    VISTAS_EXPORTADAS,
    clasificar_indice,
    clasificar_matriz,
    corte_siniestralidad,
    exportar_vistas,
    indice_siniestralidad,
    leer_vista,
    resumen_matriz,
    sin_dato,
)

VARIABLES = ("ORACLE_USER", "ORACLE_PASSWORD", "ORACLE_DSN")
CUADRANTES = (
    "cuadrante_interanual_directa",
    "cuadrante_interanual_retenida",
    "cuadrante_tcac_directa",
    "cuadrante_tcac_retenida",
)

pytestmark = pytest.mark.skipif(
    not all(os.environ.get(v) for v in VARIABLES), reason="sin variables de conexión a Oracle"
)


@pytest.fixture(scope="module")
def conexion():
    with oracledb.connect(
        user=os.environ["ORACLE_USER"],
        password=os.environ["ORACLE_PASSWORD"],
        dsn=os.environ["ORACLE_DSN"],
    ) as conexion:
        yield conexion


@pytest.fixture(scope="module")
def matriz(conexion):
    return leer_vista(conexion, "vw_matriz_riesgo")


def test_cuadrantes_iguales_a_la_vista(matriz):
    resultado = clasificar_matriz(matriz)
    for columna in CUADRANTES:
        discrepancias = [
            (fila["riesgo_comparable"], sin_dato(fila[columna]), sin_dato(fila[f"py_{columna}"]))
            for _, fila in resultado.iterrows()
            if sin_dato(fila[columna]) != sin_dato(fila[f"py_{columna}"])
        ]
        assert not discrepancias, (columna, discrepancias)


@pytest.mark.parametrize("medida", ["directa", "retenida"])
def test_indices_iguales_a_la_vista(matriz, medida):
    siniestros, primas = {
        "directa": ("siniestros_netos", "primas_netas"),
        "retenida": ("siniestros_retenidos", "primas_retenidas"),
    }[medida]
    discrepancias = []
    for _, fila in matriz.iterrows():
        calculado = indice_siniestralidad(sin_dato(fila[siniestros]), sin_dato(fila[primas]))
        vista = sin_dato(fila[f"indice_siniestralidad_{medida}"])
        if (calculado is None) != (vista is None) or (
            calculado is not None and abs(calculado - vista) >= 0.0001
        ):
            discrepancias.append((fila["riesgo_comparable"], calculado, vista))
    assert not discrepancias, discrepancias


@pytest.mark.parametrize("medida", ["directa", "retenida"])
def test_corte_de_siniestralidad_igual_a_la_vista(matriz, medida):
    calculado = corte_siniestralidad(matriz, medida)
    vista = sin_dato(matriz[f"corte_siniestralidad_{medida}"].iloc[0])
    assert calculado is not None and vista is not None
    assert abs(calculado - vista) < 0.0001, (calculado, vista)


def test_clasificacion_igual_a_la_vista(conexion):
    participacion = leer_vista(conexion, "vw_participacion_empresa_riesgo")
    discrepancias, excluidas = [], 0
    for medida, (siniestros, primas) in {
        "directa": ("siniestros_netos", "primas_netas"),
        "retenida": ("siniestros_retenidos", "primas_retenidas"),
    }.items():
        for _, fila in participacion.iterrows():
            s, p = sin_dato(fila[siniestros]), sin_dato(fila[primas])
            # Celdas de borde: el redondeo a 2 decimales puede cambiar de lado la regla.
            if s is not None and p is not None and (abs(s - p) <= 0.01 or abs(s) <= 0.01):
                excluidas += 1
                continue
            esperado = fila[f"clasificacion_{medida}"]
            if clasificar_indice(p, s) != esperado:
                discrepancias.append(
                    (fila["empresa"], fila["riesgo"], fila["fecha_corte"], medida, p, s, esperado)
                )
    celdas = 2 * len(participacion)  # dos medidas por fila
    resumen = f"{len(discrepancias)} discrepancias; {excluidas} de {celdas} celdas de borde"
    assert not discrepancias, f"{resumen}: {discrepancias[:5]}"
    assert celdas - excluidas > 0, resumen


def test_exportar_vistas(conexion, matriz, tmp_path):
    filas = exportar_vistas(conexion, tmp_path)
    assert set(filas) == set(VISTAS_EXPORTADAS.values())
    for nombre in VISTAS_EXPORTADAS.values():
        assert (tmp_path / nombre).is_file(), nombre
    exportada = pd.read_csv(tmp_path / "matriz_riesgos.csv")
    assert len(exportada) == 48 and filas["matriz_riesgos.csv"] == 48
    assert {"cuadrante_interanual_directa", "situacion"} <= set(exportada.columns)
    resumen = resumen_matriz(matriz)
    assert (resumen["filas"], resumen["sobre_umbral"], resumen["no_comparables"]) == (48, 40, 5)
