"""Reglas del análisis de 3.2 en Python (issue #8): indicadores, crecimiento y matriz.

Programa en funciones puras las decisiones de diseño D-PF01-11 a D-PF01-16, con las mismas
reglas que las vistas de sql/oracle/04_vistas_analisis.sql, para probarlas sin base de datos
(tests/test_indicadores.py) y para contrastarlas fila por fila con las vistas
(tests/test_indicadores_oracle.py):
- D-PF01-11: la variación interanual define el eje de crecimiento y el cuadrante; la TCAC
  acompaña como segundo atributo, con la marca de coincidencia de signos.
- D-PF01-12: índice de siniestralidad = 100 × Σ siniestros / Σ primas del mismo corte.
- D-PF01-13: los índices negativos o mayores que 100 % se clasifican; no se truncan.
- D-PF01-14: índice nulo (None) cuando las primas son 0 o negativas.
- D-PF01-15: rentas y Sistema Privado de Pensiones (siniestralidad_comparable = N) entran en
  la matriz con esa marca, sin cuadrante.
- D-PF01-16: cortes de los cuadrantes: crecimiento 0 % y siniestralidad igual al índice
  agregado de los riesgos comparables sobre el umbral.

None equivale al NULL de las vistas; en los marcos de pandas, NaN se trata como None. Las
funciones de acceso leen las vistas con python-oracledb y las exportan a CSV
(scripts/exportar_indicadores.py).
"""

from __future__ import annotations

from pathlib import Path

import oracledb
import pandas as pd

UMBRAL_PRIMAS = 5000.0  # miles de soles: primas netas acumuladas en el corte (acta, sección 4)
CORTE_CRECIMIENTO = 0.0  # porcentaje: crece si la variación es >= 0 (D-PF01-16)
ETIQUETAS_CUADRANTE = {
    1: "Crece con siniestralidad sobre el corte",
    2: "Crece con siniestralidad bajo el corte",
    3: "Decrece con siniestralidad sobre el corte",
    4: "Decrece con siniestralidad bajo el corte",
}
CLASIFICACIONES = (
    "sin_dato",
    "sin_primas",
    "primas_negativas",
    "negativo",
    "mayor_100",
    "en_rango",
)
VISTAS_EXPORTADAS = {
    "vw_parametros_analisis": "parametros_analisis.csv",
    "vw_cortes_analisis": "cortes_analisis.csv",
    "vw_indicadores_riesgo": "indicadores_riesgo.csv",
    "vw_crecimiento_riesgo": "crecimiento_riesgos.csv",
    "vw_matriz_riesgo": "matriz_riesgos.csv",
    "vw_participacion_empresa_riesgo": "participacion_empresa_riesgo.csv",
}
# Columnas de siniestros y primas de cada medida (D-PF01-12).
COLUMNAS_MEDIDA = {
    "directa": ("siniestros_netos", "primas_netas"),
    "retenida": ("siniestros_retenidos", "primas_retenidas"),
}

# --------------------------------------------------------------------------------------
# Funciones puras
# --------------------------------------------------------------------------------------


def sin_dato(valor: object) -> object:
    """None si el valor es None, NaN o NA (el NULL de las vistas); si no, el valor."""
    return None if valor is None or pd.isna(valor) else valor


def variacion_interanual(actual: float | None, anterior: float | None) -> float | None:
    """Variación porcentual de actual frente a anterior; None sin dato o con base no positiva."""
    if actual is None or anterior is None or anterior <= 0:
        return None
    return 100 * (actual / anterior - 1)


def tcac(inicio: float | None, fin: float | None, anios: float | None) -> float | None:
    """Tasa de crecimiento anual compuesta, en porcentaje; None sin dato o con base no positiva."""
    if inicio is None or fin is None or anios is None:
        return None
    if inicio <= 0 or fin <= 0 or anios <= 0:
        return None
    return 100 * ((fin / inicio) ** (1 / anios) - 1)


def indice_siniestralidad(siniestros: float | None, primas: float | None) -> float | None:
    """100 × siniestros / primas; None sin dato o con primas 0 o negativas (D-PF01-12 y 14)."""
    if siniestros is None or primas is None or primas <= 0:
        return None
    return 100 * siniestros / primas


def signo(x: float) -> int:
    """-1, 0 o 1, como SIGN de Oracle."""
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


def signos_coinciden(variacion: float | None, tcac: float | None) -> str | None:
    """S si la variación y la TCAC tienen el mismo signo, N si no; None si falta alguna."""
    if variacion is None or tcac is None:
        return None
    return "S" if signo(variacion) == signo(tcac) else "N"


def clasificar_indice(primas: float | None, siniestros: float | None) -> str:
    """Clasificación de una celda de siniestralidad, en orden de prioridad (D-PF01-13 y 14)."""
    if primas is None or siniestros is None:
        return "sin_dato"
    if primas == 0:
        return "sin_primas"
    if primas < 0:
        return "primas_negativas"
    if siniestros < 0:
        return "negativo"
    if 100 * siniestros / primas > 100:
        return "mayor_100"
    return "en_rango"


def cuadrante(
    crecimiento: float | None,
    indice: float | None,
    corte_siniestralidad: float | None,
    *,
    sobre_umbral: bool = True,
    comparable: bool = True,
    corte_crecimiento: float = CORTE_CRECIMIENTO,
) -> int | None:
    """Cuadrante 1 a 4 de la matriz; None fuera del umbral, no comparable o sin medida.

    1 crece con siniestralidad sobre el corte; 2 crece bajo el corte; 3 decrece sobre el
    corte; 4 decrece bajo el corte. Crece: crecimiento >= corte_crecimiento; sobre el corte:
    indice > corte_siniestralidad (D-PF01-11, D-PF01-15 y D-PF01-16).
    """
    if not sobre_umbral or not comparable:
        return None
    if crecimiento is None or indice is None or corte_siniestralidad is None:
        return None
    crece = crecimiento >= corte_crecimiento
    sobre_el_corte = indice > corte_siniestralidad
    if crece and sobre_el_corte:
        return 1
    if crece:
        return 2
    if sobre_el_corte:
        return 3
    return 4


