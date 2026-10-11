"""Validación de las tablas largas de data/interim (paquete 2.2 de la EDT).

Controles (criterio de aceptación del issue #5 y decisión D-PF01-01):
1. Estructura por corte: 12 hojas por corte, empresas y riesgos reconocidos por los catálogos.
2. Cuadre con los totales publicados (tolerancia: 1 mil soles):
   - total simple: suma de las empresas en operación al corte = columna «Total»;
   - total ampliado: suma de todas las columnas de empresa = columna «Total + …».
3. Jerarquía de riesgos: cada agregado = suma de sus componentes (catálogo de riesgos).
4. Estado de situación financiera: Activo = Pasivo + Patrimonio por empresa y moneda.
5. Consistencia del Boletín Mensual con los cuadros S-401, S-402 y S-403 de agosto de 2026.
6. Cifras acumuladas en el año: la razón diciembre / agosto de 2025 se acerca a 12 / 8.
7. Plan de cuentas: la nota al pie de P001 corresponde a la versión registrada para el corte.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

import pandas as pd

TOLERANCIA = 1.0  # mil soles: redondeo de las cifras publicadas (acta, objetivo O1)
TABLAS = ("estados_financieros", "indicadores", "riesgos")
TOTALES_SIMPLES = {"TOTAL", "TOTAL EMPRESAS DE SEGUROS"}
HOJAS_CON_TOTAL = ("P001", "P002", "P003", "P009", "P010", "P011", "P012", "P013", "P014")
HOJAS_RIESGOS_MONTOS = ("P009", "P010", "P011", "P012", "P013", "P014")
HOJAS_RIESGOS = HOJAS_RIESGOS_MONTOS + ("P015", "P016")


@dataclass(frozen=True)
class Resultado:
    """Resultado de un control: nombre, celdas revisadas, fallas y detalle de las fallas."""

    control: str
    revisados: int
    fallas: int
    detalle: pd.DataFrame
    excepciones: int = 0  # diferencias de la fuente ya documentadas en catalogos/excepciones.csv

    @property
    def ok(self) -> bool:
        return self.fallas == 0


def normalizar(texto: str) -> str:
    """Clave de comparación: mayúsculas, sin tildes y sin espacios repetidos."""
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )
    return " ".join(sin_tildes.upper().split())


# --------------------------------------------------------------------------------------
# Catálogos y carga
# --------------------------------------------------------------------------------------


def leer_catalogo(nombre: str) -> pd.DataFrame:
    """Lee un catálogo versionado del paquete (empresas, riesgos o cortes)."""
    ruta = resources.files("pf_01_siniestralidad_sbs") / "catalogos" / f"{nombre}.csv"
    with ruta.open(encoding="utf-8") as f:
        return pd.read_csv(f, dtype=str, keep_default_na=False)


def leer_interim(dir_interim: Path) -> dict[str, pd.DataFrame]:
    """Lee las tres tablas largas con las columnas de texto como texto."""
    tipos = {c: str for c in ("llamadas_concepto", "llamadas_empresa", "seccion", "moneda")}
    tablas = {}
    for nombre in TABLAS:
        df = pd.read_csv(dir_interim / f"{nombre}.csv", dtype=tipos, keep_default_na=False)
        df["valor"] = df["valor"].astype(float)
        tablas[nombre] = df
    return tablas


def tipo_total(empresa: str) -> str:
    """'simple', 'ampliado' o '' según el encabezado de la columna."""
    clave = normalizar(empresa)
    if clave in TOTALES_SIMPLES:
        return "simple"
    if clave.startswith("TOTAL +"):
        return "ampliado"
    return ""


def asignar_empresas(df: pd.DataFrame, catalogo: pd.DataFrame) -> pd.DataFrame:
    """Agrega empresa_id, empresa canónica, estado y en_total_simple según el catálogo.

    Las columnas de total no se asignan. Una columna de empresa sin equivalencia, o con más
    de una, queda con empresa_id vacío y se informa en validar_estructura.
    """
    salida = df.copy()
    salida["clave_empresa"] = salida["empresa"].map(normalizar)
    salida["tipo_total"] = salida["empresa"].map(tipo_total)
    cat = catalogo.rename(columns={"empresa": "empresa_canonica"})
    llaves = salida.loc[salida["tipo_total"] == "", ["clave_empresa", "corte"]].drop_duplicates()
    cruce = llaves.merge(cat, left_on="clave_empresa", right_on="clave_fuente", how="left")
    vigente = (cruce["corte"] >= cruce["corte_desde"]) & (cruce["corte"] <= cruce["corte_hasta"])
    cruce = cruce[vigente]
    unicos = cruce[~cruce.duplicated(["clave_empresa", "corte"], keep=False)]
    columnas = ["empresa_id", "empresa_canonica", "estado", "en_total_simple"]
    return salida.merge(
        unicos[["clave_empresa", "corte", *columnas]], on=["clave_empresa", "corte"], how="left"
    ).fillna({c: "" for c in columnas})


# --------------------------------------------------------------------------------------
# Controles
# --------------------------------------------------------------------------------------


def validar_estructura(tablas: dict[str, pd.DataFrame], cortes: pd.DataFrame) -> Resultado:
    """12 hojas por corte del Boletín, empresas y riesgos reconocidos por los catálogos."""
    todas = pd.concat(tablas.values(), ignore_index=True)
    fallas: list[dict[str, object]] = []

    boletin = todas[todas["serie"] == "S-367"]
    hojas = boletin.groupby("corte")["hoja"].nunique()
    for corte in cortes["corte"]:
        if hojas.get(corte, 0) != 12:
            fallas.append({"tipo": "hojas", "corte": corte, "valor": hojas.get(corte, 0)})

    empresas = asignar_empresas(todas, leer_catalogo("empresas"))
    sin_par = empresas[(empresas["tipo_total"] == "") & (empresas["empresa_id"] == "")]
    for (corte, empresa), _ in sin_par.groupby(["corte", "empresa"]):
        fallas.append({"tipo": "empresa sin equivalencia", "corte": corte, "valor": empresa})

    riesgos = tablas["riesgos"]
    claves = set(leer_catalogo("riesgos")["clave"])
    desconocidos = riesgos[~riesgos["concepto"].map(normalizar).isin(claves)]
    for (corte, concepto), _ in desconocidos.groupby(["corte", "concepto"]):
        fallas.append({"tipo": "riesgo fuera del catálogo", "corte": corte, "valor": concepto})

    revisados = len(cortes) + empresas["clave_empresa"].nunique() + len(riesgos)
    return Resultado("Estructura por corte", revisados, len(fallas), pd.DataFrame(fallas))


def cuadre_totales(df: pd.DataFrame, hojas: tuple[str, ...] = HOJAS_CON_TOTAL) -> Resultado:
    """Doble control D-PF01-01 por fila: total simple y, si existe, total ampliado."""
    d = asignar_empresas(df[df["hoja"].isin(hojas)], leer_catalogo("empresas"))
    llave = ["serie", "corte", "hoja", "fila", "moneda"]
    empresas = d[d["tipo_total"] == ""]
    suma_simple = empresas[empresas["en_total_simple"] == "true"].groupby(llave)["valor"].sum()
    suma_todas = empresas.groupby(llave)["valor"].sum()

    partes = []
    for tipo, suma in (("simple", suma_simple), ("ampliado", suma_todas)):
        total = d[d["tipo_total"] == tipo].groupby(llave)["valor"].sum()
        tabla = pd.concat([suma.rename("suma_empresas"), total.rename("total_publicado")], axis=1)
        tabla = tabla.dropna(subset=["total_publicado"]).fillna({"suma_empresas": 0.0})
        tabla["control"] = tipo
        partes.append(tabla.reset_index())
    detalle = pd.concat(partes, ignore_index=True)
    detalle["diferencia"] = detalle["suma_empresas"] - detalle["total_publicado"]
    fallas = detalle[detalle["diferencia"].abs() > TOLERANCIA]
    return Resultado("Cuadre con los totales publicados", len(detalle), len(fallas), fallas)


def jerarquia_riesgos(riesgos: pd.DataFrame) -> Resultado:
    """Cada agregado del catálogo es la suma de sus componentes, en cada columna de P009 a P014."""
    catalogo = leer_catalogo("riesgos")
    hijos = catalogo[catalogo["tipo"].isin(["agregado", "riesgo"])]
    d = riesgos[riesgos["hoja"].isin(HOJAS_RIESGOS_MONTOS)].assign(
        clave=lambda x: x["concepto"].map(normalizar)
    )
    llave = ["serie", "corte", "hoja", "columna"]
    valores = d.set_index([*llave, "clave"])["valor"]
    partes = []
    for padre in catalogo.loc[catalogo["tipo"].isin(["total", "agregado"]), "clave"]:
        componentes = set(hijos.loc[hijos["clave_padre"] == padre, "clave"])
        suma = d[d["clave"].isin(componentes)].groupby(llave)["valor"].sum()
        publicado = valores.xs(padre, level="clave")
        tabla = pd.concat([suma.rename("suma_componentes"), publicado.rename("publicado")], axis=1)
        tabla = tabla.fillna(0.0).assign(agregado=padre).reset_index()
        partes.append(tabla)
    detalle = pd.concat(partes, ignore_index=True)
    detalle["diferencia"] = detalle["suma_componentes"] - detalle["publicado"]
    fallas = detalle[detalle["diferencia"].abs() > TOLERANCIA]
    return Resultado("Jerarquía de riesgos", len(detalle), len(fallas), fallas)


def balance(estados: pd.DataFrame) -> Resultado:
    """Activo = Pasivo + Patrimonio por corte y empresa (hoja P001, moneda TOTAL).

    También verifica Pasivo + Patrimonio = «Total pasivo y patrimonio» en MN, ME y TOTAL. La
    igualdad Activo = Pasivo + Patrimonio no se exige por moneda: el patrimonio se presenta
    en moneda nacional y los activos y pasivos en ambas monedas.
    """
    d = estados[estados["hoja"] == "P001"].assign(clave=lambda x: x["concepto"].map(normalizar))
    llave = ["corte", "columna", "empresa", "moneda"]
    rubros = {
        "activo": "TOTAL ACTIVO",
        "pasivo": "TOTAL PASIVO",
        "patrimonio": "PATRIMONIO",
        "pasivo_y_patrimonio": "TOTAL PASIVO Y PATRIMONIO",
    }
    detalle = pd.concat(
        [d[d["clave"] == clave].set_index(llave)["valor"].rename(n) for n, clave in rubros.items()],
        axis=1,
    ).reset_index()
    detalle["dif_suma"] = detalle["pasivo"] + detalle["patrimonio"] - detalle["pasivo_y_patrimonio"]
    detalle["dif_activo"] = (detalle["activo"] - detalle["pasivo_y_patrimonio"]).where(
        detalle["moneda"] == "TOTAL", 0.0
    )
    malas = detalle[["dif_activo", "dif_suma"]].abs().gt(TOLERANCIA).any(axis=1) | detalle[
        list(rubros)
    ].isna().any(axis=1)
    return Resultado("Activo = Pasivo + Patrimonio", len(detalle), int(malas.sum()), detalle[malas])


def monedas(estados: pd.DataFrame) -> Resultado:
    """MN + ME = TOTAL en cada fila y empresa de P001 y P002 (control de la extracción).

    Se excluyen las filas de utilidad por acción, que están en soles por acción y no se
    desagregan por moneda. Las diferencias de la fuente documentadas en
    catalogos/excepciones.csv se informan como excepciones y no como fallas.
    """
    d = estados[~estados["concepto"].map(normalizar).str.contains("POR ACCION")]
    d = d.assign(concepto_n=d["concepto"].map(normalizar), empresa_n=d["empresa"].map(normalizar))
    llave = ["corte", "hoja", "fila", "concepto_n", "empresa_n"]
    p = d.pivot_table(index=llave, columns="moneda", values="valor", aggfunc="sum")
    p = p[p["TOTAL"].notna()].fillna({"MN": 0.0, "ME": 0.0})
    p["diferencia"] = p["MN"] + p["ME"] - p["TOTAL"]
    difieren = p[p["diferencia"].abs() > TOLERANCIA].reset_index()
    excepciones = leer_catalogo("excepciones")
    excepciones = excepciones[excepciones["control"] == "MN + ME = TOTAL"]
    marcadas = difieren.merge(
        excepciones.rename(columns={"concepto": "concepto_n", "empresa": "empresa_n"}),
        on=["corte", "hoja", "concepto_n", "empresa_n"],
        how="left",
    )
    es_excepcion = marcadas["observacion"].notna()
    return Resultado(
        "MN + ME = TOTAL",
        len(p),
        int((~es_excepcion).sum()),
        marcadas,
        excepciones=int(es_excepcion.sum()),
    )


def consistencia_cuadros(riesgos: pd.DataFrame) -> Resultado:
    """P009 a P016 del Boletín de agosto de 2026 frente a los cuadros S-401, S-402 y S-403."""
    clave = ["corte", "hoja", "fila", "columna"]
    boletin = riesgos[riesgos["serie"] == "S-367"].set_index(clave)["valor"]
    cuadros = riesgos[riesgos["serie"] != "S-367"].set_index(clave)["valor"]
    detalle = pd.concat([cuadros.rename("cuadro"), boletin.rename("boletin")], axis=1, join="inner")
    detalle = detalle.reset_index()
    faltan = len(cuadros) - len(detalle)
    detalle["diferencia"] = detalle["boletin"] - detalle["cuadro"]
    fallas = detalle[detalle["diferencia"].abs() > 0]
    return Resultado(
        "Boletín frente a S-401, S-402 y S-403", len(cuadros), len(fallas) + faltan, fallas
    )


def cifras_acumuladas(tablas: dict[str, pd.DataFrame], cortes: pd.DataFrame) -> Resultado:
    """Razón diciembre / agosto de 2025 de los totales de flujo, frente a 12 / 8 meses.

    Si las cifras fueran del mes, la razón rondaría 1; si fueran anualizadas, también. Con
    cifras acumuladas en el año ronda 1.5. Se acepta el intervalo de 1.3 a 1.7.
    """
    meses = cortes.set_index("corte")["meses_acumulados"].astype(int)
    esperado = meses["2025-12-31"] / meses["2025-08-31"]
    series = {
        "Primas netas (P009)": ("riesgos", "P009", "TOTAL", ""),
        "Siniestros netos (P012)": ("riesgos", "P012", "TOTAL", ""),
        "Primas netas (P002)": ("estados_financieros", "P002", "PRIMAS DE SEGUROS NETAS", "TOTAL"),
    }
    filas = []
    for nombre, (tabla, hoja, concepto, moneda) in series.items():
        d = tablas[tabla]
        d = d[
            (d["serie"] == "S-367")
            & (d["hoja"] == hoja)
            & (d["concepto"].map(normalizar) == concepto)
            & (d["empresa"].map(tipo_total) == "simple")
            & (d["moneda"] == moneda)
        ].set_index("corte")["valor"]
        razon = d["2025-12-31"] / d["2025-08-31"]
        filas.append(
            {
                "serie": nombre,
                "agosto_2025": d["2025-08-31"],
                "diciembre_2025": d["2025-12-31"],
                "razon": razon,
                "razon_esperada": esperado,
                "ok": 1.3 <= razon <= 1.7,
            }
        )
    detalle = pd.DataFrame(filas)
    return Resultado(
        "Cifras acumuladas en el año", len(detalle), int((~detalle["ok"]).sum()), detalle
    )


def plan_de_cuentas(notas: dict[str, str], cortes: pd.DataFrame) -> Resultado:
    """La nota al pie de P001 de cada corte cita la resolución del plan de cuentas registrado.

    notas: texto de las notas al pie de P001 por corte (ver extraccion.notas_al_pie).
    """
    filas = []
    for _, fila in cortes.iterrows():
        texto = notas.get(fila["corte"], "")
        esperado = fila["texto_de_la_nota"]
        # Antes de junio de 2021, la nota no debe citar la resolución de 2021.
        ok = esperado in texto if esperado else "976-2021" not in texto
        filas.append({"corte": fila["corte"], "plan_de_cuentas": fila["plan_de_cuentas"], "ok": ok})
    detalle = pd.DataFrame(filas)
    return Resultado(
        "Versión del plan de cuentas", len(detalle), int((~detalle["ok"]).sum()), detalle
    )


def leer_notas_plan(dir_raw: Path) -> dict[str, str]:
    """Notas al pie de P001 que citan cambios contables, por corte del Boletín Mensual."""
    from datetime import date

    from pf_01_siniestralidad_sbs.descarga import leer_manifiesto
    from pf_01_siniestralidad_sbs.extraccion import es_texto, leer_libro

    notas = {}
    for reg in leer_manifiesto(dir_raw / "manifest.csv").values():
        if reg.serie != "S-367":
            continue
        libro = leer_libro(
            dir_raw / reg.archivo, reg.serie, date.fromisoformat(reg.corte), reg.sha256, ("P001",)
        )
        textos = [str(v) for v in libro.hojas["P001"].iloc[:, 0] if es_texto(v)]
        notas[reg.corte] = " | ".join(t for t in textos if "cambios contables" in t)
    return notas
