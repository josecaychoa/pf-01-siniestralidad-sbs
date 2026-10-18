"""Pruebas de integración de las vistas de análisis (paquete 3.2, D-PF01-11 a D-PF01-16).

Solo leen la base. Se omiten si el entorno no tiene ORACLE_USER, ORACLE_PASSWORD y
ORACLE_DSN, como en GitHub Actions. Ejecutar antes la carga: uv run python
scripts/cargar_oracle.py. Las cifras esperadas salen del notebook de 3.1
(notebooks/01-jc-exploracion.ipynb, hallazgos 8 y 9 y sección 5).
"""

import os
from datetime import datetime

import oracledb
import pytest

VARIABLES = ("ORACLE_USER", "ORACLE_PASSWORD", "ORACLE_DSN")
CORTE_ACTUAL = "DATE '2026-08-31'"
CLASIFICACIONES = {
    "sin_dato",
    "sin_primas",
    "primas_negativas",
    "negativo",
    "mayor_100",
    "en_rango",
}

pytestmark = pytest.mark.skipif(
    not all(os.environ.get(v) for v in VARIABLES), reason="sin variables de conexión a Oracle"
)


@pytest.fixture(scope="module")
def cursor():
    with oracledb.connect(
        user=os.environ["ORACLE_USER"],
        password=os.environ["ORACLE_PASSWORD"],
        dsn=os.environ["ORACLE_DSN"],
    ) as conexion:
        yield conexion.cursor()


def una_fila(cursor, consulta: str) -> tuple:
    cursor.execute(consulta)
    filas = cursor.fetchall()
    assert len(filas) == 1, filas
    return filas[0]


def escalar(cursor, consulta: str):
    return una_fila(cursor, consulta)[0]


def fila_matriz(cursor, riesgo_comparable: str, columnas: str) -> tuple:
    return una_fila(
        cursor,
        f"SELECT {columnas} FROM vw_matriz_riesgo WHERE riesgo_comparable = '{riesgo_comparable}'",
    )


# --------------------------------------------------------------------------------------
# a) vw_cortes_analisis
# --------------------------------------------------------------------------------------


def test_cortes_del_analisis(cursor):
    fila = una_fila(
        cursor,
        "SELECT corte_actual, corte_anterior, corte_inicio_tcac, corte_fin_tcac, anios_tcac "
        "FROM vw_cortes_analisis",
    )
    assert fila == (
        datetime(2026, 8, 31),
        datetime(2025, 8, 31),
        datetime(2019, 12, 31),
        datetime(2025, 12, 31),
        6,
    )


# --------------------------------------------------------------------------------------
# b) vw_matriz_riesgo
# --------------------------------------------------------------------------------------


def test_matriz_filas_y_umbral(cursor):
    total, sobre = una_fila(
        cursor,
        "SELECT COUNT(*), SUM(CASE WHEN sobre_umbral = 'S' THEN 1 ELSE 0 END) "
        "FROM vw_matriz_riesgo",
    )
    assert (total, sobre) == (48, 40)


def test_matriz_filas_bajo_el_umbral(cursor):
    bbb = fila_matriz(cursor, "Seguro de Bancos (BBB)", "sobre_umbral, primas_netas")
    assert bbb[0] == "N" and 4808 <= bbb[1] <= 4810
    vida_ley = fila_matriz(cursor, "Vida Ley Ex-trabajadores", "sobre_umbral, primas_netas")
    assert vida_ley[0] == "N" and abs(vida_ley[1] - 4997.71) <= 0.01


def test_matriz_cauciones_y_fianzas(cursor):
    n_riesgos, sobre, tcac, variacion = fila_matriz(
        cursor, "Cauciones y fianzas", "n_riesgos, sobre_umbral, tcac, variacion_interanual"
    )
    assert (n_riesgos, sobre) == (3, "S")
    assert 10.95 <= tcac <= 11.05
    assert -1.25 <= variacion <= -1.15


def test_matriz_rentas_y_spp_sin_cuadrante(cursor):
    cursor.execute(
        "SELECT cuadrante_interanual_directa, cuadrante_interanual_retenida, "
        "cuadrante_tcac_directa, cuadrante_tcac_retenida, situacion FROM vw_matriz_riesgo "
        "WHERE sobre_umbral = 'S' AND siniestralidad_comparable = 'N'"
    )
    filas = cursor.fetchall()
    assert len(filas) == 5
    assert all(fila == (None, None, None, None, "No comparable (rentas y SPP)") for fila in filas)


def test_matriz_cuadrantes_definidos(cursor):
    en_la_matriz = "SELECT COUNT(*) FROM vw_matriz_riesgo WHERE situacion = 'En la matriz'"
    sin_cuadrante = (
        f"{en_la_matriz} AND (cuadrante_interanual_directa IS NULL "
        "OR cuadrante_interanual_directa NOT BETWEEN 1 AND 4)"
    )
    assert escalar(cursor, sin_cuadrante) == 0
    assert escalar(cursor, en_la_matriz) > 0


def test_matriz_cortes_de_siniestralidad(cursor):
    directa, retenida = una_fila(
        cursor,
        "SELECT DISTINCT corte_siniestralidad_directa, corte_siniestralidad_retenida "
        "FROM vw_matriz_riesgo",
    )
    assert 0 < directa < 100 and 0 < retenida < 100


