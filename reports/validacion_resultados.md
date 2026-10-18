# Validación de resultados · PF-01 · Paquete 3.3

`Portafolio · PF-01` · Generado con `scripts/validar_resultados.py` el 2026-10-18 · Tolerancia de O2: 0.1 p. p.

## Entorno

- Base: nativa
- Versión del motor: Oracle Database 23ai Free, versión 23.6.0.24.10
- Corte actual: 2026-08-31 (agosto de 2026)
- Fecha de descarga de los datos (data/raw/manifest.csv): 2026-10-11

| Control | Revisados | Fallas | Excepciones de la fuente | Resultado |
|---|---|---|---|---|
| O2 · índice total del sistema, agosto de 2026 | 2 | 0 | 0 | Conforme |
| Índice total del sistema por corte, 2019-2026 | 18 | 0 | 0 | Conforme |
| Índice por riesgo frente al publicado, 2019-2026 | 784 | 0 | 5 | Conforme |
| Cobertura de la matriz | 9 | 0 | 0 | Conforme |
| Primas de la matriz frente al Total publicado de P009 | 1 | 0 | 0 | Conforme |

*Nota.* Elaboración propia con datos de SBS (s. f.-a, s. f.-b, s. f.-c, s. f.-d).

## Tabla 1. Índice total del sistema por corte

Montos en miles de soles; índices en porcentaje; diferencias en puntos porcentuales (p. p.), calculado menos publicado.

| Corte | Meses | Primas netas | Siniestros netos | Directa calculada | Directa publicada | Diferencia (p. p.) | Retenida calculada | Retenida publicada | Diferencia (p. p.) |
|---|---|---|---|---|---|---|---|---|---|
| 2019-12-31 | 12 | 14 113 517 | 7 479 280 | 52.9937 | 52.9937 | 0.0000 | 45.9940 | 45.9940 | 0.0000 |
| 2020-12-31 | 12 | 14 021 356 | 7 248 490 | 51.6961 | 51.6962 | −0.0001 | 51.8621 | 51.8606 | 0.0015 |
| 2021-12-31 | 12 | 17 695 457 | 10 495 248 | 59.3104 | 59.3104 | 0.0000 | 52.8718 | 52.8718 | 0.0000 |
| 2022-12-31 | 12 | 18 746 277 | 10 114 531 | 53.9549 | 53.9549 | 0.0000 | 44.7619 | 44.7619 | 0.0000 |
| 2023-12-31 | 12 | 20 265 843 | 9 678 626 | 47.7583 | 47.7583 | 0.0000 | 45.8840 | 45.8840 | 0.0000 |
| 2024-12-31 | 12 | 22 186 102 | 9 556 704 | 43.0752 | 43.0752 | 0.0000 | 42.1865 | 42.1865 | 0.0000 |
| 2025-08-31 | 8 | 15 398 030 | 6 370 383 | 41.3714 | 41.3714 | 0.0000 | 40.2534 | 40.2534 | 0.0000 |
| 2025-12-31 | 12 | 24 034 639 | 9 473 707 | 39.4169 | 39.4169 | 0.0000 | 39.2973 | 39.2973 | 0.0000 |
| 2026-08-31 | 8 | 16 784 650 | 8 210 057 | 48.9141 | 48.9141 | 0.0000 | 45.7487 | 45.7487 | 0.0000 |

*Nota.* Elaboración propia con datos de SBS (s. f.-a, s. f.-b, s. f.-c, s. f.-d).

## Tabla 2. Índice por riesgo: diferencia máxima por corte

Filas de un riesgo con primas positivas; diferencia máxima en valor absoluto, en p. p.

