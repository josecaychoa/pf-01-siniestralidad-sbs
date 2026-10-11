"""Lleva las hojas del Boletín Mensual S-367 y de los cuadros S-401 a S-403 a formato largo.

Maquetaciones encontradas en los 9 cortes (verificado el 2026-10-11):
- Matriz: P003 y P009 a P016 (y S-401 a S-403). Etiqueta en la columna 0 y una columna por
  empresa; encabezado «Riesgos / Empresas» o «Conceptos / Empresas».
- Indicadores: P004. Sección en la columna 0, indicador en la columna 1 y empresas desde la 2.
- Bloques: P001 y P002. Bloques de tres columnas (MN, ME y TOTAL) por empresa; la columna de
  etiquetas se repite cada cuatro empresas.

La extracción no corrige ni interpreta: conserva la etiqueta original, separa las llamadas a
nota («1/», «(2)») y marca las columnas de total. La tabla de equivalencias de empresas, el
catálogo de riesgos y la elección del total para los cuadres corresponden al paquete 2.2.
"""

from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from pf_01_siniestralidad_sbs.descarga import FIRMA_ZIP, leer_manifiesto

# Hojas del alcance (acta, sección 4) y archivo de salida en data/interim/.
HOJAS_ESTADOS = ("P001", "P002")
HOJAS_INDICADORES = ("P003", "P004")
HOJAS_RIESGOS = tuple(f"P{n:03d}" for n in range(9, 17))
SALIDAS = {
    "estados_financieros.csv": HOJAS_ESTADOS,
    "indicadores.csv": HOJAS_INDICADORES,
    "riesgos.csv": HOJAS_RIESGOS,
}

COLUMNAS = [
    "serie",
    "corte",
    "hoja",
    "cuadro",
    "unidad",
    "seccion",
    "fila",
    "columna",
    "concepto_original",
    "concepto",
    "sangria",
    "llamadas_concepto",
    "empresa_original",
    "empresa",
    "llamadas_empresa",
    "es_total",
    "moneda",
    "valor",
    "sha256_archivo",
]

MESES_ES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "setiembre": 9,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}

RE_CORTE = re.compile(r"Al\s+(\d{1,2})\s+de\s+([A-Za-zÁÉÍÓÚáéíóú]+)\s+del?\s+(\d{4})")
RE_LLAMADA_BARRA = re.compile(r"(?<!\S)\d{1,2}/(?=\s|$)")
RE_LLAMADA_PARENTESIS = re.compile(r"\s*\(\d{1,2}\)\s*$")
MONEDAS = ("MN", "ME", "TOTAL")


class EstructuraError(ValueError):
    """La hoja no tiene la estructura esperada: la extracción se detiene (riesgo R2)."""


@dataclass(frozen=True)
class Libro:
    """Un libro Excel leído de data/raw, con su procedencia."""

    serie: str
    corte: date
    sha256: str
    hojas: dict[str, pd.DataFrame]


# --------------------------------------------------------------------------------------
# Utilidades de texto
# --------------------------------------------------------------------------------------


def es_texto(valor: object) -> bool:
    """Verdadero si el valor es una cadena con contenido."""
    return isinstance(valor, str) and valor.strip() != ""


def separar_llamadas(texto: str) -> tuple[str, str]:
    """Separa las llamadas a nota de una etiqueta.

    >>> separar_llamadas("Avla Perú 5/")
    ('Avla Perú', '5/')
    >>> separar_llamadas("Total + Rigel + Coface Seguros (3)")
    ('Total + Rigel + Coface Seguros', '(3)')
    """
    limpio = " ".join(texto.split())
    llamadas: list[str] = []
    while True:  # llamadas entre paréntesis al final: «(1)», «(abs) (2)» conserva «(abs)»
        m = RE_LLAMADA_PARENTESIS.search(limpio)
        if not m:
            break
        llamadas.insert(0, m.group().strip())
        limpio = limpio[: m.start()]
    llamadas = RE_LLAMADA_BARRA.findall(limpio) + llamadas
    limpio = " ".join(RE_LLAMADA_BARRA.sub(" ", limpio).split())
    return limpio, " ".join(llamadas)