def corte_siniestralidad(filas: pd.DataFrame, medida: str = "directa") -> float | None:
    """Índice agregado de las filas comparables sobre el umbral (D-PF01-16); None sin primas.

    filas tiene las columnas de vw_matriz_riesgo (o de vw_base_riesgo_comparable con
    sobre_umbral); medida es «directa» (netos y netas) o «retenida» (retenidos y retenidas).
    """
    siniestros, primas = COLUMNAS_MEDIDA[medida]
    base = filas[(filas["siniestralidad_comparable"] == "S") & (filas["sobre_umbral"] == "S")]
    suma_primas = base[primas].sum()
    if not suma_primas > 0:
        return None
    return 100 * base[siniestros].sum() / suma_primas


def clasificar_matriz(matriz: pd.DataFrame) -> pd.DataFrame:
    """Copia de la matriz con los cuatro cuadrantes recalculados en columnas py_cuadrante_*.

    Usa las mismas columnas que vw_matriz_riesgo: variacion_interanual, tcac, los dos índices
    calculados, los dos cortes de siniestralidad, sobre_umbral y siniestralidad_comparable.
    """
    resultado = matriz.copy()
    combinaciones = {
        "py_cuadrante_interanual_directa": ("variacion_interanual", "directa"),
        "py_cuadrante_interanual_retenida": ("variacion_interanual", "retenida"),
        "py_cuadrante_tcac_directa": ("tcac", "directa"),
        "py_cuadrante_tcac_retenida": ("tcac", "retenida"),
    }
    for columna, (crecimiento, medida) in combinaciones.items():
        resultado[columna] = [
            cuadrante(
                sin_dato(fila[crecimiento]),
                sin_dato(fila[f"indice_siniestralidad_{medida}"]),
                sin_dato(fila[f"corte_siniestralidad_{medida}"]),
                sobre_umbral=fila["sobre_umbral"] == "S",
                comparable=fila["siniestralidad_comparable"] == "S",
            )
            for _, fila in matriz.iterrows()
        ]
    return resultado


def resumen_matriz(matriz: pd.DataFrame) -> dict[str, object]:
    """Conteos y cortes de la matriz, para el script de exportación y las pruebas."""
    sobre_umbral = matriz["sobre_umbral"] == "S"
    no_comparable = matriz["siniestralidad_comparable"] == "N"
    recuento = matriz["cuadrante_interanual_directa"].value_counts(dropna=False)
    por_cuadrante = {sin_dato(clave): int(n) for clave, n in recuento.items()}
    por_cuadrante = {
        (None if clave is None else int(clave)): n
        for clave, n in sorted(por_cuadrante.items(), key=lambda par: (par[0] is None, par[0]))
    }
    cortes = {
        medida: sin_dato(matriz[f"corte_siniestralidad_{medida}"].dropna().iloc[0])
        if matriz[f"corte_siniestralidad_{medida}"].notna().any()
        else None
        for medida in ("directa", "retenida")
    }
    return {
        "filas": int(len(matriz)),
        "sobre_umbral": int(sobre_umbral.sum()),
        "no_comparables": int(no_comparable.sum()),
        "corte_siniestralidad_directa": cortes["directa"],
        "corte_siniestralidad_retenida": cortes["retenida"],
        "por_cuadrante_interanual_directa": por_cuadrante,
    }


# --------------------------------------------------------------------------------------
# Acceso a las vistas
# --------------------------------------------------------------------------------------


def leer_vista(conexion: oracledb.Connection, vista: str) -> pd.DataFrame:
    """Marco con SELECT * FROM vista; columnas en minúscula, fechas como date y cuadrantes Int64.

    Solo admite las vistas de VISTAS_EXPORTADAS (nombres fijos del modelo, no datos de
    entrada); otra vista lanza ValueError. Las columnas cuadrante_* usan el entero con nulos
    de pandas (Int64) para que el CSV lleve 1 a 4 o vacío, nunca «1.0».
    """
    if vista not in VISTAS_EXPORTADAS:
        raise ValueError(f"vista no exportable: {vista!r}")
    cursor = conexion.cursor()
    cursor.execute(f"SELECT * FROM {vista}")
    columnas = [descripcion[0].lower() for descripcion in cursor.description]
    marco = pd.DataFrame(cursor.fetchall(), columns=columnas)
    for columna in marco.columns:
        if pd.api.types.is_datetime64_any_dtype(marco[columna]):
            marco[columna] = marco[columna].dt.date
        elif columna.startswith("cuadrante_"):
            marco[columna] = marco[columna].astype("Int64")
    return marco


def exportar_vistas(conexion: oracledb.Connection, destino: Path) -> dict[str, int]:
    """Escribe cada vista de VISTAS_EXPORTADAS como CSV en destino; devuelve filas por archivo."""
    destino.mkdir(parents=True, exist_ok=True)
    filas = {}
    for vista, nombre in VISTAS_EXPORTADAS.items():
        marco = leer_vista(conexion, vista)
        marco.to_csv(
            destino / nombre,
            index=False,
            encoding="utf-8",
            lineterminator="\n",
            date_format="%Y-%m-%d",
        )
        filas[nombre] = len(marco)
    return filas
