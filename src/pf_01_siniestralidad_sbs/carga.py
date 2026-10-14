"""Carga del modelo de datos en Oracle (paquete 2.3 de la EDT).

Pasos (scripts/cargar_oracle.py):
1. sql/oracle/01_ddl_tablas.sql y 02_vistas.sql, idempotentes.
2. Tablas stg_: copia de data/interim/*.csv. Cada carga vacía las tablas y las vuelve a llenar.
3. Dimensiones de catálogo (dim_empresa, dim_corte, dim_riesgo y las columnas de empresa de
   dim_columna_empresa) desde src/pf_01_siniestralidad_sbs/catalogos/.
4. sql/oracle/03_carga_modelo.sql: dimensiones que salen de stg_ y tablas de hechos.

Los pasos 3 y 4 forman una sola transacción: 03_carga_modelo.sql la confirma al final y, si
falla, se deshace también el paso 3. Conexión con python-oracledb en modo Thin; usuario y
contraseña desde el entorno o desde .env, nunca impresos. Base nativa por defecto (D-PF01-03).
"""

from __future__ import annotations

import csv
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

import oracledb

from pf_01_siniestralidad_sbs.validacion import leer_catalogo

DSN_NATIVA = "localhost:1521/FREEPDB1"  # D-PF01-03; el contenedor usa ORACLE_DSN de .env
TAMANO_LOTE = 20_000

# Tablas stg_: archivo de data/interim -> tabla. Columnas en el orden del CSV y del DDL.
TABLAS_STG = {
    "estados_financieros": "stg_estados_financieros",
    "indicadores": "stg_indicadores",
    "riesgos": "stg_riesgos",
}
COLUMNAS_STG = (
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
)
# Tipos de enlace para executemany: un entero es la longitud máxima de un texto.
TIPOS_STG = (
    10,
    oracledb.DB_TYPE_DATE,
    4,
    150,
    30,
    100,
    oracledb.DB_TYPE_NUMBER,
    oracledb.DB_TYPE_NUMBER,
    200,
    200,
    oracledb.DB_TYPE_NUMBER,
    30,
    150,
    150,
    30,
    oracledb.DB_TYPE_BOOLEAN,
    5,
    oracledb.DB_TYPE_NUMBER,
    64,
)
TEXTOS_OPCIONALES = {"unidad", "seccion", "llamadas_concepto", "llamadas_empresa", "moneda"}

# Orden de borrado: primero los hechos, después las dimensiones que ellos referencian.
BORRADO_CATALOGOS = (
    "fct_estado_financiero",
    "fct_indicador",
    "fct_riesgo",
    "dim_columna_empresa",
    "dim_empresa",
    "dim_riesgo",
    "dim_corte",
)


class EjecucionSQLError(RuntimeError):
    """Una sentencia de un script SQL falló; el mensaje incluye el archivo y la línea."""


# --------------------------------------------------------------------------------------
# Conexión
# --------------------------------------------------------------------------------------


def leer_env(ruta: Path) -> dict[str, str]:
    """Variables CLAVE=valor de un archivo .env; ignora líneas vacías y comentarios."""
    variables = {}
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            clave, valor = linea.split("=", 1)
            variables[clave.strip()] = valor.strip().strip("'\"")
    return variables


def dsn_de(base: str, entorno: Mapping[str, str]) -> str:
    """DSN de la base: «nativa» (por defecto, D-PF01-03) o «contenedor» (ORACLE_DSN)."""
    if base == "nativa":
        return DSN_NATIVA
    if base == "contenedor":
        return entorno["ORACLE_DSN"]
    raise ValueError(f"base desconocida: {base!r} (nativa o contenedor)")