def normalizar_hoja(nombre: str) -> str:
    """Nombre de hoja sin espacios (en diciembre de 2020 aparecen «P003 » y «P004 »)."""
    return nombre.strip()


def leer_corte(df: pd.DataFrame) -> date:
    """Fecha de corte del rótulo «Al 31 de Agosto del 2026» en las primeras filas."""
    for valor in df.iloc[:5].to_numpy().ravel():
        if es_texto(valor):
            m = RE_CORTE.search(valor)
            if m:
                mes = MESES_ES.get(m.group(2).lower())
                if mes:
                    return date(int(m.group(3)), mes, int(m.group(1)))
    raise EstructuraError("No se encontró el rótulo de la fecha de corte")


def leer_unidad(df: pd.DataFrame) -> str:
    """Unidad declarada bajo el título, p. ej. «En Miles de Soles» o «En Porcentaje»."""
    for valor in df.iloc[:5, 0]:
        if es_texto(valor) and valor.strip().startswith("("):
            return " ".join(valor.strip().strip("()").split())
    return ""


def a_numero(valor: object) -> float | None:
    """Convierte una celda a número; vacíos, guiones y textos devuelven None."""
    if isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float)):
        return None if pd.isna(valor) else float(valor)
    if isinstance(valor, str):
        try:
            return float(valor.replace(" ", ""))
        except ValueError:
            return None
    return None


# --------------------------------------------------------------------------------------
# Lectura de libros
# --------------------------------------------------------------------------------------


def motor_excel(contenido: bytes) -> str:
    """Motor de pandas según la firma, no la extensión (el .xls de 2019 es un .xlsx)."""
    return "openpyxl" if contenido.startswith(FIRMA_ZIP) else "xlrd"


def leer_libro(ruta: Path, serie: str, corte: date, sha: str, hojas: tuple[str, ...]) -> Libro:
    """Lee las hojas pedidas de un ZIP del Boletín Mensual o de un cuadro .XLS suelto."""
    contenido = ruta.read_bytes()
    if ruta.suffix.upper() == ".ZIP":
        with zipfile.ZipFile(io.BytesIO(contenido)) as z:
            nombres = [n for n in z.namelist() if not n.endswith("/")]
            if len(nombres) != 1:
                raise EstructuraError(f"{ruta.name}: se esperaba un libro y hay {len(nombres)}")
            contenido = z.read(nombres[0])
    xl = pd.ExcelFile(io.BytesIO(contenido), engine=motor_excel(contenido))
    disponibles = {normalizar_hoja(n): n for n in xl.sheet_names}
    leidas: dict[str, pd.DataFrame] = {}
    for hoja in hojas:
        if hoja in disponibles:
            leidas[hoja] = xl.parse(disponibles[hoja], header=None, dtype=object)
    return Libro(serie=serie, corte=corte, sha256=sha, hojas=leidas)


# --------------------------------------------------------------------------------------
# Maquetaciones
# --------------------------------------------------------------------------------------


def _fila_encabezado(df: pd.DataFrame) -> int:
    """Fila cuyo primer valor termina en «/ Empresas» (matriz e indicadores)."""
    for i in range(min(15, len(df))):
        valor = df.iloc[i, 0]
        if es_texto(valor) and valor.strip().lower().endswith("/ empresas"):
            return i
    raise EstructuraError("No se encontró la fila «… / Empresas»")


