# Informe de resultados · PF-01 · Producción y siniestralidad por riesgo del mercado asegurador peruano, 2019-2026

`Portafolio · PF-01` · Paquete 4.2 (issue #11) · Corte de datos: agosto de 2026 · Elaborado el 2026-10-26

## Resumen

En agosto de 2026, el sistema asegurador peruano acumuló primas netas por 16 784.7 millones de soles, 9.0 % más que en agosto de 2025, con una siniestralidad directa de 48.9 % y una retenida de 45.7 % (Superintendencia de Banca, Seguros y AFP [SBS], s. f.-a). La directa subió 7.5 puntos porcentuales (p. p.) en un año y revirtió el descenso que traía desde el máximo de 2021 (59.3 %). De los 35 riesgos clasificados en la matriz, 9 crecen con una siniestralidad directa mayor que el corte de 44.0 %; concentran 5 305.3 millones de soles de primas, con Vida Individual de Largo Plazo, Asistencia Médica y Vehículos a la cabeza.

## 1. Problema y alcance

El proyecto responde una pregunta de monitoreo del mercado: ¿qué riesgos del sistema asegurador peruano crecen en primas con una siniestralidad mayor que la del conjunto, y cómo evolucionó el índice del sistema entre 2019 y 2026? El análisis cubre las primas y los siniestros, netos y retenidos, de los 48 riesgos del Boletín mensual de la SBS (s. f.-a), con un umbral de materialidad de 5 millones de soles de primas netas acumuladas por corte. El alcance describe cifras agregadas por riesgo; excluye juicios sobre la gestión de las empresas y cualquier dato personal (acta, `docs/01_acta.md`, sección 4).

## 2. Datos y método

Los datos provienen de cuatro conjuntos públicos de la SBS: el Boletín mensual (s. f.-a), el índice de siniestralidad por riesgos (s. f.-b), las primas por riesgos (s. f.-c) y los siniestros por riesgos (s. f.-d), descargados el 11 de octubre de 2026 con un script reproducible que registra URL, fecha y SHA-256 de cada archivo (`data/raw/manifest.csv`). El flujo lleva las hojas a formato largo, las carga en Oracle y calcula los indicadores en las vistas `vw_` de `sql/oracle/04_vistas_analisis.sql`; los CSV que alimentan el tablero y este informe están versionados en `data/processed/` (decisión D-PF01-23).

La serie usa el Total ampliado del catálogo de empresas, que incorpora a Rigel y Coface (decisiones D-PF01-12 y D-PF01-18); por esa diferencia de alcance, 5 celdas del índice publicado de diciembre de 2020 se documentan como excepciones de la fuente. La validación de resultados (`reports/validacion_resultados.md`) cuadra el índice del sistema con el publicado en los 9 cortes con una diferencia máxima de 0.0015 p. p., dentro de la tolerancia de 0.1 p. p. del objetivo O2, y cita 27 pruebas automatizadas superadas.

## 3. El sistema, 2019-2026

La siniestralidad directa del sistema pasó de 53.0 % en diciembre de 2019 a un máximo de 59.3 % en diciembre de 2021, bajó en los cuatro cortes anuales siguientes hasta 39.4 % en diciembre de 2025 y repuntó a 48.9 % en agosto de 2026, 7.5 p. p. por encima de agosto de 2025 (tabla 1 y figura 1). La retenida alcanzó su propio máximo en 2021 (52.9 %), corre por debajo de la directa desde 2022 y cerró agosto de 2026 en 45.7 %, 5.5 p. p. más que un año antes. Las primas netas cayeron 0.7 % en 2020 y crecieron todos los años desde 2021; el acumulado de agosto de 2026 supera en 9.0 % al de agosto de 2025.

**Tabla 1**

*Primas netas e índice de siniestralidad del sistema por corte, 2019-2026*

| Corte | Meses | Primas netas (millones de S/) | Directa (%) | Retenida (%) |
|---|---:|---:|---:|---:|
| 2019-12-31 | 12 | 14 113.5 | 53.0 | 46.0 |
| 2020-12-31 | 12 | 14 021.4 | 51.7 | 51.9 |
| 2021-12-31 | 12 | 17 695.5 | 59.3 | 52.9 |
| 2022-12-31 | 12 | 18 746.3 | 54.0 | 44.8 |
| 2023-12-31 | 12 | 20 265.8 | 47.8 | 45.9 |
| 2024-12-31 | 12 | 22 186.1 | 43.1 | 42.2 |
| 2025-08-31 | 8 | 15 398.0 | 41.4 | 40.3 |
| 2025-12-31 | 12 | 24 034.6 | 39.4 | 39.3 |
| 2026-08-31 | 8 | 16 784.7 | 48.9 | 45.7 |

*Nota.* Elaboración propia con datos de SBS (s. f.-a, s. f.-b, s. f.-c, s. f.-d). Suma de los 48 riesgos de `data/processed/indicadores_riesgo.csv`; los cortes de diciembre acumulan 12 meses y los de agosto, 8. Detalle con cuatro decimales en `reports/validacion_resultados.md`, tabla 1. La tabla se genera con `uv run python scripts/figura_serie.py --tabla`.

**Figura 1**

*Índice de siniestralidad del sistema asegurador peruano por corte, 2019-2026*

![Serie 2019-2026 del índice de siniestralidad del sistema: la directa sube a 48.9 % en agosto de 2026, 7.5 puntos porcentuales más que en agosto de 2025; la retenida llega a 45.7 %](figures/PF-01_serie.svg)

*Nota.* Elaboración propia con datos de SBS (s. f.-a, s. f.-b, s. f.-c, s. f.-d). Figura generada con `uv run python scripts/figura_serie.py`; los puntos huecos marcan los cortes de agosto (8 meses acumulados).

## 4. Matriz de riesgos de agosto de 2026

La matriz clasifica cada riesgo según dos atributos: la variación interanual de sus primas netas (crece si es mayor o igual que 0 %) y su índice de siniestralidad frente al corte, definido como el índice agregado de los riesgos clasificados: 44.0 % en la directa y 39.5 % en la retenida (indicador IA-PF01-07 del acta). De los 48 riesgos del corte, 35 quedan clasificados, con 11 782.8 millones de soles de primas netas; 8 quedan bajo el umbral de materialidad (8.3 millones en conjunto) y 5 no son comparables por su naturaleza previsional (rentas y seguros del Sistema Privado de Pensiones, 4 993.5 millones).

**Tabla 2**

*Riesgos clasificados por cuadrante, agosto de 2026*

| Cuadrante | Lectura | Directa | Retenida |
|---|---|---:|---:|
| 1 · Crece sobre el corte | Primas en aumento y siniestralidad mayor que el conjunto | 9 | 8 |
| 2 · Crece bajo el corte | Primas en aumento y siniestralidad menor que el conjunto | 12 | 13 |
| 3 · Decrece sobre el corte | Primas en descenso y siniestralidad mayor que el conjunto | 7 | 5 |
| 4 · Decrece bajo el corte | Primas en descenso y siniestralidad menor que el conjunto | 7 | 9 |
| **Total** | | **35** | **35** |

*Nota.* Elaboración propia con datos de SBS (s. f.-a, s. f.-b, s. f.-c, s. f.-d), según `data/processed/matriz_riesgos.csv`. El corte no es una meta: cambia con cada corte de datos (D-PF01-16).

El cuadrante 1 de la directa reúne a los 9 riesgos que crecen con una siniestralidad mayor que el 44.0 % del conjunto (tabla 3). Tres de ellos concentran el 83.7 % de las primas del cuadrante: Vida Individual de Largo Plazo, que creció 31.2 % con un índice de 45.0 %; Asistencia Médica, con 65.7 % de siniestralidad, y Vehículos, con 61.3 %. Con la medida retenida, el grupo baja a 8 riesgos frente a un corte de 39.5 %: Crédito Interno sale del cuadrante porque su índice retenido (28.2 %) queda bajo ese corte.

**Tabla 3**

*Cuadrante 1 con la siniestralidad directa: riesgos que crecen sobre el corte de 44.0 %, agosto de 2026*

| Riesgo | Ramo | Primas netas (millones de S/) | Variación interanual (%) | Directa (%) |
|---|---|---:|---:|---:|
| Vida Individual de Largo Plazo | Vida | 2 081.1 | 31.2 | 45.0 |
| Asistencia Médica | Accidentes y enfermedades | 1 238.9 | 7.6 | 65.7 |
| Vehículos | Generales | 1 117.9 | 3.4 | 61.3 |
| Seguro Obligatorio de Accidentes de Tránsito (SOAT) | Accidentes y enfermedades | 387.9 | 7.6 | 64.8 |
| Vida Ley Trabajadores | Vida | 285.9 | 0.0 | 45.7 |
| Agricola | Generales | 74.7 | 333.0 | 74.3 |
| Todo Riesgo Equipo para Contratistas | Generales | 67.8 | 2.7 | 89.9 |
| Crédito Interno | Generales | 45.8 | 7.8 | 60.8 |
| Escolares | Accidentes y enfermedades | 5.3 | 16.0 | 44.2 |

*Nota.* Elaboración propia con datos de SBS (s. f.-a, s. f.-b, s. f.-c, s. f.-d), según `data/processed/matriz_riesgos.csv`, ordenada por primas netas. Los nombres de los riesgos reproducen el catálogo de la fuente. La variación de Agricola parte de una base pequeña (17.2 millones en agosto de 2025).

Las figuras 2 y 3 muestran la página «Matriz de riesgos» del tablero Power BI del paquete 4.1, que ubica cada riesgo clasificado por su variación interanual y su índice, con la segmentación «Medida» para alternar entre la directa y la retenida (`dashboards/powerbi/README.md`).

**Figura 2**

*Matriz de riesgos con la siniestralidad directa, agosto de 2026*

![Página «Matriz de riesgos» del tablero con la medida Directa: 9 de 35 riesgos crecen con una siniestralidad directa mayor que el corte de 44.0 %](figures/PF-01_tablero_directa.png)

*Nota.* Elaboración propia con datos de SBS (s. f.-a). Los ejes se recortan en 60 % de variación y 100 % de siniestralidad (D-PF01-13): 3 de los 35 riesgos clasificados quedan fuera de escala y no se dibujan, aunque cuentan en las tablas.

**Figura 3**

*Matriz de riesgos con la siniestralidad retenida, agosto de 2026*

![Página «Matriz de riesgos» del tablero con la medida Retenida: 8 de 35 riesgos crecen con una siniestralidad retenida mayor que el corte de 39.5 %](figures/PF-01_tablero_retenida.png)

*Nota.* Elaboración propia con datos de SBS (s. f.-a). Misma página que la figura 2, con la medida Retenida; 2 de los 35 riesgos clasificados quedan fuera de escala.

## 5. El proceso: de 95.0 a 9.9 minutos por corte

Reproducir este reporte a mano (descargar los boletines, consolidar las hojas, homologar empresas, alinear riesgos, armar fórmulas y cuadrar totales) toma 95.0 minutos por corte, según la estimación del autor con las cantidades del proyecto. El flujo del repositorio ejecuta las mismas actividades en 9.9 minutos: 3.9 de scripts medidos (mediana de tres corridas que reprocesan los 9 cortes) y 6.0 estimados de lectura de las dos notas de validación. El ahorro es de 85.1 minutos por corte (89.6 %), y el flujo agrega lo que el proceso manual no tenía: manifiesto de descarga, catálogos versionados y 27 pruebas automatizadas (figura 4).

**Figura 4**

*Tiempo del reporte de siniestralidad por corte, AS-IS frente a TO-BE*

![Tabla comparada de tiempos: el proceso manual AS-IS toma 95.0 minutos por corte y el flujo reproducible TO-BE, 9.9; el ahorro es de 85.1 minutos (89.6 %)](../docs/procesos/PF-01_tiempos.svg)

*Nota.* Elaboración propia. Medición del 2026-10-19 descrita en `docs/procesos/PF-01_tiempos.csv`; diagramas BPMN del proceso en `docs/procesos/`.

## 6. Limitaciones

- Los cortes de agosto acumulan 8 meses y los de diciembre, 12; el índice no está anualizado, así que las comparaciones interanuales válidas son entre cortes del mismo mes.
- La matriz usa un solo corte (agosto de 2026). Para otro corte hay que regenerar los CSV con `uv run python scripts/exportar_indicadores.py`.
- 5 riesgos previsionales (4 993.5 millones de soles de primas) y 8 riesgos bajo el umbral (8.3 millones) quedan fuera de la clasificación por cuadrante.
- En diciembre de 2020, 5 celdas del índice publicado por riesgo difieren del calculado porque la fuente usó el Total simple, sin Rigel ni Coface; la serie usa el Total ampliado en todos los cortes (D-PF01-18).
- Los índices describen montos agregados por riesgo. No miden rentabilidad técnica ni suficiencia de primas, y el alcance excluye juicios sobre la gestión de las empresas.

## 7. Conclusiones

La siniestralidad directa del sistema rompió en 2026 la tendencia descendente que traía desde 2021: 48.9 % en agosto, 7.5 p. p. más que un año antes, con primas que crecieron 9.0 %. El aumento no es uniforme: 9 de los 35 riesgos clasificados combinan crecimiento de primas con una siniestralidad mayor que la del conjunto, y tres de ellos (Vida Individual de Largo Plazo, Asistencia Médica y Vehículos) concentran 4 437.9 millones de soles de primas. La matriz de cuadrantes separa esos casos de los 12 riesgos que crecen con siniestralidad contenida, y el flujo reproducible deja el reporte listo en 9.9 minutos por corte, frente a los 95.0 del proceso manual.

## Referencias

Superintendencia de Banca, Seguros y AFP. (s. f.-a). *Boletín mensual* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-367

Superintendencia de Banca, Seguros y AFP. (s. f.-b). *Índice de siniestralidad directa y retenida según riesgos* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-403

Superintendencia de Banca, Seguros y AFP. (s. f.-c). *Primas de seguros netas, cedidas y retenidas según riesgos* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-401

Superintendencia de Banca, Seguros y AFP. (s. f.-d). *Siniestros de primas de seguros netas, cedidas y retenidas según riesgos* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-402
