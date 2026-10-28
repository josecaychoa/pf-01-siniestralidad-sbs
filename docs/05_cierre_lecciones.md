# Cierre · PF-01: Producción y siniestralidad por riesgo del mercado asegurador peruano, 2019-2026

`Portafolio · PF-01` · Versión 0.4 · 2026-10-27 · Cambio v0.4: valor ganado en horas (sección 3.3), conciliación del total de horas, release v1.0.0 marcado y paquetes 4.4 y 4.5 de CC-PF-01-02 (auditoría integral) · Paquete 1.3 (#13) terminado y «Listo para cierre» recibido el 2026-10-27; faltan la publicación (O3) y la fecha de cierre del proyecto.

## 1. Criterios de cierre

- [x] Objetivos SMART evaluados con evidencia (sección 2); O3 se completa con la publicación del 2026-11-26.
- [x] Repositorio reproducible desde un clon limpio: `uv sync --locked` y `uv run pytest` con 129 pruebas superadas y 50 omitidas sin Oracle ni `data/raw/` (PR #51).
- [x] «Listo para cierre» (puerta 2) recibido del director del proyecto el 2026-10-27.
- [x] Release v1.0.0 etiquetado y CHANGELOG actualizado (versión 1.0.0 del 2026-10-27); v1.1.0 con CC-PF-01-02.
- [ ] Post publicado, añadido a Destacados y registrado en el tablero de indicadores.
- [x] Gantt de seguimiento exportado de Project (`gestion/cronograma/PF-01_seguimiento.pdf`) y tabla de desvíos (`gestion/cronograma/PF-01_desvios.csv`), generada desde el XML del cronograma (sección 3.1).

## 2. Evaluación de objetivos

| ID | Objetivo | Resultado | Estado | Evidencia |
|---|---|---|---|---|
| O1 | Base reproducible en Oracle con 9 cortes del Boletín Mensual (P001 a P004 y P009 a P016) | Cuadre con los totales publicados en 7 544 de 7 544 combinaciones; Activo = Pasivo + Patrimonio en 504 de 504; P009 a P016 iguales a S-401, S-402 y S-403 en 8 778 de 8 778 celdas. Terminado el 2026-10-14, 18 días hábiles antes de la fecha del objetivo (2026-11-09) | Cumplido | `reports/validacion_datos.md`; #6, PR #33 |
| O2 | Matriz de cuatro cuadrantes de los riesgos con primas de al menos S/ 5 millones, con la siniestralidad del sistema replicada con una diferencia no mayor de 0.1 p. p. | 35 riesgos clasificados (9 · 12 · 7 · 7); índice del sistema de agosto de 2026 calculado igual al publicado en P015 y P016 (48.9141 % y 45.7487 %; diferencia de 0.0000 p. p.). Terminado el 2026-10-18, 20 días hábiles antes de la fecha del objetivo (2026-11-16) | Cumplido | `reports/validacion_resultados.md`; #8, PR #41; #9, PR #43 |
| O3 | Release v1.0.0, README, documento PDF y post de LinkedIn | README publicado el 2026-10-26 (#12, PR #51); release, documento PDF y post pendientes para la publicación del 2026-11-26 | En curso | #14, #15 y #16 |

*Nota.* Elaboración propia con datos de la Superintendencia de Banca, Seguros y AFP (SBS, s. f.) y los informes de validación del repositorio.

## 3. Línea base frente a avance real

### 3.1 Fechas

El cronograma tiene tres líneas base: la Baseline (v1.0, aprobada el 2026-10-11), la Baseline1 (inicio adelantado y paquetes 2.4 y 3.4, fijada el mismo día) y la Baseline2 (horas de 4.2 por D-PF01-24, fijada el 2026-10-26). La Baseline2 se fijó sobre todo el proyecto cuando 13 tareas ya tenían fechas reales, así que repite esas fechas y no sirve como referencia; la comparación usa la v1.0 y la Baseline1.

| Paquete | Fin v1.0 | Fin Baseline1 | Inicio real | Fin real | Desvío frente a v1.0 (días hábiles) | Desvío frente a Baseline1 (días hábiles) |
|---|---|---|---|---|---:|---:|
| 1.1 Acta | 2026-10-13 | 2026-10-11 | 2026-10-10 | 2026-10-11 | −1 | 0 |
| 1.2 Plan y línea base | 2026-10-16 | 2026-10-11 | 2026-10-11 | 2026-10-11 | −4 | 0 |
| 2.1 Extracción | 2026-11-03 | 2026-10-11 | 2026-10-11 | 2026-10-11 | −16 | 0 |
| 2.2 Validación | 2026-11-05 | 2026-10-13 | 2026-10-11 | 2026-10-11 | −18 | −1 |
| 2.3 Modelo de datos Oracle | 2026-11-09 | 2026-10-15 | 2026-10-11 | 2026-10-14 | −18 | −1 |
| 2.4 Arquitectura en Visio (opcional) | No aplica | 2026-10-16 | 2026-10-14 | 2026-10-14 | No aplica | −2 |
| 3.1 Exploración | 2026-11-10 | 2026-10-16 | 2026-10-15 | 2026-10-15 | −18 | −1 |
| 3.2 Indicadores y matriz | 2026-11-12 | 2026-10-20 | 2026-10-18 | 2026-10-18 | −18 | −1 |
| 3.3 Validación de resultados | 2026-11-13 | 2026-10-21 | 2026-10-18 | 2026-10-18 | −19 | −2 |
| 3.4 Proceso en Bizagi (opcional) | No aplica | 2026-10-22 | 2026-10-18 | 2026-10-21 | No aplica | −1 |
| 4.1 Tablero Power BI | 2026-11-18 | 2026-10-26 | 2026-10-22 | 2026-10-26 | −17 | 0 |
| 4.2 Informe | 2026-11-19 | 2026-10-27 | 2026-10-26 | 2026-10-26 | −18 | −1 |
| 4.3 README | 2026-11-20 | 2026-10-28 | 2026-10-26 | 2026-10-26 | −19 | −2 |
| 1.3 Cierre | 2026-11-23 | 2026-10-29 | 2026-10-26 | 2026-10-27 | −19 | −2 |

*Nota.* Elaboración propia con la Baseline, la Baseline1 y las fechas reales de `gestion/cronograma/PF-01_cronograma.xml`. Días hábiles de lunes a viernes, sin feriados en la ventana del proyecto; un valor negativo es adelanto. Las mismas cifras están en `PF-01_desvios.csv`, que se generó desde ese XML con los campos de la tabla Variación de Project más la Baseline1, porque la exportación a CSV de Project quedó bloqueada por la opción de formatos heredados (sección 4).

Desvíos mayores que 2 días hábiles. Todos los paquetes del núcleo terminaron entre 16 y 19 días hábiles antes de la v1.0 por una sola causa: el control de cambios del 2026-10-11 adelantó el inicio de la ejecución tres semanas (de 2026-11-02 a 2026-10-11) y se replanificó en la Baseline1. Frente a la Baseline1 ningún paquete se desvía más de 2 días hábiles. La fecha de publicación (2026-11-26) no se movió, porque la fija el calendario editorial.

Desvíos de duración. 4.2 y 4.3 se trabajaron fuera del horario del calendario (09:00 a 18:00), así que Project registró una duración de 0 días y los marcó como hitos; se desmarcaron y se conservaron las fechas reales (lección L-PF01-78). En 3.1, 3.2 y 3.3 se usó el calendario «24 horas» con la duración en minutos (L-PF01-52).

### 3.2 Esfuerzo

| Paquete | Estimado (h) | Real (h) | Desvío (h) | Causa principal del desvío |
|---|---:|---:|---:|---|
| 1.1 Acta | 1.0 | 1.7 | +0.7 | Iteraciones del acta y primer uso de Claude Code |
| 1.2 Plan y línea base | 1.5 | 3.0 | +1.5 | Calendario de fin de semana, hitos y fechas con hora en Project (L-PF01-06) |
| 2.1 y 2.2 Extracción y validación | 7.0 | 2.4 | −4.6 | La estimación suponía trabajo manual; Claude Code automatizó la descarga, la extracción y los controles |
| 2.3 Modelo de datos Oracle | 5.0 | 11.8 | +6.8 | Incidencias del Data Modeler y validación completa en la base nativa y en el contenedor |
| 2.4 Arquitectura en Visio | 2.0 | 7.9 | +5.9 | El alcance cambió tres veces en un día; cinco versiones del boceto; incluye una exploración de ratios fuera de alcance |
| 3.1 Exploración | 1.0 | 1.3 | +0.3 | Revisión y registro en Project |
| 3.2 Indicadores y matriz | 2.0 | 3.5 | +1.5 | Reingeniería descartada del modelo en el Data Modeler (≈ 0.8 h) |
| 3.3 Validación de resultados | 1.0 | 1.5 | +0.5 | Correcciones del registro en Project |
| 3.4 Proceso en Bizagi | 3.5 | 4.7 | +1.2 | Verificación del `.bpm` guardado por guardado y exportaciones repetidas |
| 4.1 Tablero Power BI | 4.0 | 4.3 | +0.3 | Cultura de los CSV y formatos de la cinta (L-PF01-67 y L-PF01-68) |
| 4.2 Informe | 2.0 | 1.1 | −0.9 | Insumos listos en las notas de validación y el tablero |
| 4.3 README | 1.0 | 0.6 | −0.4 | Insumos listos; ciclo completo desde el chat |
| 1.3 Cierre | 1.0 | 0.6 | −0.4 | Reconstrucción de horas y desvíos delegada en lecturas automáticas de los chats |
| Total de los paquetes terminados | 32.0 | 44.6 | +12.6 | |

*Nota.* Elaboración propia. Las horas no se cronometraron: son la suma de las ventanas de sesión (del primer al último mensaje; una pausa de más de 60 minutos abre una sesión nueva), tomadas de los resúmenes de continuidad y de las marcas de hora de los chats, y validadas por el director del proyecto el 2026-10-27; las de 1.3 llegan hasta el registro del avance en Project (2026-10-27, 20:18). Son un piso: no incluyen el trabajo antes del primer mensaje ni después del último, e incluyen la gestión hecha en la misma sesión.

| Indicador | Plan | Real | Desvío |
|---|---|---|---|
| Esfuerzo del núcleo, paquetes terminados (h) | 26.5 | 32.0 | +5.5 h (+20.8 %) |
| Esfuerzo de los opcionales (h) | 5.5 | 12.6 | +7.1 h (+129.1 %) |
| Esfuerzo total del PF (h) | 34.5 | Pendiente (faltan 5.1 a 5.3) | Pendiente |
| Fecha de publicación | 2026-11-26 (2026-11-12 desde CC-PF-01-02) | Pendiente | Pendiente |
| Cambios aprobados | No aplica | 9 controles de cambios y 1 enmienda en el issue #1, más las solicitudes CC-PF-01-01 y CC-PF-01-02 | No aplica |

Las filas de la tabla de esfuerzo, redondeadas a un decimal, suman 44.4 h (31.8 h de núcleo y 12.6 h de opcionales); el total validado por el director del proyecto el 2026-10-27 es 44.6 h. La diferencia de 0.2 h no se puede conciliar con los datos disponibles y se revisa en el cierre de 5.3; las cifras de la sección 3.3 usan el total validado.

### 3.3 Valor ganado en horas

Project no registra trabajo ni costo (sin recursos asignados), así que el valor ganado se calcula en horas con la estimación de cada paquete como valor planificado y la Baseline1 como línea base de control. Fecha de estado: 2026-10-27, después de cerrar 1.3.

| Indicador | Fórmula | Valor |
|---|---|---|
| Valor planificado (PV) | Horas estimadas de los paquetes que la Baseline1 preveía terminar al 2026-10-27 (todos, menos 4.3 del 28/10 y 1.3 del 29/10) | 30.0 h |
| Valor ganado (EV) | Horas estimadas de los paquetes terminados | 32.0 h |
| Costo real (AC) | Horas reales de los paquetes terminados | 44.6 h |
| Índice de desempeño del cronograma (SPI) | EV / PV | 1.07 |
| Índice de desempeño del costo (CPI) | EV / AC | 0.72 |

*Nota.* Elaboración propia con las tablas 3.1 y 3.2. Cada hora planificada costó 1.39 h reales (1 / CPI). El SPI frente a la línea base v1.0 no mide desempeño: la v1.0 preveía empezar la ejecución el 2026-11-02 y el proyecto empezó el 2026-10-11, así que casi todo el trabajo terminó antes de su fecha planificada.

## 4. Lecciones aprendidas

Resumen de las lecciones L-PF01-01 a L-PF01-85; el detalle está en el registro de lecciones del portafolio.

| Qué funcionó | Qué no funcionó | Causa | Acción para el siguiente proyecto | ¿Cambia instrucciones, plantillas, fichas o skills? |
|---|---|---|---|---|
| Adelantar el inicio y replanificar en la Baseline1 dejó el núcleo terminado entre 16 y 19 días hábiles antes de la v1.0 | La Baseline2 repite las fechas reales y no sirve para medir desvíos | Se fijó sobre todo el proyecto cuando la mayoría de los paquetes ya tenía avance | Un cambio de horas sin tareas nuevas se registra en la columna «Horas» y en el control de cambios; si se fija otra línea base, se declara cuál es la de control | Sí: skill `portafolio-ms-project` |
| La doble implementación de las reglas (SQL y Python) con pruebas cruzadas y cifras de oráculo convirtió la validación de O2 en una comprobación mecánica (L-PF01-42 y L-PF01-50) | No aplica | No aplica | Repetirlo en todo PF con vistas analíticas | No |
| No aplica | 2.3 y 2.4 superaron su estimación en 6.8 h y 5.9 h | Herramientas sin uso previo en el portafolio (Data Modeler, Visio) y alcance de páginas decidido durante la ejecución (L-PF01-32) | Estimar con margen las herramientas nuevas y cerrar el alcance de cada diagrama, con su boceto, en la Fase 1 | Sí: skill `portafolio-acta-proyecto` |
| No aplica | Las horas reales no se cronometraron y hubo que reconstruirlas al cierre | Ni los resúmenes ni el GitHub Project tenían un campo de horas reales (D15 pendiente) | Registrar el inicio y el fin de cada sesión en su resumen y las horas reales al cerrar cada issue | Sí: skill `portafolio-cierre-retro` y `14_indicadores_gestion.md` |
| El estado de commit requerido `revision/claude` impidió fusionar antes de la revisión (L-PF01-82) | Siete PR (#43 y #45 a #50) se fusionaron antes del «Conforme para fusionar» (L-PF01-57, L-PF01-66, L-PF01-76 y L-PF01-79) | El control era solo conversacional | Proteger `main` con el estado requerido desde el primer PR | Ya incorporado: instrucciones v1.13 |
| Las excepciones de la fuente registradas en un catálogo mantuvieron la serie comparable sin ocultar diferencias (L-PF01-54) | La SBS no usa un criterio único para el índice publicado ni un formato único de archivo (L-PF01-12) | Cada corte se publica con la herramienta y el criterio de ese momento | Validar la estructura por corte y registrar las excepciones antes de calcular | Ya incorporado: catálogo 05 |
| No aplica | Trabajar fuera del horario del calendario convirtió tareas en hitos de duración 0 en cinco paquetes (3.1 a 3.3, 4.2 y 4.3) (L-PF01-06, L-PF01-52 y L-PF01-78) | El calendario del PF tiene la jornada predeterminada, no las horas reales de trabajo | Definir en la Fase 1 un calendario con las horas reales de trabajo | Sí: skill `portafolio-ms-project` |
| Las reglas de `.gitattributes` por tipo de archivo evitaron cambios espurios entre Windows y Linux (L-PF01-10, L-PF01-64 y L-PF01-83) | Cada tipo nuevo (CSV, SVG, BPMN, XML) necesitó un PR propio para su regla | La plantilla no traía las reglas | Plantilla con todas las reglas desde el inicio | Sí: skill `portafolio-repo-scaffold` |
| Con las carpetas conectadas, Claude escribió y verificó en el equipo, y el ciclo de un issue de documentación cupo en el chat (L-PF01-37, L-PF01-80 y L-PF01-85) | No aplica | No aplica | Conectar la carpeta del repositorio al iniciar cada sesión | Ya incorporado: instrucciones v1.11 y v1.13 |
| La tabla de desvíos se generó desde el XML exportado por Project, con los mismos campos y sin tocar la seguridad del equipo | Guardar como CSV falló por la opción «Formatos heredados» del Centro de confianza y, al habilitarla, el asistente usó el mapa genérico de tareas (separado por tabulaciones, en ANSI y sin las variaciones de comienzo y fin) | Project trata el CSV como formato heredado y el asistente no parte de la tabla activa | Generar `PF-XX_desvios.csv` desde el XML del cronograma con un script, en UTF-8 y con LF | Sí: skill `portafolio-ms-project`, sección C.2 |

## 5. Retrospectiva de la colaboración con Claude

- Instrucciones o datos que faltaron: un registro de horas reales por sesión; el calendario real de trabajo para Project; un control mecánico de fusión, que llegó recién con la versión 1.13 de las instrucciones; y la regla de qué línea base se usa para medir desvíos.
- Prompts de Claude Code que conviene reutilizar: el prompt base con verificación del punto de partida (`git status -sb`, `git log -1 --oneline`) y parada si no coincide (L-PF01-58); commits con rutas explícitas y sin `gestion/cronograma/` en los commits de código; toda afirmación de resultado acompañada de la salida real del comando (L-PF01-44 y L-PF01-48).
- Skills que convendría crear o mejorar: mejorar `portafolio-ms-project` (calendario y línea base de control), `portafolio-cierre-retro` (horas reales) y `portafolio-repo-scaffold` (reglas de `.gitattributes` y protección de `main`). Crear una skill de carga en Oracle solo si PF-02 vuelve a usar el mismo flujo (sección 7 de las instrucciones: dos proyectos o más).

## 6. Limitaciones conocidas

- En P001 de diciembre de 2021, la nota al pie «*Actualizado al 01/09/2022» entra como cuenta en `dim_cuenta` porque trae un 0 en una columna de empresa; no afecta los cuadres. Se cerró como «no se hará» por la solicitud de cambio CC-PF-01-01 (#34).

## 7. Propuestas de mejora (máximo 3)

| N.º | Archivo afectado | Texto exacto del cambio | Nueva versión |
|---|---|---|---|
| 1 | Skill `portafolio-cierre-retro`, sección 1 | Agregar al reporte por sesión: «- Horas: inicio y fin de la sesión (hora de Lima) y horas atribuibles a cada issue». Agregar en la sección 3, paso 2: «Si faltan horas reales, se reconstruyen con las ventanas de sesión (resúmenes y marcas de hora de los chats; una pausa de más de 60 minutos abre una sesión nueva), se declaran como piso y José las valida» | v1.4 |
| 2 | Skill `portafolio-ms-project`, sección A.3 y sección C | A.3: «El calendario del PF cubre las horas reales de trabajo de José, incluidas noches y fines de semana; si no, las tareas de ejecución usan el calendario "24 horas"». C.1: «La comparación de cierre usa la v1.0 y la última línea base fijada antes del primer avance real de cada paquete; una línea base fijada con fechas reales no se usa para medir desvíos» | v1.5 |
| 3 | Skill `portafolio-acta-proyecto`, estimación de la EDT | «Los paquetes que usan una herramienta sin uso previo en el portafolio o que requieren boceto aprobado llevan su alcance de páginas cerrado en la Fase 1 y un margen de estimación declarado en el acta» | Siguiente versión |

## Referencias

Superintendencia de Banca, Seguros y AFP. (s. f.). *Boletín mensual* [Conjunto de datos]. Recuperado el 11 de octubre de 2026, de https://www.sbs.gob.pe/app/stats_net/stats/EstadisticaSistemaFinancieroResultados.aspx?c=S-367