def conectar(ruta_env: Path, base: str = "nativa", dsn: str | None = None) -> oracledb.Connection:
    """Conexión en modo Thin. Las variables del entorno tienen prioridad sobre .env."""
    entorno = {**(leer_env(ruta_env) if ruta_env.exists() else {}), **os.environ}
    conexion = oracledb.connect(
        user=entorno["ORACLE_USER"],
        password=entorno["ORACLE_PASSWORD"],
        dsn=dsn or dsn_de(base, entorno),
    )
    if not oracledb.is_thin_mode():
        raise RuntimeError("python-oracledb no está en modo Thin")
    return conexion


# --------------------------------------------------------------------------------------
# Ejecución de scripts SQL
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Sentencia:
    """Una sentencia de un script: línea de inicio, tipo (sql, plsql o prompt) y texto."""

    linea: int
    tipo: str
    texto: str


def dividir_sentencias(texto: str) -> list[Sentencia]:
    """Separa un script con la convención de SQL*Plus y SQLcl.

    Un bloque que empieza con DECLARE o BEGIN termina en una línea con «/»; cualquier otra
    sentencia termina en «;» al final de una línea. PROMPT se conserva para mostrarlo;
    WHENEVER y SET se ignoran. Los comentarios entre sentencias se descartan.
    """
    sentencias: list[Sentencia] = []
    buffer: list[str] = []
    inicio, plsql = 0, False
    for numero, linea in enumerate(texto.splitlines(), start=1):
        limpia = linea.strip()
        if not buffer:
            if not limpia or limpia.startswith("--"):
                continue
            mayusculas = limpia.upper()
            if mayusculas.startswith("PROMPT"):
                sentencias.append(Sentencia(numero, "prompt", limpia[6:].strip()))
                continue
            if mayusculas.startswith(("WHENEVER", "SET ")):
                continue
            inicio, plsql = numero, mayusculas.startswith(("DECLARE", "BEGIN"))
        if plsql and limpia == "/":
            sentencias.append(Sentencia(inicio, "plsql", "\n".join(buffer)))
            buffer = []
            continue
        buffer.append(linea)
        if not plsql and limpia.endswith(";"):
            sentencias.append(Sentencia(inicio, "sql", "\n".join(buffer).rstrip().rstrip(";")))
            buffer = []
    if buffer:
        raise ValueError(f"Sentencia sin terminar desde la línea {inicio}")
    return sentencias


def ejecutar_script(
    conexion: oracledb.Connection, ruta: Path, mostrar: Callable[[str], None] = print
) -> int:
    """Ejecuta las sentencias de un script en orden y devuelve cuántas ejecutó.

    Ante un error deshace la transacción en curso y lanza EjecucionSQLError con el mensaje
    de Oracle.
    """
    cursor = conexion.cursor()
    ejecutadas = 0
    for sentencia in dividir_sentencias(ruta.read_text(encoding="utf-8")):
        if sentencia.tipo == "prompt":
            mostrar(f"    {sentencia.texto}")
            continue
        try:
            cursor.execute(sentencia.texto)
        except oracledb.DatabaseError as error:
            conexion.rollback()
            primera = sentencia.texto.strip().splitlines()[0]
            mensaje = f"{ruta.name}, línea {sentencia.linea} ({primera}): {error}"
            raise EjecucionSQLError(mensaje) from error
        ejecutadas += 1
    return ejecutadas


# --------------------------------------------------------------------------------------
# Tablas stg_
# --------------------------------------------------------------------------------------


def a_booleano(texto: str) -> bool:
    """es_total del CSV (True o False, como lo escribe pandas) a bool."""
    if texto not in ("True", "False"):
        raise ValueError(f"es_total debe ser True o False, no {texto!r}")
    return texto == "True"


