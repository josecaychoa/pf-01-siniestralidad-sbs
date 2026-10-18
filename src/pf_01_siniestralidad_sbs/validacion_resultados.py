"""Validación de resultados del análisis (paquete 3.3 de la EDT, issue #9).

Programa en funciones puras sobre marcos de pandas, sin conexión, los controles de la
decisión D-PF01-17 (scripts/validar_resultados.py lee las vistas y escribe la nota):
1. O2 · índice total del sistema en agosto de 2026: 100 × Σ siniestros / Σ primas de las
   filas de vw_indicadores_riesgo del corte frente a la fila Total de P015 y P016.
2. El mismo contraste en los 9 cortes de 2019 a 2026.
3. Índice por riesgo frente al publicado en las filas de un solo riesgo con primas positivas.
4. Cobertura de la matriz (vw_matriz_riesgo) frente a los resultados de 3.2.
5. Primas de la matriz frente al Total publicado de P009 del corte actual.
Los controles 6 (cruce SQL frente a Python) y 7 (casos borde) son pruebas ya escritas que la
nota cita con el resultado de su corrida.

Una diferencia que no se puede calcular (falta el publicado) cuenta como falla.
"""

from __future__ import annotations

from datetime import date

import pandas as pd

from pf_01_siniestralidad_sbs.indicadores import COLUMNAS_MEDIDA, resumen_matriz
from pf_01_siniestralidad_sbs.validacion import Resultado

TOLERANCIA_O2 = 0.1  # puntos porcentuales: objetivo O2 del acta
TOLERANCIA_MILES = 1.0  # miles de soles: redondeo de las cifras publicadas (objetivo O1)
# Resultados de 3.2 (#8): matriz de agosto de 2026 en vw_matriz_riesgo, con la clasificación
# por variación interanual e índice directo (scripts/exportar_indicadores.py).
COBERTURA_ESPERADA = {
    "filas": 48,
    "sobre_umbral": 40,
    "no_comparables": 5,
    "clasificadas": 35,
    "por_cuadrante": {1: 9, 2: 12, 3: 7, 4: 7, None: 13},
}
MEDIDAS = ("directa", "retenida")
MESES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)
NOTA_TABLA = "*Nota.* Elaboración propia con datos de SBS (s. f.-a, s. f.-b, s. f.-c, s. f.-d)."
# Pruebas que la nota cita (controles 6 y 7 de D-PF01-17): nombre, archivo y qué verifica.
PRUEBAS_CITADAS = (
    (
        "test_matriz_indice_calculado_igual_al_publicado",
        "tests/test_vistas_analisis.py",
        "Índice directo calculado frente al publicado en las filas de un riesgo con primas "
        "positivas del corte actual: diferencia máxima menor que 0.1 p. p.",
    ),
    (
        "test_matriz_filas_y_umbral",
        "tests/test_vistas_analisis.py",
        "La matriz tiene 48 filas y 40 sobre el umbral de 5 000 mil soles",
    ),
    (
        "test_matriz_filas_bajo_el_umbral",
        "tests/test_vistas_analisis.py",
        "Casos borde: Seguro de Bancos (BBB), con celdas negativas en la suma, y Vida Ley "
        "Ex-trabajadores (4 997.71) quedan bajo el umbral",
    ),
    (
        "test_matriz_suma_con_el_total_publicado",
        "tests/test_vistas_analisis.py",
        "Suma de las primas netas de la matriz frente al Total de P009: menos de 1 mil soles",
    ),
    (
        "test_participacion_indice_nulo_sin_primas",
        "tests/test_vistas_analisis.py",
        "Ninguna celda con primas netas 0 o negativas tiene índice directo (D-PF01-14)",
    ),
    (
        "test_cuadrantes_iguales_a_la_vista",
        "tests/test_indicadores_oracle.py",
        "Los cuatro cuadrantes recalculados en Python coinciden con vw_matriz_riesgo",
    ),
    (
        "test_indices_iguales_a_la_vista",
        "tests/test_indicadores_oracle.py",
        "Los índices recalculados en Python coinciden con la vista (diferencia menor que 0.0001)",
    ),
    (
        "test_clasificacion_igual_a_la_vista",
        "tests/test_indicadores_oracle.py",
        "La clasificación por celda de vw_participacion_empresa_riesgo coincide con Python",
    ),
)
REFERENCIAS = (
    "Superintendencia de Banca, Seguros y AFP. (s. f.-a). *Boletín mensual* [Conjunto de "
    "datos]. Recuperado el 11 de octubre de 2026, de "
    "https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-367",
    "Superintendencia de Banca, Seguros y AFP. (s. f.-b). *Índice de siniestralidad directa "
    "y retenida según riesgos* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de "
    "https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-403",
    "Superintendencia de Banca, Seguros y AFP. (s. f.-c). *Primas de seguros netas, cedidas "
    "y retenidas según riesgos* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de "
    "https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-401",
    "Superintendencia de Banca, Seguros y AFP. (s. f.-d). *Siniestros de primas de seguros "
    "netas, cedidas y retenidas según riesgos* [Conjunto de datos]. Recuperado el 11 de "
    "octubre de 2026, de "
    "https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-402",
)


