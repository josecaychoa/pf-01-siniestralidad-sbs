"""Pruebas de la carga en Oracle sin base de datos (paquete 2.3)."""

import re
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from pf_01_siniestralidad_sbs.carga import (
    COLUMNAS_STG,
    a_booleano,
    a_s_n,
    dividir_sentencias,
    dsn_de,
    filas_dim_columna_empresa,
    filas_dim_corte,
    filas_dim_riesgo,
    leer_csv_stg,
    leer_env,
)
from pf_01_siniestralidad_sbs.validacion import leer_catalogo, normalizar

DIR_SQL = Path(__file__).resolve().parents[1] / "sql" / "oracle"

# --------------------------------------------------------------------------------------
# Traducción S/N y catálogos
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(("valor", "codigo"), [("true", "S"), ("false", "N")])
def test_a_s_n(valor, codigo):
    assert a_s_n(valor) == codigo


@pytest.mark.parametrize("valor", ["True", "S", "", "1"])
def test_a_s_n_rechaza_otros_valores(valor):
    with pytest.raises(ValueError):
        a_s_n(valor)


def test_columnas_de_empresa_del_catalogo():
    filas = filas_dim_columna_empresa(leer_catalogo("empresas").to_dict("records"))
    assert [f[0] for f in filas] == list(range(1, len(filas) + 1))
    assert {f[4] for f in filas} == {"empresa"}
    assert {f[7] for f in filas} == {"S", "N"}
    mapfre_abs = next(f for f in filas if f[1] == "MAPFRE PERU (ABS)")
    assert mapfre_abs[7] == "N" and mapfre_abs[10] == "MAPFRE"


def test_riesgos_con_el_padre_antes_que_los_hijos():
    filas = filas_dim_riesgo(leer_catalogo("riesgos").to_dict("records"))
    vistos: set[int] = set()
    for riesgo_id, *_, padre in filas:
        assert padre is None or padre in vistos
        vistos.add(riesgo_id)
    assert filas[0][1] == "TOTAL" and filas[0][9] is None


def test_cortes_sin_resolucion_antes_de_2021():
    filas = filas_dim_corte(leer_catalogo("cortes").to_dict("records"))
    assert filas[0] == (date(2019, 12, 31), 12, "Anterior a la Resolución SBS N.º 976-2021", None)
    assert filas[-1][3] == "085-2026"


# --------------------------------------------------------------------------------------
# Normalización: 03_carga_modelo.sql aplica la regla de validacion.normalizar()
# --------------------------------------------------------------------------------------


def traduccion_sql() -> tuple[str, str]:
    texto = (DIR_SQL / "03_carga_modelo.sql").read_text(encoding="utf-8")
    pares = set(re.findall(r"TRANSLATE\(\w+\.\w+,\s*'([^']+)',\s*'([^']+)'\)", texto))
    assert len(pares) == 1, "todas las sentencias deben usar la misma traducción"
    return pares.pop()


def normalizar_como_sql(texto: str) -> str:
    """TRIM(REGEXP_REPLACE(UPPER(TRANSLATE(...)), '[[:space:]]+', ' ')) en Python."""
    origen, destino = traduccion_sql()
    return " ".join(texto.translate(str.maketrans(origen, destino)).upper().split())


def test_traduccion_sql_letra_por_letra():
    origen, destino = traduccion_sql()
    assert len(origen) == len(destino)
    for con_tilde, sin_tilde in zip(origen, destino, strict=True):
        assert normalizar(con_tilde) == sin_tilde.upper()


@pytest.mark.parametrize("texto", ["Rímac ", "Mapfre Perú  (abs)", "Compañía", "Quálitas"])
def test_normalizacion_sql_igual_a_python(texto):
    assert normalizar_como_sql(texto) == normalizar(texto)


def test_normalizacion_sql_cubre_los_catalogos():
    rotulos = [
        *leer_catalogo("riesgos")["riesgo"],
        *leer_catalogo("empresas")["entidad"],
        *leer_catalogo("empresas")["empresa"],
    ]
    for rotulo in rotulos:
        assert normalizar_como_sql(rotulo) == normalizar(rotulo), rotulo


# --------------------------------------------------------------------------------------
# Lectura de los CSV de data/interim
# --------------------------------------------------------------------------------------