| Corte | Medida | Filas comparadas | Diferencia máxima (p. p.) | Riesgo |
|---|---|---|---|---|
| 2019-12-31 | Directa | 45 | 0.0000 | Terremoto |
| 2019-12-31 | Retenida | 45 | 0.0000 | Terremoto |
| 2020-12-31 | Directa | 44 | 3.6537 | Crédito Interno |
| 2020-12-31 | Retenida | 45 | 3.8232 | Crédito Interno |
| 2021-12-31 | Directa | 44 | 0.0000 | Robo y Asalto |
| 2021-12-31 | Retenida | 44 | 0.0000 | Robo y Asalto |
| 2022-12-31 | Directa | 45 | 0.0000 | Renta de Jubilados |
| 2022-12-31 | Retenida | 44 | 0.0000 | Renta de Jubilados |
| 2023-12-31 | Directa | 44 | 0.0000 | Incendio |
| 2023-12-31 | Retenida | 44 | 0.0000 | Incendio |
| 2024-12-31 | Directa | 44 | 0.0000 | Crédito Interno |
| 2024-12-31 | Retenida | 43 | 0.0000 | Crédito Interno |
| 2025-08-31 | Directa | 42 | 0.0000 | Crédito Interno |
| 2025-08-31 | Retenida | 42 | 0.0000 | Crédito Interno |
| 2025-12-31 | Directa | 42 | 0.0000 | Seguro Complementario de Trabajo de Riesgo |
| 2025-12-31 | Retenida | 42 | 0.0000 | Seguro Complementario de Trabajo de Riesgo |
| 2026-08-31 | Directa | 43 | 0.0000 | Vida Ley Ex-trabajadores |
| 2026-08-31 | Retenida | 42 | 0.0000 | Vida Ley Ex-trabajadores |

*Nota.* Elaboración propia con datos de SBS (s. f.-a, s. f.-b, s. f.-c, s. f.-d).

## Tabla 3. Cobertura de la matriz

| Magnitud | Esperado | Obtenido |
|---|---|---|
| Filas | 48 | 48 |
| Sobre el umbral | 40 | 40 |
| No comparables (rentas y SPP) | 5 | 5 |
| Clasificadas | 35 | 35 |
| Cuadrante 1 | 9 | 9 |
| Cuadrante 2 | 12 | 12 |
| Cuadrante 3 | 7 | 7 |
| Cuadrante 4 | 7 | 7 |
| Sin cuadrante | 13 | 13 |

*Nota.* Elaboración propia con datos de SBS (s. f.-a, s. f.-b, s. f.-c, s. f.-d).

## Detalle: índice por riesgo frente al publicado

Celdas que superan la tolerancia de 0.1 p. p.; índices en porcentaje y diferencia en p. p., calculado menos publicado. Las excepciones de la fuente están documentadas en `src/pf_01_siniestralidad_sbs/catalogos/excepciones.csv`.

| Corte | Hoja | Riesgo | Calculado | Publicado | Diferencia (p. p.) | Observación |
|---|---|---|---|---|---|---|
| 2020-12-31 | P015 | Crédito a la Exportación | 57.307244 | 54.426822 | 2.880422 | El índice publicado (54.426822) se calculó con el Total simple, sin Rigel ni Coface; el proyecto usa el Total ampliado (57.307244; D-PF01-12 y D-PF01-18): diferencia de 2.880422 p. p. |
| 2020-12-31 | P016 | Crédito a la Exportación | 38.735398 | 35.184965 | 3.550433 | El índice publicado (35.184965) se calculó con el Total simple, sin Rigel ni Coface; el proyecto usa el Total ampliado (38.735398; D-PF01-12 y D-PF01-18): diferencia de 3.550433 p. p. |
| 2020-12-31 | P015 | Crédito Interno | 41.093782 | 44.747437 | −3.653655 | El índice publicado (44.747437) se calculó con el Total simple, sin Rigel ni Coface; el proyecto usa el Total ampliado (41.093782; D-PF01-12 y D-PF01-18): diferencia de −3.653655 p. p. |
| 2020-12-31 | P016 | Crédito Interno | 16.842451 | 20.665698 | −3.823247 | El índice publicado (20.665698) se calculó con el Total simple, sin Rigel ni Coface; el proyecto usa el Total ampliado (16.842451; D-PF01-12 y D-PF01-18): diferencia de −3.823247 p. p. |
| 2020-12-31 | P016 | Seguros Previsionales | 116.189118 | 116.066594 | 0.122524 | El índice publicado (116.066594) se calculó con el Total simple, sin Rigel ni Coface; el proyecto usa el Total ampliado (116.189118; D-PF01-12 y D-PF01-18): diferencia de 0.122524 p. p. |

