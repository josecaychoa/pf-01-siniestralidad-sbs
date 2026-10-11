# Validación de datos · PF-01 · Paquete 2.2

`Portafolio · PF-01` · Generado con `scripts/validar_datos.py` el 2026-10-11 · Tolerancia: 1 mil soles

| Control | Revisados | Fallas | Excepciones de la fuente | Resultado |
|---|---|---|---|---|
| Estructura por corte | 86 886 | 0 | 0 | Conforme |
| Cuadre con los totales publicados | 7 544 | 0 | 0 | Conforme |
| Jerarquía de riesgos | 6 912 | 0 | 0 | Conforme |
| Activo = Pasivo + Patrimonio | 504 | 0 | 0 | Conforme |
| MN + ME = TOTAL | 16 816 | 0 | 6 | Conforme |
| Boletín frente a S-401, S-402 y S-403 | 8 778 | 0 | 0 | Conforme |
| Cifras acumuladas en el año | 3 | 0 | 0 | Conforme |
| Versión del plan de cuentas | 9 | 0 | 0 | Conforme |

*Nota.* Elaboración propia con datos de SBS (s. f.-a, s. f.-b, s. f.-c, s. f.-d). «Revisados» cuenta filas, celdas o combinaciones según el control. Las excepciones son diferencias de la propia fuente, documentadas en `src/pf_01_siniestralidad_sbs/catalogos/excepciones.csv`.

## Cifras acumuladas en el año

| Serie | Agosto de 2025 | Diciembre de 2025 | Razón | Esperada (12 / 8) |
|---|---|---|---|---|
| Primas netas (P009) | 15 398 030 | 24 034 639 | 1.561 | 1.500 |
| Siniestros netos (P012) | 6 370 383 | 9 473 707 | 1.487 | 1.500 |
| Primas netas (P002) | 15 398 030 | 24 034 639 | 1.561 | 1.500 |

*Nota.* En miles de soles. Elaboración propia con datos de SBS (s. f.-a).

## Detalle: MN + ME = TOTAL

| corte | hoja | fila | concepto_n | empresa_n | ME | MN | TOTAL | diferencia | control | observacion |
|---|---|---|---|---|---|---|---|---|---|---|
| 2021-12-31 | P001 | 77 | PERDIDA NETA NO REALIZADA POR VALORIZACION DE LAS INVERSIONES DISPONIBLES PARA LA VENTA | AVLA PERU | 0.000 | 0.000 | -361.983 | 361.983 | MN + ME = TOTAL | La columna TOTAL publica un monto que no figura en MN ni en ME (-361.983 mil soles); la diferencia se arrastra al total de empresas |
| 2021-12-31 | P001 | 77 | PERDIDA NETA NO REALIZADA POR VALORIZACION DE LAS INVERSIONES DISPONIBLES PARA LA VENTA | TOTAL EMPRESAS DE SEGUROS | -16 201.411 | -95 400.370 | -111 963.768 | 361.987 | MN + ME = TOTAL | Efecto de la fila de Avla Perú del mismo corte |
| 2022-12-31 | P001 | 77 | PERDIDA NETA NO REALIZADA POR VALORIZACION DE LAS INVERSIONES DISPONIBLES PARA LA VENTA | AVLA PERU | 0.000 | 0.000 | -282.818 | 282.818 | MN + ME = TOTAL | La columna TOTAL publica un monto que no figura en MN ni en ME (-282.818 mil soles); la diferencia se arrastra al total de empresas |
| 2022-12-31 | P001 | 77 | PERDIDA NETA NO REALIZADA POR VALORIZACION DE LAS INVERSIONES DISPONIBLES PARA LA VENTA | TOTAL EMPRESAS DE SEGUROS | -25 675.056 | -253 624.797 | -279 582.671 | 282.818 | MN + ME = TOTAL | Efecto de la fila de Avla Perú del mismo corte |
| 2023-12-31 | P001 | 78 | PERDIDA NETA NO REALIZADA POR VALORIZACION DE LAS INVERSIONES DISPONIBLES PARA LA VENTA | AVLA PERU | 0.000 | 0.000 | -141.053 | 141.053 | MN + ME = TOTAL | La columna TOTAL publica un monto que no figura en MN ni en ME (-141.053 mil soles); la diferencia se arrastra al total de empresas |
| 2023-12-31 | P001 | 78 | PERDIDA NETA NO REALIZADA POR VALORIZACION DE LAS INVERSIONES DISPONIBLES PARA LA VENTA | TOTAL EMPRESAS DE SEGUROS | -19 083.641 | -133 412.849 | -152 637.544 | 141.054 | MN + ME = TOTAL | Efecto de la fila de Avla Perú del mismo corte |

## Referencias

Superintendencia de Banca, Seguros y AFP. (s. f.-a). *Boletín mensual* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-367

Superintendencia de Banca, Seguros y AFP. (s. f.-b). *Índice de siniestralidad directa y retenida según riesgos* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-403

Superintendencia de Banca, Seguros y AFP. (s. f.-c). *Primas de seguros netas, cedidas y retenidas según riesgos* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-401

Superintendencia de Banca, Seguros y AFP. (s. f.-d). *Siniestros de primas de seguros netas, cedidas y retenidas según riesgos* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-402
