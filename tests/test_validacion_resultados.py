"""Pruebas unitarias de validacion_resultados (paquete 3.3), sin base de datos."""

from datetime import date

import pandas as pd
import pytest

from pf_01_siniestralidad_sbs.validacion_resultados import (
    COBERTURA_ESPERADA,
    TOLERANCIA_O2,
    contraste_total_sistema,
    control_cobertura_matriz,
    control_indice_por_riesgo,
    control_o2,
    control_primas_matriz,
    control_serie_total,
    informe,
)

CORTE_ANTERIOR = date(2025, 8, 31)
CORTE_ACTUAL = date(2026, 8, 31)


def fila_indicador(corte, riesgo, primas, siniestros, publicado=None, n_riesgos=1, **otras):
    """Fila de vw_indicadores_riesgo con las mismas cifras en la directa y en la retenida."""
    indice = 100 * siniestros / primas if primas > 0 else None
    fila = {
        "fecha_corte": corte,
        "meses_acumulados": 8,
        "riesgo_comparable": riesgo,
        "n_riesgos": n_riesgos,
        "primas_netas": primas,
        "primas_retenidas": primas,
        "siniestros_netos": siniestros,
        "siniestros_retenidos": siniestros,
        "indice_siniestralidad_directa": indice,
        "indice_siniestralidad_retenida": indice,
        "indice_directa_publicado": indice if publicado is None else publicado,
        "indice_retenida_publicado": indice if publicado is None else publicado,
    }
    fila.update(otras)
    return fila


@pytest.fixture
def indicadores():
    # Actual: Σ siniestros / Σ primas = 500 / 1 000 = 50 %. Anterior: 300 / 1 000 = 30 %.
    return pd.DataFrame(
        [
            fila_indicador(CORTE_ACTUAL, "Incendio", 600.0, 400.0),
            fila_indicador(CORTE_ACTUAL, "Vehículos", 400.0, 100.0),
            fila_indicador(CORTE_ANTERIOR, "Incendio", 600.0, 200.0),
            fila_indicador(CORTE_ANTERIOR, "Vehículos", 400.0, 100.0),
        ]
    )


@pytest.fixture
def publicados():
    # El corte actual cuadra (50.05: diferencia -0.05); el anterior no (30.5: -0.5).
    return pd.DataFrame(
        {
            "fecha_corte": [CORTE_ANTERIOR, CORTE_ACTUAL],
            "total_p009": [1000.0, 1000.0],
            "directa_publicada": [30.5, 50.05],
            "retenida_publicada": [30.0, 50.0],
        }
    )


@pytest.fixture
def contraste(indicadores, publicados):
    return contraste_total_sistema(indicadores, publicados)


def test_contraste_total_sistema(contraste):
    assert list(contraste["fecha_corte"]) == [CORTE_ANTERIOR, CORTE_ACTUAL]
    actual = contraste.iloc[1]
    assert actual["meses_acumulados"] == 8
    assert actual["primas_netas"] == pytest.approx(1000)
    assert actual["siniestros_retenidos"] == pytest.approx(500)
    assert actual["directa_calculada"] == pytest.approx(50)
    assert actual["diferencia_directa"] == pytest.approx(-0.05)
    assert abs(actual["diferencia_directa"]) <= TOLERANCIA_O2
    anterior = contraste.iloc[0]
    assert anterior["diferencia_directa"] == pytest.approx(-0.5)
    assert abs(anterior["diferencia_directa"]) > TOLERANCIA_O2
    assert anterior["diferencia_retenida"] == pytest.approx(0)


def test_control_o2_conforme(contraste):
    resultado = control_o2(contraste, CORTE_ACTUAL)
    assert resultado.control == "O2 · índice total del sistema, agosto de 2026"
    assert (resultado.revisados, resultado.fallas, resultado.ok) == (2, 0, True)


def test_control_o2_con_falla(contraste):
    resultado = control_o2(contraste, CORTE_ANTERIOR)
    assert (resultado.revisados, resultado.fallas) == (2, 1)
    falla = resultado.detalle[~resultado.detalle["conforme"]]
    assert list(falla["medida"]) == ["directa"]


def test_control_o2_sin_el_corte(contraste):
    resultado = control_o2(contraste, date(2027, 8, 31))
    assert resultado.fallas == 2


def test_control_serie_total_con_falla_localizada(contraste):
    resultado = control_serie_total(contraste)
    assert (resultado.revisados, resultado.fallas) == (4, 1)
    falla = resultado.detalle[~resultado.detalle["conforme"]].iloc[0]
    assert (falla["fecha_corte"], falla["medida"]) == (CORTE_ANTERIOR, "directa")


def test_control_serie_total_publicado_faltante_es_falla(indicadores, publicados):
    sin_dato = publicados.assign(retenida_publicada=[30.0, None])
    resultado = control_serie_total(contraste_total_sistema(indicadores, sin_dato))
    assert resultado.fallas == 2  # directa de 2025 y retenida de 2026 sin publicado


