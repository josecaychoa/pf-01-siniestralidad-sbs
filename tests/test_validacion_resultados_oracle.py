"""Prueba de integración de validacion_resultados contra las vistas de 3.2 (paquete 3.3).

Solo lee la base. Se omite si el entorno no tiene ORACLE_USER, ORACLE_PASSWORD y
ORACLE_DSN, como en GitHub Actions. Ejecutar antes la carga: uv run python
scripts/cargar_oracle.py. Los cinco controles de D-PF01-17 deben estar conformes; el índice
por riesgo, con las 5 excepciones de la fuente de diciembre de 2020 (D-PF01-18).
"""

import os

import oracledb
import pandas as pd
import pytest

from pf_01_siniestralidad_sbs.indicadores import leer_vista
from pf_01_siniestralidad_sbs.validacion_resultados import (
    TOLERANCIA_O2,
    contraste_total_sistema,
    control_cobertura_matriz,
    control_indice_por_riesgo,
    control_o2,
    control_primas_matriz,
    control_serie_total,
)

VARIABLES = ("ORACLE_USER", "ORACLE_PASSWORD", "ORACLE_DSN")
CONSULTA_PUBLICADOS = (
    "SELECT f.fecha_corte, "
    "MAX(CASE WHEN f.hoja = :hoja_primas THEN f.valor END) AS total_p009, "
    "MAX(CASE WHEN f.hoja = :hoja_directa THEN f.valor END) AS directa_publicada, "
    "MAX(CASE WHEN f.hoja = :hoja_retenida THEN f.valor END) AS retenida_publicada "
    "FROM fct_riesgo f "
    "JOIN dim_riesgo r ON r.riesgo_id = f.riesgo_id "
    "JOIN dim_columna_empresa ce ON ce.columna_id = f.columna_id "
    "WHERE r.clave = :clave AND ce.tipo_columna = :tipo_columna "
    "AND f.hoja IN (:hoja_primas, :hoja_directa, :hoja_retenida) "
    "GROUP BY f.fecha_corte"
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
def publicados(conexion):
    cursor = conexion.cursor()
    cursor.execute(
        CONSULTA_PUBLICADOS,
        hoja_primas="P009",
        hoja_directa="P015",
        hoja_retenida="P016",
        clave="TOTAL",
        tipo_columna="total_simple",
    )
    marco = pd.DataFrame(cursor.fetchall(), columns=[d[0].lower() for d in cursor.description])
    marco["fecha_corte"] = pd.to_datetime(marco["fecha_corte"]).dt.date
    return marco


def test_controles_conformes(conexion, publicados):
    corte_actual = leer_vista(conexion, "vw_cortes_analisis")["corte_actual"].iloc[0]
    indicadores = leer_vista(conexion, "vw_indicadores_riesgo")
    matriz = leer_vista(conexion, "vw_matriz_riesgo")
    contraste = contraste_total_sistema(indicadores, publicados)
    total_p009 = publicados.loc[publicados["fecha_corte"] == corte_actual, "total_p009"].iloc[0]
    o2 = control_o2(contraste, corte_actual)
    resultados = [
        o2,
        control_serie_total(contraste),
        control_indice_por_riesgo(indicadores),
        control_cobertura_matriz(matriz),
        control_primas_matriz(matriz, float(total_p009)),
    ]
    assert all(r.ok for r in resultados), [(r.control, r.fallas) for r in resultados if not r.ok]
    por_riesgo = resultados[2]
    assert (por_riesgo.fallas, por_riesgo.excepciones) == (0, 5)  # diciembre de 2020, D-PF01-18
    assert len(o2.detalle) == 2
    assert (o2.detalle["diferencia"].abs() <= TOLERANCIA_O2).all(), o2.detalle