def fuera_de_tolerancia(diferencia: pd.Series, tolerancia: float = TOLERANCIA_O2) -> pd.Series:
    """True si el valor absoluto supera la tolerancia o si la diferencia no existe (NaN)."""
    return ~(diferencia.abs() <= tolerancia)


# --------------------------------------------------------------------------------------
# Controles
# --------------------------------------------------------------------------------------


def contraste_total_sistema(indicadores: pd.DataFrame, publicados: pd.DataFrame) -> pd.DataFrame:
    """Índice total del sistema por corte, calculado con las filas de vw_indicadores_riesgo.

    indicadores tiene las columnas de vw_indicadores_riesgo; publicados, una fila por corte
    con fecha_corte, directa_publicada (fila Total de P015) y retenida_publicada (de P016).
    El índice calculado es 100 × Σ siniestros / Σ primas del corte (D-PF01-12).
    """
    montos = ["primas_netas", "primas_retenidas", "siniestros_netos", "siniestros_retenidos"]
    datos = indicadores.assign(**{c: indicadores[c].astype(float) for c in montos})
    sumas = datos.groupby("fecha_corte").agg(
        meses_acumulados=("meses_acumulados", "first"), **{c: (c, "sum") for c in montos}
    )
    for medida, (siniestros, primas) in COLUMNAS_MEDIDA.items():
        sumas[f"{medida}_calculada"] = 100 * sumas[siniestros] / sumas[primas]
    publicado = publicados.set_index("fecha_corte")[
        [f"{medida}_publicada" for medida in MEDIDAS]
    ].astype(float)
    contraste = sumas.join(publicado, how="left")
    for medida in MEDIDAS:
        contraste[f"diferencia_{medida}"] = (
            contraste[f"{medida}_calculada"] - contraste[f"{medida}_publicada"]
        )
    contraste["meses_acumulados"] = contraste["meses_acumulados"].astype(int)
    return contraste.sort_index().reset_index()


def comparacion_por_medida(contraste: pd.DataFrame) -> pd.DataFrame:
    """Una fila por corte y medida: calculada, publicada, diferencia y si está conforme."""
    partes = [
        pd.DataFrame(
            {
                "fecha_corte": contraste["fecha_corte"],
                "medida": medida,
                "calculada": contraste[f"{medida}_calculada"],
                "publicada": contraste[f"{medida}_publicada"],
                "diferencia": contraste[f"diferencia_{medida}"],
            }
        )
        for medida in MEDIDAS
    ]
    detalle = pd.concat(partes, ignore_index=True).sort_values(["fecha_corte", "medida"])
    detalle["conforme"] = ~fuera_de_tolerancia(detalle["diferencia"])
    return detalle.reset_index(drop=True)


def control_o2(contraste: pd.DataFrame, corte_actual: date) -> Resultado:
    """O2: índice total del sistema del corte actual, directa y retenida, dentro de 0.1 p. p."""
    detalle = comparacion_por_medida(contraste[contraste["fecha_corte"] == corte_actual])
    fallas = int((~detalle["conforme"]).sum())
    if detalle.empty:
        fallas = len(MEDIDAS)  # sin el corte actual no hay contraste
    return Resultado("O2 · índice total del sistema, agosto de 2026", len(MEDIDAS), fallas, detalle)