def escribir_csv(ruta: Path, encabezado: str, *filas: str) -> Path:
    ruta.write_text("\n".join([encabezado, *filas]) + "\n", encoding="utf-8")
    return ruta


def test_leer_csv_stg_convierte_los_tipos(tmp_path):
    fila = (
        "S-367,2026-08-31,P004,Indicadores,,DE SOLVENCIA,12,3,Endeudamiento 1/,Endeudamiento,"
        "2,1/,Rímac,Rímac,,False,,1.5e-05,abc123"
    )
    ruta = escribir_csv(tmp_path / "indicadores.csv", ",".join(COLUMNAS_STG), fila)
    (registro,) = leer_csv_stg(ruta)
    assert len(registro) == len(COLUMNAS_STG)
    assert registro[1] == date(2026, 8, 31)
    assert registro[4] is None and registro[16] is None  # unidad y moneda vacías
    assert registro[5] == "DE SOLVENCIA"
    assert (registro[6], registro[7], registro[10]) == (12, 3, 2)
    assert registro[15] is False
    assert registro[17] == Decimal("1.5e-05")  # sin pasar por float (D-PF01-06)


def test_leer_csv_stg_exige_las_columnas_del_diccionario(tmp_path):
    ruta = escribir_csv(tmp_path / "riesgos.csv", "serie,corte,valor", "S-367,2026-08-31,1")
    with pytest.raises(ValueError, match="columnas"):
        leer_csv_stg(ruta)


@pytest.mark.parametrize(("texto", "valor"), [("True", True), ("False", False)])
def test_a_booleano(texto, valor):
    assert a_booleano(texto) is valor


def test_a_booleano_rechaza_otros_valores():
    with pytest.raises(ValueError):
        a_booleano("true")


# --------------------------------------------------------------------------------------
# Ejecución de scripts SQL y conexión
# --------------------------------------------------------------------------------------


def test_dividir_sentencias():
    texto = "\n".join(
        [
            "-- comentario",
            "WHENEVER SQLERROR EXIT FAILURE",
            "PROMPT == Paso 1 ==",
            "CREATE TABLE IF NOT EXISTS t (",
            "    a NUMBER  -- comentario dentro de la sentencia",
            ");",
            "DECLARE",
            "    v NUMBER;",
            "BEGIN",
            "    v := 1;",
            "END;",
            "/",
            "COMMIT;",
        ]
    )
    sentencias = dividir_sentencias(texto)
    assert [s.tipo for s in sentencias] == ["prompt", "sql", "plsql", "sql"]
    assert sentencias[0].texto == "== Paso 1 =="
    assert sentencias[1].linea == 4 and sentencias[1].texto.endswith(")")
    assert sentencias[2].texto.splitlines()[-1] == "END;"
    assert sentencias[3].texto == "COMMIT"


def test_dividir_sentencias_detecta_un_bloque_sin_terminar():
    with pytest.raises(ValueError, match="línea 1"):
        dividir_sentencias("BEGIN\n    NULL;\nEND;\n")


@pytest.mark.parametrize("script", ["01_ddl_tablas.sql", "02_vistas.sql", "03_carga_modelo.sql"])
def test_scripts_del_repositorio_se_dividen(script):
    sentencias = dividir_sentencias((DIR_SQL / script).read_text(encoding="utf-8"))
    assert any(s.tipo == "sql" for s in sentencias)
    for s in sentencias:
        if s.tipo == "plsql":
            assert s.texto.rstrip().endswith("END;")
        if s.tipo == "sql":
            assert not s.texto.rstrip().endswith(";")


def test_leer_env(tmp_path):
    ruta = tmp_path / ".env"
    ruta.write_text(
        "# comentario\nORACLE_USER=pf01\nORACLE_DSN='localhost:1522/FREEPDB1'\n\nVACIA=\n",
        encoding="utf-8",
    )
    assert leer_env(ruta) == {
        "ORACLE_USER": "pf01",
        "ORACLE_DSN": "localhost:1522/FREEPDB1",
        "VACIA": "",
    }


def test_dsn_nativa_por_defecto_y_contenedor_desde_el_entorno():
    entorno = {"ORACLE_DSN": "localhost:1522/FREEPDB1"}
    assert dsn_de("nativa", entorno) == "localhost:1521/FREEPDB1"
    assert dsn_de("contenedor", entorno) == "localhost:1522/FREEPDB1"
    with pytest.raises(ValueError):
        dsn_de("otra", {})