def test_control_indice_por_riesgo():
    filas = pd.DataFrame(
        [
            fila_indicador(CORTE_ACTUAL, "Incendio", 600.0, 400.0),
            fila_indicador(CORTE_ACTUAL, "Vehículos", 400.0, 100.0, publicado=25.3),
            # Ignoradas: varios riesgos, primas cero y primas negativas.
            fila_indicador(CORTE_ACTUAL, "Cauciones y fianzas", 50.0, 10.0, 90.0, n_riesgos=3),
            fila_indicador(CORTE_ACTUAL, "Sin primas", 0.0, 10.0, publicado=99.0),
            fila_indicador(CORTE_ACTUAL, "Negativas", -5.0, 10.0, publicado=99.0),
        ]
    )
    resultado = control_indice_por_riesgo(filas)
    assert resultado.control == "Índice por riesgo frente al publicado, 2019-2026"
    assert (resultado.revisados, resultado.fallas) == (4, 2)  # 2 filas por 2 medidas
    detalle = resultado.detalle.set_index("medida")
    assert list(detalle["filas"]) == [2, 2]
    assert detalle.loc["directa", "diferencia_maxima"] == pytest.approx(0.3)
    assert detalle.loc["directa", "riesgo_comparable"] == "Vehículos"


def test_control_indice_por_riesgo_retenida_con_sus_primas():
    fila = fila_indicador(CORTE_ACTUAL, "Incendio", 600.0, 400.0, primas_retenidas=0.0)
    resultado = control_indice_por_riesgo(pd.DataFrame([fila]))
    assert list(resultado.detalle["medida"]) == ["directa"]


def matriz_sintetica(por_cuadrante=None):
    """Matriz con los recuentos de COBERTURA_ESPERADA (48 filas, 40 sobre el umbral)."""
    por_cuadrante = por_cuadrante or COBERTURA_ESPERADA["por_cuadrante"]
    cuadrantes = [c for c, n in por_cuadrante.items() for _ in range(n)]
    filas = len(cuadrantes)
    return pd.DataFrame(
        {
            "riesgo_comparable": [f"Riesgo {i}" for i in range(filas)],
            "sobre_umbral": ["S"] * 40 + ["N"] * (filas - 40),
            "siniestralidad_comparable": ["S"] * 35 + ["N"] * 5 + ["S"] * (filas - 40),
            "cuadrante_interanual_directa": pd.array(cuadrantes, dtype="Int64"),
            "corte_siniestralidad_directa": [48.9] * filas,
            "corte_siniestralidad_retenida": [45.7] * filas,
            "primas_netas": [100.0] * filas,
        }
    )


def test_control_cobertura_matriz_conforme():
    resultado = control_cobertura_matriz(matriz_sintetica())
    assert (resultado.revisados, resultado.fallas) == (9, 0)
    obtenido = resultado.detalle.set_index("magnitud")["obtenido"]
    assert obtenido["Clasificadas"] == 35 and obtenido["Sin cuadrante"] == 13


def test_control_cobertura_matriz_con_recuento_distinto():
    resultado = control_cobertura_matriz(matriz_sintetica({1: 10, 2: 11, 3: 7, 4: 7, None: 13}))
    fallas = resultado.detalle[~resultado.detalle["conforme"]]
    assert list(fallas["magnitud"]) == ["Cuadrante 1", "Cuadrante 2"]
    assert resultado.fallas == 2


def test_control_primas_matriz_en_el_borde():
    matriz = pd.DataFrame({"primas_netas": [600.0, 400.0]})
    assert control_primas_matriz(matriz, 999.01).ok  # 0.99 mil soles
    con_falla = control_primas_matriz(matriz, 999.0)  # 1.00 mil soles
    assert (con_falla.revisados, con_falla.fallas) == (1, 1)


def test_informe(indicadores, publicados, contraste):
    por_riesgo = control_indice_por_riesgo(indicadores)
    cobertura = control_cobertura_matriz(matriz_sintetica())
    resultados = [
        control_o2(contraste, CORTE_ACTUAL),
        control_serie_total(contraste),
        por_riesgo,
        cobertura,
        control_primas_matriz(pd.DataFrame({"primas_netas": [1000.0]}), 1000.0),
    ]
    entorno = {
        "fecha_generacion": "2026-10-18",
        "base": "nativa",
        "version": "Oracle Database 23ai Free",
        "corte_actual": "2026-08-31 (agosto de 2026)",
        "fecha_descarga": "2026-10-11",
    }
    pruebas = {"comando": "uv run pytest -q", "resumen": "30 passed in 2.00s", "codigo": 0}
    texto = informe(resultados, contraste, por_riesgo.detalle, cobertura.detalle, entorno, pruebas)
    for seccion in (
        "# Validación de resultados · PF-01 · Paquete 3.3",
        "Tolerancia de O2: 0.1 p. p.",
        "## Entorno",
        "| Control | Revisados | Fallas | Resultado |",
        "## Tabla 1. Índice total del sistema por corte",
        "## Tabla 2. Índice por riesgo: diferencia máxima por corte",
        "## Tabla 3. Cobertura de la matriz",
        "## Lectura",
        "## Pruebas automatizadas citadas",
        "## Referencias",
    ):
        assert seccion in texto, seccion
    assert "| 1 000 |" in texto  # separador de millares de espacio
    assert "p. p." in texto
    assert "| -0.5000 |" in texto and "| -0.0500 |" in texto
    assert "Con fallas" in texto  # la serie tiene una falla
    assert texto.count("*Nota.* Elaboración propia con datos de SBS") == 5  # una por tabla
    assert "test_clasificacion_igual_a_la_vista" in texto and "Aprobada" in texto
    assert "—" not in texto and "–" not in texto