def control_serie_total(contraste: pd.DataFrame) -> Resultado:
    """Índice total del sistema en cada corte y medida, dentro de 0.1 p. p."""
    detalle = comparacion_por_medida(contraste)
    return Resultado(
        "Índice total del sistema por corte, 2019-2026",
        len(detalle),
        int((~detalle["conforme"]).sum()),
        detalle,
    )


def control_indice_por_riesgo(indicadores: pd.DataFrame) -> Resultado:
    """Índice calculado frente al publicado en las filas de un riesgo con primas positivas.

    Directa: filas con primas netas positivas; retenida: con primas retenidas positivas. El
    detalle resume cada corte y medida: filas comparadas, diferencia máxima en valor absoluto
    y el riesgo comparable donde ocurre.
    """
    partes = []
    for medida, (_, primas) in COLUMNAS_MEDIDA.items():
        filas = indicadores[
            (indicadores["n_riesgos"] == 1) & (indicadores[primas].astype(float) > 0)
        ]
        calculado = filas[f"indice_siniestralidad_{medida}"].astype(float)
        publicado = filas[f"indice_{medida}_publicado"].astype(float)
        partes.append(
            pd.DataFrame(
                {
                    "fecha_corte": filas["fecha_corte"],
                    "medida": medida,
                    "riesgo_comparable": filas["riesgo_comparable"],
                    "diferencia": calculado - publicado,
                }
            )
        )
    comparadas = pd.concat(partes, ignore_index=True)
    comparadas["absoluta"] = comparadas["diferencia"].abs()
    comparadas["falla"] = fuera_de_tolerancia(comparadas["diferencia"])
    resumen = []
    for (corte, medida), grupo in comparadas.groupby(["fecha_corte", "medida"], sort=True):
        # Una diferencia sin publicado (NaN) se muestra como el máximo: es una falla.
        orden = grupo.sort_values("absoluta", ascending=False, na_position="first")
        mayor = orden.iloc[0]
        resumen.append(
            {
                "fecha_corte": corte,
                "medida": medida,
                "filas": len(grupo),
                "diferencia_maxima": mayor["absoluta"],
                "riesgo_comparable": mayor["riesgo_comparable"],
                "fallas": int(grupo["falla"].sum()),
            }
        )
    return Resultado(
        "Índice por riesgo frente al publicado, 2019-2026",
        len(comparadas),
        int(comparadas["falla"].sum()),
        pd.DataFrame(resumen),
    )


def control_cobertura_matriz(matriz: pd.DataFrame) -> Resultado:
    """Recuentos de vw_matriz_riesgo frente a COBERTURA_ESPERADA (resultados de 3.2)."""
    resumen = resumen_matriz(matriz)
    por_cuadrante = resumen["por_cuadrante_interanual_directa"]
    obtenido = {
        "Filas": resumen["filas"],
        "Sobre el umbral": resumen["sobre_umbral"],
        "No comparables (rentas y SPP)": resumen["no_comparables"],
        "Clasificadas": int(matriz["cuadrante_interanual_directa"].notna().sum()),
    }
    esperado = {
        "Filas": COBERTURA_ESPERADA["filas"],
        "Sobre el umbral": COBERTURA_ESPERADA["sobre_umbral"],
        "No comparables (rentas y SPP)": COBERTURA_ESPERADA["no_comparables"],
        "Clasificadas": COBERTURA_ESPERADA["clasificadas"],
    }
    for clave, n in COBERTURA_ESPERADA["por_cuadrante"].items():
        magnitud = "Sin cuadrante" if clave is None else f"Cuadrante {clave}"
        esperado[magnitud] = n
        obtenido[magnitud] = por_cuadrante.get(clave, 0)
    detalle = pd.DataFrame(
        {
            "magnitud": list(esperado),
            "esperado": list(esperado.values()),
            "obtenido": [obtenido[m] for m in esperado],
        }
    )
    detalle["conforme"] = detalle["esperado"] == detalle["obtenido"]
    return Resultado(
        "Cobertura de la matriz", len(detalle), int((~detalle["conforme"]).sum()), detalle
    )