def _registro(
    libro: Libro,
    hoja: str,
    df: pd.DataFrame,
    fila: int,
    columna: int,
    concepto_original: str,
    empresa_original: str,
    valor: float,
    seccion: str = "",
    moneda: str = "",
) -> dict[str, object]:
    concepto, llamadas_concepto = separar_llamadas(concepto_original)
    empresa, llamadas_empresa = separar_llamadas(empresa_original)
    cuadro, _ = separar_llamadas(str(df.iloc[0, 0]))
    return {
        "serie": libro.serie,
        "corte": libro.corte.isoformat(),
        "hoja": hoja,
        "cuadro": cuadro,
        "unidad": leer_unidad(df),
        "seccion": seccion,
        "fila": fila + 1,  # numeración de Excel (1 = primera fila)
        "columna": columna + 1,
        "concepto_original": concepto_original.rstrip(),
        "concepto": concepto,
        "sangria": len(concepto_original) - len(concepto_original.lstrip()),
        "llamadas_concepto": llamadas_concepto,
        "empresa_original": " ".join(empresa_original.split()),
        "empresa": empresa,
        "llamadas_empresa": llamadas_empresa,
        "es_total": empresa.upper().startswith("TOTAL"),
        "moneda": moneda,
        "valor": valor,
        "sha256_archivo": libro.sha256,
    }


def extraer_matriz(libro: Libro, hoja: str, df: pd.DataFrame) -> list[dict[str, object]]:
    """Matriz (P003, P009 a P016) e indicadores (P004): etiqueta por fila y empresa por columna.

    Si la columna 1 del encabezado está vacía (P004), la columna 0 es la sección y la 1 la
    etiqueta; si no, la etiqueta está en la columna 0.
    """
    h = _fila_encabezado(df)
    col_etiqueta = 1 if pd.isna(df.iloc[h, 1]) else 0

    def empresas_de(fila: int) -> dict[int, str]:
        encontradas = {
            j: str(df.iloc[fila, j])
            for j in range(col_etiqueta + 1, df.shape[1])
            if es_texto(df.iloc[fila, j])
        }
        if not encontradas:
            raise EstructuraError(f"{hoja}: no hay columnas de empresas en la fila {fila + 1}")
        return encontradas

    empresas = empresas_de(h)
    registros: list[dict[str, object]] = []
    seccion = ""
    for i in range(h + 1, len(df)):
        primera = df.iloc[i, 0]
        if es_texto(primera) and primera.strip().lower().endswith("/ empresas"):
            # P003 repite el encabezado a mitad de hoja con llamadas propias (p. ej., «(4)»).
            empresas = empresas_de(i)
            continue
        etiqueta = df.iloc[i, col_etiqueta]
        valores = {j: a_numero(df.iloc[i, j]) for j in empresas}
        hay_numeros = any(v is not None for v in valores.values())
        if col_etiqueta == 1 and es_texto(df.iloc[i, 0]) and not hay_numeros:
            seccion = " ".join(str(df.iloc[i, 0]).split())
            continue
        if not es_texto(etiqueta) or not hay_numeros:
            continue  # filas vacías, notas al pie o indicadores sin dato publicado
        for j, valor in valores.items():
            if valor is not None:
                registros.append(
                    _registro(libro, hoja, df, i, j, str(etiqueta), empresas[j], valor, seccion)
                )
    return registros