*Nota.* Elaboración propia con datos de SBS (s. f.-a, s. f.-b, s. f.-c, s. f.-d).

## Lectura

En agosto de 2026, el índice total del sistema calculado con las filas de vw_indicadores_riesgo es 48.9141 % en la directa y 45.7487 % en la retenida, frente a 48.9141 % y 45.7487 % publicados. Las diferencias son 0.0000 p. p. y 0.0000 p. p.; O2 se cumple con la tolerancia de 0.1 p. p. En los 9 cortes de la serie, la mayor diferencia en valor absoluto es 0.0001 p. p. en la directa (diciembre de 2020) y 0.0015 p. p. en la retenida (diciembre de 2020); ninguna de las 18 combinaciones de corte y medida supera la tolerancia.

En diciembre de 2020 el índice publicado por riesgo se calculó con el Total simple, sin Rigel ni Coface: 5 celdas superan la tolerancia, con una diferencia máxima, en valor absoluto, de 3.8232 p. p. (Crédito Interno, P016), mientras que en diciembre de 2022 corresponde al Total ampliado, con una diferencia máxima de 0.0000 p. p. en la directa y 0.0000 p. p. en la retenida. La serie usa el Total ampliado en los dos cortes (D-PF01-18) y esas 5 celdas se informan como excepciones de la fuente; el índice total del sistema de diciembre de 2020 difiere del publicado en −0.0001 p. p. en la directa y 0.0015 p. p. en la retenida (tabla 1).

## Pruebas automatizadas citadas

Corrida: `uv run pytest -q -p no:cacheprovider tests/test_vistas_analisis.py tests/test_indicadores_oracle.py` · Resumen: 27 pruebas superadas (`27 passed in 11.40s`)

| Prueba | Archivo | Qué verifica | Resultado |
|---|---|---|---|
| `test_matriz_indice_calculado_igual_al_publicado` | `tests/test_vistas_analisis.py` | Índice directo calculado frente al publicado en las filas de un riesgo con primas positivas del corte actual: diferencia máxima menor que 0.1 p. p. | Aprobada |
| `test_matriz_filas_y_umbral` | `tests/test_vistas_analisis.py` | La matriz tiene 48 filas y 40 sobre el umbral de 5 000 mil soles | Aprobada |
| `test_matriz_filas_bajo_el_umbral` | `tests/test_vistas_analisis.py` | Casos borde: Seguro de Bancos (BBB), con celdas negativas en la suma, y Vida Ley Ex-trabajadores (4 997.71) quedan bajo el umbral | Aprobada |
| `test_matriz_suma_con_el_total_publicado` | `tests/test_vistas_analisis.py` | Suma de las primas netas de la matriz frente al Total de P009: menos de 1 mil soles | Aprobada |
| `test_participacion_indice_nulo_sin_primas` | `tests/test_vistas_analisis.py` | Ninguna celda con primas netas 0 o negativas tiene índice directo (D-PF01-14) | Aprobada |
| `test_cuadrantes_iguales_a_la_vista` | `tests/test_indicadores_oracle.py` | Los cuatro cuadrantes recalculados en Python coinciden con vw_matriz_riesgo | Aprobada |
| `test_indices_iguales_a_la_vista` | `tests/test_indicadores_oracle.py` | Los índices recalculados en Python coinciden con la vista (diferencia menor que 0.0001) | Aprobada |
| `test_clasificacion_igual_a_la_vista` | `tests/test_indicadores_oracle.py` | La clasificación por celda de vw_participacion_empresa_riesgo coincide con Python | Aprobada |

*Nota.* Elaboración propia con datos de SBS (s. f.-a, s. f.-b, s. f.-c, s. f.-d).

## Referencias

Superintendencia de Banca, Seguros y AFP. (s. f.-a). *Boletín mensual* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-367

Superintendencia de Banca, Seguros y AFP. (s. f.-b). *Índice de siniestralidad directa y retenida según riesgos* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-403

Superintendencia de Banca, Seguros y AFP. (s. f.-c). *Primas de seguros netas, cedidas y retenidas según riesgos* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-401

Superintendencia de Banca, Seguros y AFP. (s. f.-d). *Siniestros de primas de seguros netas, cedidas y retenidas según riesgos* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-402