def control_primas_matriz(matriz: pd.DataFrame, total_p009: float) -> Resultado:
    """Suma de las primas netas de la matriz frente al Total de P009: diferencia < 1 mil soles."""
    suma = float(matriz["primas_netas"].astype(float).sum())
    diferencia = suma - float(total_p009)
    falla = not abs(diferencia) < TOLERANCIA_MILES
    detalle = pd.DataFrame(
        [{"suma_matriz": suma, "total_publicado": float(total_p009), "diferencia": diferencia}]
    )
    return Resultado(
        "Primas de la matriz frente al Total publicado de P009", 1, int(falla), detalle
    )


# --------------------------------------------------------------------------------------
# Nota en Markdown
# --------------------------------------------------------------------------------------


def miles(n: float) -> str:
    """Entero con separador de millares de espacio (RAE)."""
    return f"{n:,.0f}".replace(",", " ")


def decimales(x: float, cifras: int = 4) -> str:
    """Número con cifras decimales fijas; sin «-0.0000»; «s. d.» si no hay dato."""
    if pd.isna(x):
        return "s. d."
    redondeado = round(float(x), cifras)
    return f"{0.0 if redondeado == 0 else redondeado:.{cifras}f}"


def mes_y_anio(corte: date) -> str:
    """«agosto de 2026»."""
    return f"{MESES[corte.month - 1]} de {corte.year}"


def tabla_markdown(encabezados: list[str], filas: list[list[str]]) -> list[str]:
    """Líneas de una tabla Markdown."""
    return [
        "| " + " | ".join(encabezados) + " |",
        "|" + "---|" * len(encabezados),
        *["| " + " | ".join(fila) + " |" for fila in filas],
    ]


def resultado_prueba(pruebas: dict[str, object]) -> str:
    """Resultado de una prueba citada a partir del resumen de la corrida de pytest -q.

    Los dos archivos de pruebas citados se omiten juntos (mismo pytestmark), así que el
    resumen de la corrida vale para cada prueba citada.
    """
    resumen = str(pruebas.get("resumen", ""))
    if pruebas.get("codigo") != 0 or "failed" in resumen or "error" in resumen:
        return "Con fallas en la corrida"
    if "passed" in resumen:
        return "Aprobada"
    if "skipped" in resumen:
        return "Omitida"
    return "Sin resultado"


def lectura(resultados: list[Resultado], contraste: pd.DataFrame) -> list[str]:
    """Dos o tres frases con el resultado de O2 y el de la serie, sin adjetivos."""
    o2, serie = resultados[0], resultados[1]
    frases = []
    if not o2.detalle.empty:
        actual = o2.detalle.set_index("medida")
        corte = o2.detalle["fecha_corte"].iloc[0]
        frases.append(
            f"En {mes_y_anio(corte)}, el índice total del sistema calculado con las filas de "
            f"vw_indicadores_riesgo es {decimales(actual.loc['directa', 'calculada'])} % en la "
            "directa y "
            f"{decimales(actual.loc['retenida', 'calculada'])} % en la retenida, frente a "
            f"{decimales(actual.loc['directa', 'publicada'])} % y "
            f"{decimales(actual.loc['retenida', 'publicada'])} % publicados."
        )
        frases.append(
            f"Las diferencias son {decimales(actual.loc['directa', 'diferencia'])} p. p. y "
            f"{decimales(actual.loc['retenida', 'diferencia'])} p. p.; O2 "
            f"{'se cumple' if o2.ok else 'no se cumple'} con la tolerancia de 0.1 p. p."
        )
    detalle = serie.detalle.assign(absoluta=serie.detalle["diferencia"].abs())
    maximos = []
    for medida in MEDIDAS:
        filas_medida = detalle[detalle["medida"] == medida].sort_values(
            "absoluta", ascending=False, na_position="first"
        )
        if not filas_medida.empty:
            mayor = filas_medida.iloc[0]
            maximos.append(
                f"{decimales(mayor['absoluta'])} p. p. en la {medida} "
                f"({mes_y_anio(mayor['fecha_corte'])})"
            )
    frases.append(
        f"En los {len(contraste)} cortes de la serie, la mayor diferencia en valor absoluto es "
        f"{' y '.join(maximos)}; {serie.fallas} de {serie.revisados} combinaciones de corte y "
        "medida superan la tolerancia."
    )
    return [" ".join(frases)]