def test_matriz_incendio(cursor):
    directa, retenida = fila_matriz(
        cursor, "Incendio", "indice_siniestralidad_directa, indice_siniestralidad_retenida"
    )
    assert 223.95 <= directa <= 224.05
    assert 55.35 <= retenida <= 55.45


def test_matriz_suma_con_el_total_publicado(cursor):
    suma = escalar(cursor, "SELECT SUM(primas_netas) FROM vw_matriz_riesgo")
    total = escalar(
        cursor,
        "SELECT f.valor FROM fct_riesgo f "
        "JOIN dim_riesgo r ON r.riesgo_id = f.riesgo_id "
        "JOIN dim_columna_empresa ce ON ce.columna_id = f.columna_id "
        "WHERE r.clave = 'TOTAL' AND f.hoja = 'P009' AND ce.tipo_columna = 'total_simple' "
        f"AND f.fecha_corte = {CORTE_ACTUAL}",
    )
    assert abs(suma - total) < 1


def test_matriz_indices_agregados_del_sistema(cursor):
    directa, retenida = una_fila(
        cursor,
        "SELECT 100 * SUM(siniestros_netos) / SUM(primas_netas), "
        "100 * SUM(siniestros_retenidos) / SUM(primas_retenidas) FROM vw_matriz_riesgo",
    )
    assert abs(directa - 48.9141) < 0.001  # hallazgo 9
    assert abs(retenida - 45.7487) < 0.001


def test_matriz_indice_calculado_igual_al_publicado(cursor):
    diferencia = escalar(
        cursor,
        "SELECT MAX(ABS(indice_siniestralidad_directa - indice_directa_publicado)) "
        "FROM vw_matriz_riesgo WHERE n_riesgos = 1 AND primas_netas > 0",
    )
    assert diferencia < 0.1  # tolerancia de O2


def test_matriz_signos_coinciden(cursor):
    cursor.execute(
        "SELECT riesgo_comparable, signos_coinciden, SIGN(variacion_interanual), SIGN(tcac) "
        "FROM vw_matriz_riesgo WHERE variacion_interanual IS NOT NULL AND tcac IS NOT NULL"
    )
    filas = cursor.fetchall()
    assert filas
    for riesgo, marca, signo_variacion, signo_tcac in filas:
        assert (marca == "N") == (signo_variacion != signo_tcac), riesgo


# --------------------------------------------------------------------------------------
# c) vw_participacion_empresa_riesgo
# --------------------------------------------------------------------------------------


def test_participacion_suma_cien_por_riesgo(cursor):
    cursor.execute(
        "SELECT riesgo_id, SUM(participacion_riesgo), SUM(primas_netas) "
        f"FROM vw_participacion_empresa_riesgo WHERE fecha_corte = {CORTE_ACTUAL} "
        "GROUP BY riesgo_id"
    )
    filas = cursor.fetchall()
    positivos = [(riesgo, suma) for riesgo, suma, primas in filas if primas > 0]
    assert positivos
    for riesgo, suma in positivos:
        assert abs(suma - 100) < 0.001, riesgo


@pytest.mark.parametrize("columna", ["clasificacion_directa", "clasificacion_retenida"])
def test_participacion_dominio_de_la_clasificacion(cursor, columna):
    cursor.execute(f"SELECT DISTINCT {columna} FROM vw_participacion_empresa_riesgo")
    valores = {fila[0] for fila in cursor.fetchall()}
    assert valores and valores <= CLASIFICACIONES


def test_participacion_indice_nulo_sin_primas(cursor):
    consulta = (
        "SELECT COUNT(*) FROM vw_participacion_empresa_riesgo "
        "WHERE primas_netas <= 0 AND indice_siniestralidad_directa IS NOT NULL"
    )
    assert escalar(cursor, consulta) == 0


def test_participacion_incendio_sobre_el_umbral(cursor):
    cursor.execute(
        "SELECT clasificacion_directa FROM vw_participacion_empresa_riesgo "
        f"WHERE fecha_corte = {CORTE_ACTUAL} AND riesgo = 'Incendio' AND sobre_umbral = 'S'"
    )
    clasificaciones = [fila[0] for fila in cursor.fetchall()]
    assert len(clasificaciones) == 5  # hallazgo 8
    assert set(clasificaciones) == {"mayor_100"}


# --------------------------------------------------------------------------------------
# d) vw_indicadores_riesgo
# --------------------------------------------------------------------------------------


def test_indicadores_cortes_y_filas(cursor):
    cortes, en_corte_actual = una_fila(
        cursor,
        "SELECT COUNT(DISTINCT fecha_corte), "
        f"SUM(CASE WHEN fecha_corte = {CORTE_ACTUAL} THEN 1 ELSE 0 END) FROM vw_indicadores_riesgo",
    )
    assert (cortes, en_corte_actual) == (9, 48)


def test_indicadores_columna_total(cursor):
    actual = escalar(
        cursor,
        "SELECT DISTINCT columna_total FROM vw_indicadores_riesgo "
        f"WHERE fecha_corte = {CORTE_ACTUAL}",
    )
    assert actual == "TOTAL"
    cursor.execute(
        "SELECT DISTINCT columna_total FROM vw_indicadores_riesgo "
        "WHERE fecha_corte = DATE '2022-12-31'"
    )
    valores_2022 = {fila[0] for fila in cursor.fetchall()}
    assert valores_2022 and "TOTAL" not in valores_2022  # prioridad de la columna ampliada