def convertir_fila(fila: Mapping[str, str]) -> tuple[object, ...]:
    """Fila del CSV con los tipos de la tabla stg_; el texto vacío opcional pasa a NULL."""
    enteros = {"fila", "columna", "sangria"}
    valores: list[object] = []
    for columna in COLUMNAS_STG:
        texto = fila[columna]
        if columna == "corte":
            valores.append(date.fromisoformat(texto))
        elif columna in enteros:
            valores.append(int(texto))
        elif columna == "es_total":
            valores.append(a_booleano(texto))
        elif columna == "valor":
            valores.append(Decimal(texto))  # la cifra publicada, sin pasar por float (D-PF01-06)
        elif columna in TEXTOS_OPCIONALES:
            valores.append(texto or None)
        else:
            valores.append(texto)
    return tuple(valores)


def leer_csv_stg(ruta: Path) -> list[tuple[object, ...]]:
    """Lee un CSV de data/interim y comprueba que tenga las columnas del diccionario."""
    with ruta.open(encoding="utf-8", newline="") as archivo:
        lector = csv.DictReader(archivo)
        if tuple(lector.fieldnames or ()) != COLUMNAS_STG:
            raise ValueError(f"{ruta.name}: columnas distintas de las del diccionario de datos")
        return [convertir_fila(fila) for fila in lector]


def cargar_stg(
    conexion: oracledb.Connection, dir_interim: Path, lote: int = TAMANO_LOTE
) -> dict[str, int]:
    """Vacía y vuelve a llenar las tres tablas stg_ (la carga reemplaza, no acumula).

    Después de cada tabla reúne sus estadísticas del optimizador: sin ellas, Oracle muestrea
    las tablas en cada sentencia de 03_carga_modelo.sql y la carga tarda varios minutos.
    """
    cursor = conexion.cursor()
    marcadores = ", ".join(f":{i}" for i in range(1, len(COLUMNAS_STG) + 1))
    conteo = {}
    for nombre, tabla in TABLAS_STG.items():
        filas = leer_csv_stg(dir_interim / f"{nombre}.csv")
        cursor.execute(f"TRUNCATE TABLE {tabla}")
        insercion = f"INSERT INTO {tabla} ({', '.join(COLUMNAS_STG)}) VALUES ({marcadores})"
        for desde in range(0, len(filas), lote):
            cursor.setinputsizes(*TIPOS_STG)
            cursor.executemany(insercion, filas[desde : desde + lote])
        conexion.commit()
        cursor.execute(
            "BEGIN DBMS_STATS.GATHER_TABLE_STATS(ownname => USER, tabname => :tabla); END;",
            tabla=tabla.upper(),
        )
        conteo[tabla] = len(filas)
    return conteo


# --------------------------------------------------------------------------------------
# Dimensiones de catálogo
# --------------------------------------------------------------------------------------


def a_s_n(valor: str) -> str:
    """en_total_simple del catálogo (true o false) a la codificación S o N (D-PF01-07)."""
    codigos = {"true": "S", "false": "N"}
    if valor not in codigos:
        raise ValueError(f"en_total_simple debe ser true o false, no {valor!r}")
    return codigos[valor]


def filas_dim_empresa(empresas: list[dict[str, str]]) -> list[tuple[str, str]]:
    """Una fila por empresa_id; exige una sola denominación por empresa."""
    nombres: dict[str, str] = {}
    for fila in empresas:
        anterior = nombres.setdefault(fila["empresa_id"], fila["empresa"])
        if anterior != fila["empresa"]:
            raise ValueError(f"{fila['empresa_id']}: dos denominaciones en empresas.csv")
    return list(nombres.items())


def filas_dim_corte(cortes: list[dict[str, str]]) -> list[tuple[object, ...]]:
    """fecha_corte, meses_acumulados, plan_de_cuentas y resolucion_plan (nula antes de 2021)."""
    return [
        (
            date.fromisoformat(f["corte"]),
            int(f["meses_acumulados"]),
            f["plan_de_cuentas"],
            f["texto_de_la_nota"] or None,
        )
        for f in cortes
    ]