def informe(
    resultados: list[Resultado],
    contraste: pd.DataFrame,
    detalle_por_riesgo: pd.DataFrame,
    cobertura: pd.DataFrame,
    entorno: dict[str, str],
    pruebas: dict[str, object],
) -> str:
    """Markdown de reports/validacion_resultados.md.

    resultados: los cinco controles, en el orden de D-PF01-17 (O2 primero, la serie después).
    entorno: fecha_generacion, base, version, corte_actual y fecha_descarga.
    pruebas: comando, resumen (línea final de pytest -q) y codigo (código de salida).
    """
    resumen = [
        [r.control, miles(r.revisados), str(r.fallas), "Conforme" if r.ok else "Con fallas"]
        for r in resultados
    ]
    serie = [
        [
            f"{fila.fecha_corte:%Y-%m-%d}",
            str(fila.meses_acumulados),
            miles(fila.primas_netas),
            miles(fila.siniestros_netos),
            decimales(fila.directa_calculada),
            decimales(fila.directa_publicada),
            decimales(fila.diferencia_directa),
            decimales(fila.retenida_calculada),
            decimales(fila.retenida_publicada),
            decimales(fila.diferencia_retenida),
        ]
        for fila in contraste.itertuples(index=False)
    ]
    por_riesgo = [
        [
            f"{fila.fecha_corte:%Y-%m-%d}",
            fila.medida.capitalize(),
            str(fila.filas),
            decimales(fila.diferencia_maxima),
            str(fila.riesgo_comparable),
        ]
        for fila in detalle_por_riesgo.itertuples(index=False)
    ]
    magnitudes = [
        [fila.magnitud, str(fila.esperado), str(fila.obtenido)]
        for fila in cobertura.itertuples(index=False)
    ]
    resultado = resultado_prueba(pruebas)
    citadas = [
        [f"`{nombre}`", f"`{archivo}`", verifica, resultado]
        for nombre, archivo, verifica in PRUEBAS_CITADAS
    ]
    partes = [
        "# Validación de resultados · PF-01 · Paquete 3.3",
        "",
        f"`Portafolio · PF-01` · Generado con `scripts/validar_resultados.py` el "
        f"{entorno['fecha_generacion']} · Tolerancia de O2: 0.1 p. p.",
        "",
        "## Entorno",
        "",
        f"- Base: {entorno['base']}",
        f"- Versión del motor: {entorno['version']}",
        f"- Corte actual: {entorno['corte_actual']}",
        f"- Fecha de descarga de los datos (data/raw/manifest.csv): {entorno['fecha_descarga']}",
        "",
        *tabla_markdown(["Control", "Revisados", "Fallas", "Resultado"], resumen),
        "",
        NOTA_TABLA,
        "",
        "## Tabla 1. Índice total del sistema por corte",
        "",
        "Montos en miles de soles; índices en porcentaje; diferencias en puntos porcentuales "
        "(p. p.), calculado menos publicado.",
        "",
        *tabla_markdown(
            [
                "Corte",
                "Meses",
                "Primas netas",
                "Siniestros netos",
                "Directa calculada",
                "Directa publicada",
                "Diferencia (p. p.)",
                "Retenida calculada",
                "Retenida publicada",
                "Diferencia (p. p.)",
            ],
            serie,
        ),
        "",
        NOTA_TABLA,
        "",
        "## Tabla 2. Índice por riesgo: diferencia máxima por corte",
        "",
        "Filas de un riesgo con primas positivas; diferencia máxima en valor absoluto, en p. p.",
        "",
        *tabla_markdown(
            ["Corte", "Medida", "Filas comparadas", "Diferencia máxima (p. p.)", "Riesgo"],
            por_riesgo,
        ),
        "",
        NOTA_TABLA,
        "",
        "## Tabla 3. Cobertura de la matriz",
        "",
        *tabla_markdown(["Magnitud", "Esperado", "Obtenido"], magnitudes),
        "",
        NOTA_TABLA,
        "",
        "## Lectura",
        "",
        *lectura(resultados, contraste),
        "",
        "## Pruebas automatizadas citadas",
        "",
        f"Corrida: `{pruebas.get('comando', '')}` · Resumen: {pruebas.get('resumen', '')}",
        "",
        *tabla_markdown(["Prueba", "Archivo", "Qué verifica", "Resultado"], citadas),
        "",
        NOTA_TABLA,
        "",
        "## Referencias",
        "",
    ]
    for referencia in REFERENCIAS:
        partes += [referencia, ""]
    return "\n".join(partes)
