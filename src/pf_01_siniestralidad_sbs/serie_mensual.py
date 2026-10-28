"""Serie mensual de primas y siniestros por riesgo, enero de 2025 a agosto de 2026 (paquete 4.4).

Lee los cuadros mensuales S-401 (primas) y S-402 (siniestros) de ``data/raw/mensual/``
(registrados en su propio manifiesto por ``scripts/descargar_mensual.py``) y arma una fila por
mes y riesgo comparable con los montos acumulados en el año y los del mes (diferencia entre el
acumulado del mes y el del mes anterior del mismo año).

Para qué sirve (CC-PF-01-02): la SBS cifra los siniestros acumulados en el año, así que el
corte de agosto de 2026 no deja ver en qué mes cambió una serie. Desde la información de marzo
de 2026, el cuadro S-402 pasa a titularse «Siniestros de Primas de Seguros y Otras Obligaciones
Netos…» y su nota 1/ remite a la Resolución SBS N.º 085-2026 (rescates y vencimientos de los
seguros de vida con componente de ahorro). La serie mensual ubica ese quiebre y conserva el
título y la nota de cada cuadro como evidencia de la fuente.

Reglas:
- Solo se usa la columna «TOTAL» del sistema (todas las empresas).
- Cada concepto se reconoce con el catálogo de riesgos (clave normalizada); un concepto
  desconocido detiene el proceso. Los agregados y los detalles («del cual») se descartan, y los
  riesgos con el mismo ``riesgo_comparable`` se suman, igual que en el corte de 3.2.
- Control: en cada mes y medida, la suma de los riesgos cuadra con la fila «TOTAL» del cuadro
  dentro de la tolerancia de O1 (1 mil soles).
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

import pandas as pd

from pf_01_siniestralidad_sbs.descarga import leer_manifiesto
from pf_01_siniestralidad_sbs.extraccion import extraer_matriz, leer_libro
from pf_01_siniestralidad_sbs.validacion import TOLERANCIA, leer_catalogo, normalizar

# Hoja de cada cuadro → medida (montos en miles de soles, acumulados en el año).
HOJAS_MEDIDAS: dict[str, str] = {
    "P009": "primas_netas",
    "P011": "primas_retenidas",
    "P012": "siniestros_netos",
    "P014": "siniestros_retenidos",
}
MEDIDAS = tuple(HOJAS_MEDIDAS.values())
COLUMNAS = [
    "fecha_corte",
    "riesgo_comparable",
    "ramo",
    "siniestralidad_comparable",
    *MEDIDAS,
    *(f"{m}_mes" for m in MEDIDAS),
    "cuadro_siniestros",
    "nota_plan_de_cuentas",
]
PATRON_NOTA_PLAN = re.compile(r"cambios contables dispuestos en la Resoluci", re.IGNORECASE)


class ConceptoDesconocidoError(ValueError):
    """Un concepto del cuadro no figura en el catálogo de riesgos."""


class CuadreError(ValueError):
    """La suma de los riesgos no cuadra con la fila «TOTAL» del cuadro."""


def riesgos_por_clave() -> dict[str, dict[str, str]]:
    """Catálogo de riesgos indexado por clave normalizada (solo filas «riesgo» y «total»)."""
    catalogo = leer_catalogo("riesgos")
    return {
        fila["clave"]: fila
        for fila in catalogo.to_dict("records")
        if fila["tipo"] in ("riesgo", "total")
    }


def todas_las_claves() -> set[str]:
    """Claves de todo el catálogo (incluye agregados y detalles, que se descartan)."""
    return set(leer_catalogo("riesgos")["clave"])


def leer_cuadro(ruta: Path, serie: str, corte: date, sha: str) -> tuple[list[dict], str, str]:
    """Celdas de la columna «TOTAL» del cuadro, su título (P012) y la nota del plan de cuentas."""
    xl = pd.ExcelFile(ruta)
    hojas = tuple(h for h in HOJAS_MEDIDAS if h in {n.strip() for n in xl.sheet_names})
    libro = leer_libro(ruta, serie, corte, sha, hojas)
    celdas: list[dict] = []
    titulo, nota = "", ""
    for hoja, df in libro.hojas.items():
        for registro in extraer_matriz(libro, hoja, df):
            if normalizar(str(registro["empresa"])) == "TOTAL":
                celdas.append(registro)
        if hoja == "P012":
            titulo = " ".join(str(df.iloc[0, 0]).split())
            notas = [
                " ".join(str(v).split())
                for v in df.iloc[:, 0].tolist()
                if isinstance(v, str) and PATRON_NOTA_PLAN.search(v)
            ]
            nota = notas[0] if notas else ""
    return celdas, titulo, nota


def construir_serie(dir_mensual: Path) -> pd.DataFrame:
    """Serie mensual por riesgo comparable a partir de los cuadros y su manifiesto."""
    registros = leer_manifiesto(dir_mensual / "manifest.csv")
    if not registros:
        raise FileNotFoundError(f"No hay manifiesto en {dir_mensual}; ejecute la descarga")
    catalogo = riesgos_por_clave()
    conocidas = todas_las_claves()

    montos: dict[tuple[date, str], dict[str, float]] = defaultdict(dict)
    totales: dict[tuple[date, str], float] = {}
    titulos: dict[date, str] = {}
    notas: dict[date, str] = {}
    for reg in registros.values():
        corte = date.fromisoformat(reg.corte)
        celdas, titulo, nota = leer_cuadro(dir_mensual / reg.archivo, reg.serie, corte, reg.sha256)
        if titulo:
            titulos[corte], notas[corte] = titulo, nota
        for celda in celdas:
            clave = normalizar(str(celda["concepto"]))
            medida = HOJAS_MEDIDAS[celda["hoja"]]
            if clave not in conocidas:
                raise ConceptoDesconocidoError(f"{reg.archivo} {celda['hoja']}: {clave}")
            fila = catalogo.get(clave)
            if fila is None:
                continue  # agregado o detalle: no suma en el total
            if fila["tipo"] == "total":
                totales[(corte, medida)] = float(celda["valor"])
                continue
            acumulado = montos[(corte, fila["riesgo_comparable"])]
            acumulado[medida] = acumulado.get(medida, 0.0) + float(celda["valor"])

    tabla = _a_tabla(montos, catalogo, titulos, notas)
    _cuadrar(tabla, totales)
    return tabla


def _a_tabla(
    montos: dict[tuple[date, str], dict[str, float]],
    catalogo: dict[str, dict[str, str]],
    titulos: dict[date, str],
    notas: dict[date, str],
) -> pd.DataFrame:
    """Tabla ordenada con los montos del mes calculados dentro de cada año."""
    atributos = {f["riesgo_comparable"]: f for f in catalogo.values() if f["tipo"] == "riesgo"}
    filas = []
    for (corte, riesgo), valores in montos.items():
        filas.append(
            {
                "fecha_corte": corte,
                "riesgo_comparable": riesgo,
                "ramo": atributos[riesgo]["ramo"],
                "siniestralidad_comparable": atributos[riesgo]["siniestralidad_comparable"],
                **{m: valores.get(m, 0.0) for m in MEDIDAS},
                "cuadro_siniestros": titulos.get(corte, ""),
                "nota_plan_de_cuentas": notas.get(corte, ""),
            }
        )
    tabla = pd.DataFrame(filas).sort_values(["riesgo_comparable", "fecha_corte"], kind="stable")
    anio = tabla["fecha_corte"].map(lambda d: d.year)
    for medida in MEDIDAS:
        previo = tabla.groupby(["riesgo_comparable", anio])[medida].shift(1).fillna(0.0)
        tabla[f"{medida}_mes"] = tabla[medida] - previo
    tabla = tabla.sort_values(["fecha_corte", "riesgo_comparable"], kind="stable")
    return tabla[COLUMNAS].reset_index(drop=True)


def _cuadrar(tabla: pd.DataFrame, totales: dict[tuple[date, str], float]) -> None:
    """Cada mes y medida: suma de los riesgos = fila «TOTAL» del cuadro (± 1 mil soles)."""
    sumas = tabla.groupby("fecha_corte")[list(MEDIDAS)].sum()
    for (corte, medida), total in totales.items():
        diferencia = sumas.loc[corte, medida] - total
        if abs(diferencia) > TOLERANCIA:
            raise CuadreError(f"{corte} {medida}: riesgos − TOTAL = {diferencia:.2f} mil soles")


def escribir_csv(tabla: pd.DataFrame, ruta: Path) -> None:
    """CSV en UTF-8 con LF y fechas ISO, como el resto de data/processed/."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    salida = tabla.copy()
    salida["fecha_corte"] = salida["fecha_corte"].map(date.isoformat)
    salida.to_csv(
        ruta,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
        float_format="%.2f",
        quoting=csv.QUOTE_MINIMAL,
    )


def leer_csv(ruta: Path) -> pd.DataFrame:
    """Lee la serie mensual versionada con las fechas como ``date``."""
    tabla = pd.read_csv(
        ruta, dtype={"cuadro_siniestros": str, "nota_plan_de_cuentas": str}, keep_default_na=False
    )
    tabla["fecha_corte"] = tabla["fecha_corte"].map(date.fromisoformat)
    return tabla