def extraer_bloques(libro: Libro, hoja: str, df: pd.DataFrame) -> list[dict[str, object]]:
    """Estados financieros (P001 y P002): bloques MN, ME y TOTAL por empresa."""
    fila_monedas = next(
        (
            i
            for i in range(min(15, len(df)))
            if any(str(v).strip() == "MN" for v in df.iloc[i] if es_texto(v))
        ),
        None,
    )
    if fila_monedas is None:
        raise EstructuraError(f"{hoja}: no se encontró la fila de monedas MN, ME y TOTAL")
    m, h = fila_monedas, fila_monedas - 1
    monedas = [str(v).strip() if es_texto(v) else "" for v in df.iloc[m]]

    inicios = [j for j in range(len(monedas) - 2) if tuple(monedas[j : j + 3]) == MONEDAS]
    if not inicios:
        raise EstructuraError(f"{hoja}: no hay bloques MN, ME y TOTAL")

    # Columnas de etiquetas: con texto en el cuerpo y sin moneda en la fila de monedas.
    cuerpo = df.iloc[m + 1 :]
    col_texto = [
        j
        for j in range(df.shape[1])
        if monedas[j] == "" and sum(es_texto(v) for v in cuerpo.iloc[:, j]) >= 5
    ]

    registros: list[dict[str, object]] = []
    for j in inicios:
        nombres = [str(df.iloc[h, k]) for k in range(j, j + 3) if es_texto(df.iloc[h, k])]
        if len(nombres) != 1:
            raise EstructuraError(f"{hoja}: bloque en la columna {j + 1} sin empresa única")
        etiquetas = [k for k in col_texto if k < j]
        if not etiquetas:
            raise EstructuraError(f"{hoja}: bloque en la columna {j + 1} sin etiquetas")
        k_etiqueta = etiquetas[-1]
        for i in range(m + 1, len(df)):
            etiqueta = df.iloc[i, k_etiqueta]
            if not es_texto(etiqueta):
                continue
            for desplazamiento, moneda in enumerate(MONEDAS):
                valor = a_numero(df.iloc[i, j + desplazamiento])
                if valor is not None:
                    registros.append(
                        _registro(
                            libro,
                            hoja,
                            df,
                            i,
                            j + desplazamiento,
                            str(etiqueta),
                            nombres[0],
                            valor,
                            moneda=moneda,
                        )
                    )
    return registros


def extraer_hoja(libro: Libro, hoja: str) -> list[dict[str, object]]:
    """Extrae una hoja con la maquetación que le corresponde y valida su fecha de corte."""
    df = libro.hojas[hoja]
    corte_rotulo = leer_corte(df)
    if corte_rotulo != libro.corte:
        raise EstructuraError(
            f"{libro.serie} {hoja}: el rótulo dice {corte_rotulo} y el archivo es {libro.corte}"
        )
    if hoja in HOJAS_ESTADOS:
        return extraer_bloques(libro, hoja, df)
    return extraer_matriz(libro, hoja, df)


# --------------------------------------------------------------------------------------
# Proceso completo
# --------------------------------------------------------------------------------------


def extraer(dir_raw: Path, dir_interim: Path) -> dict[str, int]:
    """Lee los archivos del manifiesto y escribe las tres tablas largas en dir_interim."""
    registros_manifiesto = leer_manifiesto(dir_raw / "manifest.csv")
    if not registros_manifiesto:
        raise FileNotFoundError(f"No hay manifiesto en {dir_raw}; ejecute primero la descarga")

    todas_las_hojas = HOJAS_ESTADOS + HOJAS_INDICADORES + HOJAS_RIESGOS
    filas: dict[str, list[dict[str, object]]] = {nombre: [] for nombre in SALIDAS}
    for reg in registros_manifiesto.values():
        corte = date.fromisoformat(reg.corte)
        libro = leer_libro(dir_raw / reg.archivo, reg.serie, corte, reg.sha256, todas_las_hojas)
        if reg.serie == "S-367" and set(libro.hojas) != set(todas_las_hojas):
            faltan = sorted(set(todas_las_hojas) - set(libro.hojas))
            raise EstructuraError(f"{reg.archivo}: faltan las hojas {faltan}")
        for hoja in libro.hojas:
            salida = next(n for n, hs in SALIDAS.items() if hoja in hs)
            nuevas = extraer_hoja(libro, hoja)
            filas[salida].extend(nuevas)
            print(f"  {reg.serie} {reg.corte} {hoja}: {len(nuevas):>6} celdas")

    dir_interim.mkdir(parents=True, exist_ok=True)
    conteo: dict[str, int] = {}
    for nombre, datos in filas.items():
        tabla = pd.DataFrame(datos, columns=COLUMNAS)
        llave = ["serie", "corte", "hoja", "fila", "columna"]
        if tabla.duplicated(llave).any():
            raise EstructuraError(f"{nombre}: hay celdas duplicadas por {llave}")
        tabla = tabla.sort_values(llave, kind="stable")
        tabla.to_csv(dir_interim / nombre, index=False, encoding="utf-8", lineterminator="\n")
        conteo[nombre] = len(tabla)
    return conteo