def filas_dim_riesgo(riesgos: list[dict[str, str]]) -> list[tuple[object, ...]]:
    """Filas de dim_riesgo con riesgo_padre_id; los padres van antes que los hijos."""
    ids = {f["clave"]: int(f["riesgo_id"]) for f in riesgos}
    filas = [
        (
            int(f["riesgo_id"]),
            f["clave"],
            f["riesgo"],
            int(f["nivel"]),
            f["tipo"],
            f["ramo"] or None,
            f["riesgo_comparable"],
            date.fromisoformat(f["corte_desde"]),
            f["nota"] or None,
            ids[f["clave_padre"]] if f["clave_padre"] else None,
        )
        for f in riesgos
    ]
    return sorted(filas, key=lambda fila: (fila[3], fila[0]))


def filas_dim_columna_empresa(empresas: list[dict[str, str]]) -> list[tuple[object, ...]]:
    """Columnas de empresa del catálogo, con columna_id en el orden de empresas.csv.

    Las columnas Total no están en el catálogo: las agrega 03_carga_modelo.sql.
    """
    return [
        (
            numero,
            f["clave_fuente"],
            date.fromisoformat(f["corte_desde"]),
            date.fromisoformat(f["corte_hasta"]),
            "empresa",
            f["entidad"] or None,
            f["estado"] or None,
            a_s_n(f["en_total_simple"]),
            f["evento"] or None,
            f["fuente_evento"] or None,
            f["empresa_id"],
        )
        for numero, f in enumerate(empresas, start=1)
    ]


def cargar_catalogos(conexion: oracledb.Connection) -> dict[str, int]:
    """Reemplaza las dimensiones de catálogo; no confirma la transacción.

    Borra antes los hechos, que las referencian. 03_carga_modelo.sql los vuelve a llenar y
    confirma todo junto; si no se ejecuta, la transacción debe deshacerse.
    """
    empresas = leer_catalogo("empresas").to_dict("records")
    numero, fecha = oracledb.DB_TYPE_NUMBER, oracledb.DB_TYPE_DATE
    # Tabla: (inserción, tipos de enlace, filas). Los tipos se fijan porque la primera fila
    # puede traer nulos (p. ej., el riesgo TOTAL no tiene ramo ni padre).
    tablas = {
        "dim_empresa": (
            "INSERT INTO dim_empresa (empresa_id, empresa) VALUES (:1, :2)",
            (30, 100),
            filas_dim_empresa(empresas),
        ),
        "dim_corte": (
            "INSERT INTO dim_corte (fecha_corte, meses_acumulados, plan_de_cuentas, "
            "resolucion_plan) VALUES (:1, :2, :3, :4)",
            (fecha, numero, 100, 20),
            filas_dim_corte(leer_catalogo("cortes").to_dict("records")),
        ),
        "dim_riesgo": (
            "INSERT INTO dim_riesgo (riesgo_id, clave, riesgo, nivel, tipo, ramo, "
            "riesgo_comparable, corte_desde, nota, riesgo_padre_id) "
            "VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10)",
            (numero, 80, 100, numero, 10, 50, 100, fecha, 400, numero),
            filas_dim_riesgo(leer_catalogo("riesgos").to_dict("records")),
        ),
        "dim_columna_empresa": (
            "INSERT INTO dim_columna_empresa (columna_id, clave_fuente, corte_desde, "
            "corte_hasta, tipo_columna, entidad, estado, en_total_simple, evento, "
            "fuente_evento, empresa_id) VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10, :11)",
            (numero, 120, fecha, fecha, 15, 150, 10, 1, 200, 200, 30),
            filas_dim_columna_empresa(empresas),
        ),
    }
    cursor = conexion.cursor()
    for tabla in BORRADO_CATALOGOS:
        cursor.execute(f"DELETE FROM {tabla}")
    for insercion, tipos, filas in tablas.values():
        cursor.setinputsizes(*tipos)
        cursor.executemany(insercion, filas)
    return {tabla: len(filas) for tabla, (_, _, filas) in tablas.items()}
