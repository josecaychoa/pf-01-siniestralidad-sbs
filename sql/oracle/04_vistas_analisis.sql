-- =============================================================================
-- PF-01 · Producción y siniestralidad por riesgo del mercado asegurador
-- peruano, 2019-2026
-- Script:  sql/oracle/04_vistas_analisis.sql
-- Paquete: 3.2 Indicadores y matriz (issue #8)
-- =============================================================================
--
-- Propósito
--   Crea las vistas vw_ del análisis, que programan las decisiones de diseño
--   de 3.2 (D-PF01-11 a D-PF01-16) sobre las tablas dim_ y fct_:
--   - vw_parametros_analisis: parámetros con nombre (umbral de primas y corte
--     de crecimiento), en una fila.
--   - vw_cortes_analisis: cortes del análisis derivados de dim_corte (actual,
--     anterior e inicio y fin de la TCAC), en una fila.
--   - vw_base_riesgo_comparable: cifras sin redondear por corte y riesgo
--     comparable; base de las vistas de presentación.
--   - vw_indicadores_riesgo: serie por corte y riesgo comparable, con los
--     índices de siniestralidad calculados y los publicados como control.
--   - vw_crecimiento_riesgo: variación interanual, TCAC y umbral por riesgo
--     comparable.
--   - vw_matriz_riesgo: matriz de cuatro cuadrantes en el corte actual.
--   - vw_participacion_empresa_riesgo: apertura por empresa y riesgo, con la
--     clasificación de los índices por celda.
--
-- Orden de ejecución
--   Después de 01_ddl_tablas.sql (tablas) y de 02_vistas.sql, y antes de la
--   carga de datos. Las vistas dependen entre sí en este orden: parámetros y
--   cortes; base; indicadores y crecimiento; matriz; participación.
--
-- Requisitos
--   - Oracle Database 23ai o posterior. Desarrollo en la base nativa 23.6
--     (D-PF01-03); validación final en el contenedor gvenzl/oracle-free:23.26.3.
--   - Usuario del proyecto con privilegio CREATE VIEW.
--   - Ejecución con SQLcl o SQL*Plus, por ejemplo:
--       sql pf01@localhost:1521/FREEPDB1 @sql/oracle/04_vistas_analisis.sql
--
-- Idempotencia
--   CREATE OR REPLACE VIEW (Oracle no admite IF NOT EXISTS junto con OR
--   REPLACE: ORA-11541) y COMMENT ON, que reemplaza el texto en cada ejecución.
--
-- Convenciones
--   - Las filas del análisis son las agrupaciones de dim_riesgo.riesgo_comparable
--     de los riesgos de tipo riesgo (D-PF01-12); las cifras de cada fila salen
--     de la columna Total de cada hoja: la ampliada («Total + …») si la hoja
--     la publica; si no, la simple («Total»).
--   - Los índices de siniestralidad de cada fila se calculan como
--     Σ siniestros / Σ primas del mismo corte: directa con netos y netas,
--     retenida con retenidos y retenidas (D-PF01-12). Son nulos cuando el
--     denominador es 0 o negativo (D-PF01-14). Los publicados (P015 y P016) se
--     conservan como control en las filas de un solo riesgo.
--   - Crecimiento: la variación interanual (agosto frente a agosto) define el
--     eje y el cuadrante; la TCAC entre diciembres acompaña como segundo
--     atributo, con la marca signos_coinciden (D-PF01-11).
--   - Rentas y Sistema Privado de Pensiones se marcan con
--     siniestralidad_comparable = N (D-PF01-15): entran en la matriz con esa
--     marca y no participan en el corte de siniestralidad.
--   - Cortes de los cuadrantes: crecimiento 0 % y siniestralidad igual al
--     índice agregado de los riesgos comparables sobre el umbral (D-PF01-16).
--     Los dos cortes y el umbral son parámetros con nombre.
--   - Redondeo solo en las vistas de presentación (D-PF01-06): montos en miles
--     de soles a 2 decimales y porcentajes a 6 decimales; la vista base
--     conserva las cifras sin redondear.
--
-- Decisiones: D-PF01-11 (variación interanual y TCAC), D-PF01-12 (filas por
-- riesgo comparable e índices calculados), D-PF01-13 (índices atípicos se
-- marcan, no se truncan), D-PF01-14 (índice nulo sin primas), D-PF01-15
-- (atributo siniestralidad_comparable) y D-PF01-16 (cortes de los cuadrantes).
-- =============================================================================

WHENEVER SQLERROR EXIT FAILURE

PROMPT == 1. vw_parametros_analisis ==

-- 1. vw_parametros_analisis: parámetros con nombre (una fila).
CREATE OR REPLACE VIEW vw_parametros_analisis AS
SELECT 5000 AS umbral_primas,       -- miles de soles: primas netas acumuladas en el corte (acta, sección 4; O2)
       0    AS corte_crecimiento    -- porcentaje: crece si la variación es >= 0 (D-PF01-16)
  FROM dual;

COMMENT ON TABLE vw_parametros_analisis IS 'Parámetros con nombre del análisis de 3.2, en una fila: umbral de materialidad de las primas y corte de crecimiento de los cuadrantes (D-PF01-16)';
COMMENT ON COLUMN vw_parametros_analisis.umbral_primas IS 'Umbral de materialidad: primas netas acumuladas en el corte, en miles de soles (5 000; acta, sección 4; O2)';
COMMENT ON COLUMN vw_parametros_analisis.corte_crecimiento IS 'Corte de crecimiento de los cuadrantes, en porcentaje: una fila crece si su variación es mayor o igual que este valor (0; D-PF01-16)';

PROMPT == 2. vw_cortes_analisis ==

-- 2. vw_cortes_analisis: cortes del análisis derivados de dim_corte (una fila).
CREATE OR REPLACE VIEW vw_cortes_analisis AS
WITH agosto AS (
    SELECT MAX(fecha_corte) AS corte_actual FROM dim_corte WHERE meses_acumulados = 8
),
diciembre AS (
    SELECT MIN(fecha_corte) AS corte_inicio_tcac, MAX(fecha_corte) AS corte_fin_tcac
      FROM dim_corte WHERE meses_acumulados = 12
)
SELECT a.corte_actual,
       ADD_MONTHS(a.corte_actual, -12)                                AS corte_anterior,
       d.corte_inicio_tcac,
       d.corte_fin_tcac,
       MONTHS_BETWEEN(d.corte_fin_tcac, d.corte_inicio_tcac) / 12     AS anios_tcac
  FROM agosto a CROSS JOIN diciembre d;

COMMENT ON TABLE vw_cortes_analisis IS 'Cortes del análisis de 3.2 derivados de dim_corte, en una fila: corte actual (último de 8 meses), corte anterior (12 meses antes) e inicio y fin de la TCAC (primer y último corte de 12 meses) (D-PF01-11)';
COMMENT ON COLUMN vw_cortes_analisis.corte_actual IS 'Corte más reciente con 8 meses acumulados (agosto de 2026)';
COMMENT ON COLUMN vw_cortes_analisis.corte_anterior IS 'Corte actual menos 12 meses: base de la variación interanual (D-PF01-11)';
COMMENT ON COLUMN vw_cortes_analisis.corte_inicio_tcac IS 'Primer corte con 12 meses acumulados: inicio de la TCAC (diciembre de 2019)';
COMMENT ON COLUMN vw_cortes_analisis.corte_fin_tcac IS 'Último corte con 12 meses acumulados: fin de la TCAC (diciembre de 2025)';
COMMENT ON COLUMN vw_cortes_analisis.anios_tcac IS 'Años entre el inicio y el fin de la TCAC: meses entre los dos cortes divididos entre 12';

PROMPT == 3. vw_base_riesgo_comparable ==

-- 3. vw_base_riesgo_comparable: cifras sin redondear por corte y riesgo comparable (D-PF01-12).
--    Base de las vistas de presentación; no se consume directamente.
CREATE OR REPLACE VIEW vw_base_riesgo_comparable AS
WITH totales AS (
    -- Columna Total de cada corte, hoja y riesgo: la ampliada («Total + …») si la hoja la
    -- publica (incluye los flujos de las empresas que dejaron de operar en el año, hallazgo
    -- 10); si no, la simple («Total»). P015 y P016 no publican columna ampliada: en diciembre
    -- de 2022 su índice en «Total» corresponde a las cifras ampliadas de P009 a P014
    -- (Incendio: 21.134744 calculado y publicado); en diciembre de 2020, al Total simple,
    -- sin Rigel ni Coface (D-PF01-18). La serie usa la ampliada en los dos cortes y 3.3
    -- informa las diferencias de 2020 como excepciones de la fuente. El rótulo columna_total
    -- se toma de la hoja de primas netas (P009).
    SELECT f.fecha_corte, f.hoja, f.riesgo_id, f.valor, ce.clave_fuente,
           ROW_NUMBER() OVER (
               PARTITION BY f.fecha_corte, f.hoja, f.riesgo_id
               ORDER BY CASE ce.tipo_columna WHEN 'total_ampliado' THEN 1 ELSE 2 END, ce.columna_id
           ) AS orden
      FROM fct_riesgo f
      JOIN dim_columna_empresa ce ON ce.columna_id = f.columna_id
     WHERE ce.tipo_columna IN ('total_simple', 'total_ampliado')
),
por_riesgo AS (
    -- Una fila por corte y riesgo, con una medida por hoja.
    SELECT t.fecha_corte, t.riesgo_id,
           MAX(CASE WHEN t.hoja = 'P009' THEN t.valor END) AS primas_netas,
           MAX(CASE WHEN t.hoja = 'P011' THEN t.valor END) AS primas_retenidas,
           MAX(CASE WHEN t.hoja = 'P012' THEN t.valor END) AS siniestros_netos,
           MAX(CASE WHEN t.hoja = 'P014' THEN t.valor END) AS siniestros_retenidos,
           MAX(CASE WHEN t.hoja = 'P015' THEN t.valor END) AS indice_directa_publicado,
           MAX(CASE WHEN t.hoja = 'P016' THEN t.valor END) AS indice_retenida_publicado,
           MAX(CASE WHEN t.hoja = 'P009' THEN t.clave_fuente END) AS columna_total
      FROM totales t
     WHERE t.orden = 1
     GROUP BY t.fecha_corte, t.riesgo_id
)
SELECT p.fecha_corte,
       r.riesgo_comparable,
       COUNT(*)                                                           AS n_riesgos,
       MIN(r.ramo)                                                        AS ramo,
       MIN(r.siniestralidad_comparable)                                   AS siniestralidad_comparable,
       MIN(p.columna_total)                                               AS columna_total,
       SUM(p.primas_netas)                                                AS primas_netas,
       SUM(p.primas_retenidas)                                            AS primas_retenidas,
       SUM(p.siniestros_netos)                                            AS siniestros_netos,
       SUM(p.siniestros_retenidos)                                        AS siniestros_retenidos,
       -- El índice publicado solo existe para las filas de un riesgo (D-PF01-12).
       CASE WHEN COUNT(*) = 1 THEN MAX(p.indice_directa_publicado) END    AS indice_directa_publicado,
       CASE WHEN COUNT(*) = 1 THEN MAX(p.indice_retenida_publicado) END   AS indice_retenida_publicado
  FROM por_riesgo p
  JOIN dim_riesgo r ON r.riesgo_id = p.riesgo_id
 WHERE r.tipo = 'riesgo'
 GROUP BY p.fecha_corte, r.riesgo_comparable;

COMMENT ON TABLE vw_base_riesgo_comparable IS 'Base de las vistas de análisis: primas y siniestros sin redondear de la columna Total de cada hoja (la ampliada si existe; si no, la simple) por corte y riesgo comparable, sumando los riesgos de tipo riesgo de cada agrupación (D-PF01-12); no se consume directamente';
COMMENT ON COLUMN vw_base_riesgo_comparable.n_riesgos IS 'Riesgos de tipo riesgo que suma la agrupación en el corte (3 en Cauciones y fianzas desde diciembre de 2023; 1 en las demás)';
COMMENT ON COLUMN vw_base_riesgo_comparable.siniestralidad_comparable IS 'S si el índice de siniestralidad de la fila es comparable con el de los ramos generales; N en rentas y Sistema Privado de Pensiones (D-PF01-15)';
COMMENT ON COLUMN vw_base_riesgo_comparable.columna_total IS 'Rótulo de la columna Total de la que salen las primas netas (P009): la ampliada («Total + …») cuando la hoja la publica (diciembre de 2020 y de 2022), si no, «Total». P015 y P016 no publican columna ampliada: en diciembre de 2022 su índice en «Total» corresponde a las cifras ampliadas de P009 a P014 (Incendio: 21.134744 calculado y publicado) y en diciembre de 2020 al Total simple, sin Rigel ni Coface (D-PF01-18); la serie usa la ampliada en los dos cortes y 3.3 informa las diferencias de 2020 como excepciones de la fuente';
COMMENT ON COLUMN vw_base_riesgo_comparable.primas_netas IS 'Primas de seguros netas (P009), en miles de soles, acumuladas en el año; sin redondear';
COMMENT ON COLUMN vw_base_riesgo_comparable.primas_retenidas IS 'Primas retenidas (P011), en miles de soles, acumuladas en el año; sin redondear';
COMMENT ON COLUMN vw_base_riesgo_comparable.siniestros_netos IS 'Siniestros de primas de seguros netos (P012), en miles de soles, acumulados en el año; sin redondear';
COMMENT ON COLUMN vw_base_riesgo_comparable.siniestros_retenidos IS 'Siniestros retenidos (P014), en miles de soles, acumulados en el año; sin redondear';
COMMENT ON COLUMN vw_base_riesgo_comparable.indice_directa_publicado IS 'Índice de siniestralidad directa publicado por la SBS (P015), en porcentaje, sin redondear; solo en las filas de un riesgo (D-PF01-12)';
COMMENT ON COLUMN vw_base_riesgo_comparable.indice_retenida_publicado IS 'Índice de siniestralidad retenida publicado por la SBS (P016), en porcentaje, sin redondear; solo en las filas de un riesgo (D-PF01-12)';

PROMPT == 4. vw_indicadores_riesgo ==

-- 4. vw_indicadores_riesgo: serie por corte y riesgo comparable, con los índices calculados
--    (D-PF01-12 y D-PF01-14) y los publicados como control.
CREATE OR REPLACE VIEW vw_indicadores_riesgo AS
SELECT b.fecha_corte,
       co.meses_acumulados,
       b.riesgo_comparable,
       b.n_riesgos,
       b.ramo,
       b.siniestralidad_comparable,
       b.columna_total,
       ROUND(b.primas_netas, 2)          AS primas_netas,
       ROUND(b.primas_retenidas, 2)      AS primas_retenidas,
       ROUND(b.siniestros_netos, 2)      AS siniestros_netos,
       ROUND(b.siniestros_retenidos, 2)  AS siniestros_retenidos,
       CASE WHEN b.primas_netas > 0
            THEN ROUND(100 * b.siniestros_netos / b.primas_netas, 6) END           AS indice_siniestralidad_directa,
       CASE WHEN b.primas_retenidas > 0
            THEN ROUND(100 * b.siniestros_retenidos / b.primas_retenidas, 6) END   AS indice_siniestralidad_retenida,
       ROUND(b.indice_directa_publicado, 6)   AS indice_directa_publicado,
       ROUND(b.indice_retenida_publicado, 6)  AS indice_retenida_publicado
  FROM vw_base_riesgo_comparable b
  JOIN dim_corte co ON co.fecha_corte = b.fecha_corte;

COMMENT ON TABLE vw_indicadores_riesgo IS 'Serie por corte y riesgo comparable: primas y siniestros (miles de soles, 2 decimales), índices de siniestralidad calculados como Σ siniestros / Σ primas (porcentaje, 6 decimales; nulos sin primas, D-PF01-12 y D-PF01-14) y los publicados como control';
COMMENT ON COLUMN vw_indicadores_riesgo.columna_total IS 'Rótulo de la columna Total de la que salen las primas netas (P009): la ampliada («Total + …») cuando la hoja la publica (diciembre de 2020 y de 2022), si no, «Total». P015 y P016 no publican columna ampliada: en diciembre de 2022 su índice en «Total» corresponde a las cifras ampliadas de P009 a P014 (Incendio: 21.134744 calculado y publicado) y en diciembre de 2020 al Total simple, sin Rigel ni Coface (D-PF01-18); la serie usa la ampliada en los dos cortes y 3.3 informa las diferencias de 2020 como excepciones de la fuente';
COMMENT ON COLUMN vw_indicadores_riesgo.primas_netas IS 'Primas de seguros netas (P009), en miles de soles, acumuladas en el año; 2 decimales';
COMMENT ON COLUMN vw_indicadores_riesgo.primas_retenidas IS 'Primas retenidas (P011), en miles de soles, acumuladas en el año; 2 decimales';
COMMENT ON COLUMN vw_indicadores_riesgo.siniestros_netos IS 'Siniestros de primas de seguros netos (P012), en miles de soles, acumulados en el año; 2 decimales';
COMMENT ON COLUMN vw_indicadores_riesgo.siniestros_retenidos IS 'Siniestros retenidos (P014), en miles de soles, acumulados en el año; 2 decimales';
COMMENT ON COLUMN vw_indicadores_riesgo.indice_siniestralidad_directa IS 'Índice de siniestralidad directa calculado: 100 × siniestros netos / primas netas, en porcentaje; 6 decimales; nulo si las primas netas son 0 o negativas (D-PF01-12 y D-PF01-14)';
COMMENT ON COLUMN vw_indicadores_riesgo.indice_siniestralidad_retenida IS 'Índice de siniestralidad retenida calculado: 100 × siniestros retenidos / primas retenidas, en porcentaje; 6 decimales; nulo si las primas retenidas son 0 o negativas (D-PF01-12 y D-PF01-14)';
COMMENT ON COLUMN vw_indicadores_riesgo.indice_directa_publicado IS 'Índice de siniestralidad directa publicado por la SBS (P015), en porcentaje; 6 decimales; columna de control, solo en las filas de un riesgo';
COMMENT ON COLUMN vw_indicadores_riesgo.indice_retenida_publicado IS 'Índice de siniestralidad retenida publicado por la SBS (P016), en porcentaje; 6 decimales; columna de control, solo en las filas de un riesgo';

PROMPT == 5. vw_crecimiento_riesgo ==

-- 5. vw_crecimiento_riesgo: variación interanual, TCAC y umbral por riesgo comparable (D-PF01-11).
CREATE OR REPLACE VIEW vw_crecimiento_riesgo AS
WITH c AS (SELECT * FROM vw_cortes_analisis),
p AS (SELECT * FROM vw_parametros_analisis),
base AS (
    SELECT b.riesgo_comparable,
           MAX(b.ramo)                                                                   AS ramo,
           MAX(b.siniestralidad_comparable)                                              AS siniestralidad_comparable,
           MAX(CASE WHEN b.fecha_corte = c.corte_actual      THEN b.n_riesgos END)      AS n_riesgos,
           SUM(CASE WHEN b.fecha_corte = c.corte_actual      THEN b.primas_netas END)   AS primas_actual,
           SUM(CASE WHEN b.fecha_corte = c.corte_anterior    THEN b.primas_netas END)   AS primas_anterior,
           SUM(CASE WHEN b.fecha_corte = c.corte_inicio_tcac THEN b.primas_netas END)   AS primas_inicio_tcac,
           SUM(CASE WHEN b.fecha_corte = c.corte_fin_tcac    THEN b.primas_netas END)   AS primas_fin_tcac
      FROM vw_base_riesgo_comparable b
     CROSS JOIN c
     GROUP BY b.riesgo_comparable
),
medidas AS (
    SELECT b.*,
           CASE WHEN b.primas_anterior > 0
                THEN 100 * (b.primas_actual / b.primas_anterior - 1) END                              AS variacion_interanual,
           CASE WHEN b.primas_inicio_tcac > 0 AND b.primas_fin_tcac > 0 AND c.anios_tcac > 0
                THEN 100 * (POWER(b.primas_fin_tcac / b.primas_inicio_tcac, 1 / c.anios_tcac) - 1) END AS tcac
      FROM base b CROSS JOIN c
)
SELECT m.riesgo_comparable,
       m.n_riesgos,
       m.ramo,
       m.siniestralidad_comparable,
       c.corte_actual,
       c.corte_anterior,
       c.corte_inicio_tcac,
       c.corte_fin_tcac,
       ROUND(m.primas_actual, 2)        AS primas_actual,
       ROUND(m.primas_anterior, 2)      AS primas_anterior,
       ROUND(m.primas_inicio_tcac, 2)   AS primas_inicio_tcac,
       ROUND(m.primas_fin_tcac, 2)      AS primas_fin_tcac,
       ROUND(m.variacion_interanual, 6) AS variacion_interanual,
       ROUND(m.tcac, 6)                 AS tcac,
       CASE WHEN m.variacion_interanual IS NULL OR m.tcac IS NULL THEN NULL
            WHEN SIGN(m.variacion_interanual) = SIGN(m.tcac) THEN 'S' ELSE 'N' END AS signos_coinciden,
       p.umbral_primas,
       CASE WHEN m.primas_actual >= p.umbral_primas THEN 'S' ELSE 'N' END        AS sobre_umbral
  FROM medidas m CROSS JOIN c CROSS JOIN p;

COMMENT ON TABLE vw_crecimiento_riesgo IS 'Crecimiento por riesgo comparable: variación interanual de las primas netas (corte actual frente al anterior), TCAC entre el primer y el último diciembre, coincidencia de signos y marca de umbral (D-PF01-11); porcentajes a 6 decimales y montos en miles de soles a 2 decimales';
COMMENT ON COLUMN vw_crecimiento_riesgo.primas_actual IS 'Primas netas acumuladas en el corte actual, en miles de soles; 2 decimales';
COMMENT ON COLUMN vw_crecimiento_riesgo.primas_anterior IS 'Primas netas acumuladas en el corte anterior (12 meses antes), en miles de soles; 2 decimales';
COMMENT ON COLUMN vw_crecimiento_riesgo.primas_inicio_tcac IS 'Primas netas del primer corte de 12 meses (inicio de la TCAC), en miles de soles; 2 decimales';
COMMENT ON COLUMN vw_crecimiento_riesgo.primas_fin_tcac IS 'Primas netas del último corte de 12 meses (fin de la TCAC), en miles de soles; 2 decimales';
COMMENT ON COLUMN vw_crecimiento_riesgo.variacion_interanual IS 'Variación de las primas netas del corte actual frente al anterior: 100 × (actual / anterior - 1), en porcentaje; 6 decimales; nula si las primas anteriores son 0 o negativas; define el eje de crecimiento y el cuadrante (D-PF01-11)';
COMMENT ON COLUMN vw_crecimiento_riesgo.tcac IS 'Tasa de crecimiento anual compuesta de las primas netas entre el inicio y el fin de la TCAC: 100 × ((fin / inicio)^(1 / años) - 1), en porcentaje; 6 decimales; nula si alguna de las dos primas es 0 o negativa; segundo atributo de crecimiento (D-PF01-11)';
COMMENT ON COLUMN vw_crecimiento_riesgo.signos_coinciden IS 'S si la variación interanual y la TCAC tienen el mismo signo; N si discrepan (marca de D-PF01-11); nulo si falta alguna de las dos';
COMMENT ON COLUMN vw_crecimiento_riesgo.umbral_primas IS 'Umbral de materialidad de vw_parametros_analisis, en miles de soles';
COMMENT ON COLUMN vw_crecimiento_riesgo.sobre_umbral IS 'S si las primas netas del corte actual alcanzan el umbral de materialidad; N si no';

PROMPT == 6. vw_matriz_riesgo ==

-- 6. vw_matriz_riesgo: matriz de cuatro cuadrantes en el corte actual (D-PF01-11, 13, 15 y 16).
--    Cuadrantes: 1 crece con siniestralidad sobre el corte; 2 crece con siniestralidad bajo el
--    corte; 3 decrece con siniestralidad sobre el corte; 4 decrece con siniestralidad bajo el
--    corte. Crece: variación >= corte_crecimiento; sobre el corte: índice > corte de
--    siniestralidad. Nulo si la fila está bajo el umbral, no es comparable (rentas y SPP) o no
--    tiene crecimiento o índice definidos.
CREATE OR REPLACE VIEW vw_matriz_riesgo AS
WITH c AS (SELECT * FROM vw_cortes_analisis),
p AS (SELECT * FROM vw_parametros_analisis),
actual AS (
    SELECT b.* FROM vw_base_riesgo_comparable b CROSS JOIN c WHERE b.fecha_corte = c.corte_actual
),
g AS (SELECT * FROM vw_crecimiento_riesgo),
corte AS (
    -- Corte de siniestralidad (D-PF01-16): índice agregado de los riesgos comparables sobre el umbral.
    SELECT 100 * SUM(a.siniestros_netos) / SUM(a.primas_netas)           AS corte_directa,
           100 * SUM(a.siniestros_retenidos) / SUM(a.primas_retenidas)   AS corte_retenida
      FROM actual a
      JOIN g ON g.riesgo_comparable = a.riesgo_comparable
     WHERE a.siniestralidad_comparable = 'S' AND g.sobre_umbral = 'S'
),
filas AS (
    SELECT a.riesgo_comparable, a.n_riesgos, a.ramo, a.siniestralidad_comparable,
           a.primas_netas, a.primas_retenidas, a.siniestros_netos, a.siniestros_retenidos,
           100 * a.primas_netas / SUM(a.primas_netas) OVER ()                           AS participacion_sistema,
           CASE WHEN a.primas_netas > 0 THEN 100 * a.siniestros_netos / a.primas_netas END             AS indice_directa,
           CASE WHEN a.primas_retenidas > 0 THEN 100 * a.siniestros_retenidos / a.primas_retenidas END AS indice_retenida,
           a.indice_directa_publicado, a.indice_retenida_publicado,
           g.variacion_interanual, g.tcac, g.signos_coinciden, g.sobre_umbral,
           k.corte_directa, k.corte_retenida
      FROM actual a
      JOIN g ON g.riesgo_comparable = a.riesgo_comparable
     CROSS JOIN corte k
)
SELECT f.riesgo_comparable,
       f.n_riesgos,
       f.ramo,
       f.siniestralidad_comparable,
       c.corte_actual,
       c.corte_anterior,
       c.corte_inicio_tcac,
       c.corte_fin_tcac,
       ROUND(f.primas_netas, 2)              AS primas_netas,
       ROUND(f.primas_retenidas, 2)          AS primas_retenidas,
       ROUND(f.siniestros_netos, 2)          AS siniestros_netos,
       ROUND(f.siniestros_retenidos, 2)      AS siniestros_retenidos,
       ROUND(f.participacion_sistema, 6)     AS participacion_sistema,
       f.variacion_interanual,
       f.tcac,
       f.signos_coinciden,
       ROUND(f.indice_directa, 6)            AS indice_siniestralidad_directa,
       ROUND(f.indice_retenida, 6)           AS indice_siniestralidad_retenida,
       ROUND(f.indice_directa_publicado, 6)  AS indice_directa_publicado,
       ROUND(f.indice_retenida_publicado, 6) AS indice_retenida_publicado,
       p.umbral_primas,
       f.sobre_umbral,
       p.corte_crecimiento,
       ROUND(f.corte_directa, 6)             AS corte_siniestralidad_directa,
       ROUND(f.corte_retenida, 6)            AS corte_siniestralidad_retenida,
       CASE WHEN f.sobre_umbral = 'N' OR f.siniestralidad_comparable = 'N'
              OR f.variacion_interanual IS NULL OR f.indice_directa IS NULL THEN NULL
            WHEN f.variacion_interanual >= p.corte_crecimiento AND f.indice_directa > f.corte_directa THEN 1
            WHEN f.variacion_interanual >= p.corte_crecimiento THEN 2
            WHEN f.indice_directa > f.corte_directa THEN 3
            ELSE 4 END                        AS cuadrante_interanual_directa,
       CASE WHEN f.sobre_umbral = 'N' OR f.siniestralidad_comparable = 'N'
              OR f.variacion_interanual IS NULL OR f.indice_retenida IS NULL THEN NULL
            WHEN f.variacion_interanual >= p.corte_crecimiento AND f.indice_retenida > f.corte_retenida THEN 1
            WHEN f.variacion_interanual >= p.corte_crecimiento THEN 2
            WHEN f.indice_retenida > f.corte_retenida THEN 3
            ELSE 4 END                        AS cuadrante_interanual_retenida,
       CASE WHEN f.sobre_umbral = 'N' OR f.siniestralidad_comparable = 'N'
              OR f.tcac IS NULL OR f.indice_directa IS NULL THEN NULL
            WHEN f.tcac >= p.corte_crecimiento AND f.indice_directa > f.corte_directa THEN 1
            WHEN f.tcac >= p.corte_crecimiento THEN 2
            WHEN f.indice_directa > f.corte_directa THEN 3
            ELSE 4 END                        AS cuadrante_tcac_directa,
       CASE WHEN f.sobre_umbral = 'N' OR f.siniestralidad_comparable = 'N'
              OR f.tcac IS NULL OR f.indice_retenida IS NULL THEN NULL
            WHEN f.tcac >= p.corte_crecimiento AND f.indice_retenida > f.corte_retenida THEN 1
            WHEN f.tcac >= p.corte_crecimiento THEN 2
            WHEN f.indice_retenida > f.corte_retenida THEN 3
            ELSE 4 END                        AS cuadrante_tcac_retenida,
       CASE WHEN f.sobre_umbral = 'N' THEN 'Bajo el umbral'
            WHEN f.siniestralidad_comparable = 'N' THEN 'No comparable (rentas y SPP)'
            WHEN f.variacion_interanual IS NULL OR f.indice_directa IS NULL THEN 'Sin medida definida'
            ELSE 'En la matriz' END          AS situacion
  FROM filas f CROSS JOIN c CROSS JOIN p;

COMMENT ON TABLE vw_matriz_riesgo IS 'Matriz de cuatro cuadrantes de crecimiento y siniestralidad en el corte actual, una fila por riesgo comparable: 1 crece con siniestralidad sobre el corte, 2 crece bajo el corte, 3 decrece sobre el corte, 4 decrece bajo el corte; cuadrante nulo bajo el umbral, en rentas y SPP o sin medida definida (D-PF01-11, D-PF01-13, D-PF01-15 y D-PF01-16)';
COMMENT ON COLUMN vw_matriz_riesgo.primas_netas IS 'Primas de seguros netas (P009) del corte actual, en miles de soles; 2 decimales';
COMMENT ON COLUMN vw_matriz_riesgo.primas_retenidas IS 'Primas retenidas (P011) del corte actual, en miles de soles; 2 decimales';
COMMENT ON COLUMN vw_matriz_riesgo.siniestros_netos IS 'Siniestros de primas de seguros netos (P012) del corte actual, en miles de soles; 2 decimales';
COMMENT ON COLUMN vw_matriz_riesgo.siniestros_retenidos IS 'Siniestros retenidos (P014) del corte actual, en miles de soles; 2 decimales';
COMMENT ON COLUMN vw_matriz_riesgo.participacion_sistema IS 'Primas netas de la fila sobre la suma de primas netas de todas las filas del corte actual, en porcentaje; 6 decimales';
COMMENT ON COLUMN vw_matriz_riesgo.variacion_interanual IS 'Variación de las primas netas frente al corte anterior, en porcentaje; 6 decimales; eje de crecimiento por defecto (D-PF01-11)';
COMMENT ON COLUMN vw_matriz_riesgo.tcac IS 'Tasa de crecimiento anual compuesta de las primas netas entre diciembre de 2019 y diciembre de 2025, en porcentaje; 6 decimales; segundo atributo de crecimiento (D-PF01-11)';
COMMENT ON COLUMN vw_matriz_riesgo.signos_coinciden IS 'S si la variación interanual y la TCAC tienen el mismo signo; N si discrepan (marca de D-PF01-11); nulo si falta alguna';
COMMENT ON COLUMN vw_matriz_riesgo.indice_siniestralidad_directa IS 'Índice de siniestralidad directa calculado: 100 × siniestros netos / primas netas, en porcentaje; 6 decimales; nulo sin primas (D-PF01-12 y D-PF01-14); los valores negativos o mayores que 100 se conservan (D-PF01-13)';
COMMENT ON COLUMN vw_matriz_riesgo.indice_siniestralidad_retenida IS 'Índice de siniestralidad retenida calculado: 100 × siniestros retenidos / primas retenidas, en porcentaje; 6 decimales; nulo sin primas (D-PF01-12 y D-PF01-14); los valores negativos o mayores que 100 se conservan (D-PF01-13)';
COMMENT ON COLUMN vw_matriz_riesgo.indice_directa_publicado IS 'Índice de siniestralidad directa publicado por la SBS (P015), en porcentaje; 6 decimales; columna de control, solo en las filas de un riesgo';
COMMENT ON COLUMN vw_matriz_riesgo.indice_retenida_publicado IS 'Índice de siniestralidad retenida publicado por la SBS (P016), en porcentaje; 6 decimales; columna de control, solo en las filas de un riesgo';
COMMENT ON COLUMN vw_matriz_riesgo.umbral_primas IS 'Umbral de materialidad de vw_parametros_analisis, en miles de soles';
COMMENT ON COLUMN vw_matriz_riesgo.sobre_umbral IS 'S si las primas netas del corte actual alcanzan el umbral de materialidad; N si no (la fila sale de los cuadrantes)';
COMMENT ON COLUMN vw_matriz_riesgo.corte_crecimiento IS 'Corte de crecimiento de vw_parametros_analisis, en porcentaje: crece si la variación es mayor o igual (D-PF01-16)';
COMMENT ON COLUMN vw_matriz_riesgo.corte_siniestralidad_directa IS 'Corte de siniestralidad directa: 100 × Σ siniestros netos / Σ primas netas de las filas comparables sobre el umbral en el corte actual, en porcentaje; 6 decimales; el mismo valor en todas las filas (D-PF01-16)';
COMMENT ON COLUMN vw_matriz_riesgo.corte_siniestralidad_retenida IS 'Corte de siniestralidad retenida: 100 × Σ siniestros retenidos / Σ primas retenidas de las filas comparables sobre el umbral en el corte actual, en porcentaje; 6 decimales; el mismo valor en todas las filas (D-PF01-16)';
COMMENT ON COLUMN vw_matriz_riesgo.cuadrante_interanual_directa IS 'Cuadrante por variación interanual e índice directo: 1 crece y sobre el corte, 2 crece y bajo el corte, 3 decrece y sobre el corte, 4 decrece y bajo el corte; nulo bajo el umbral, en rentas y SPP o sin medida (cuadrante por defecto, D-PF01-11 y D-PF01-16)';
COMMENT ON COLUMN vw_matriz_riesgo.cuadrante_interanual_retenida IS 'Cuadrante por variación interanual e índice retenido, con la misma codificación 1 a 4 y los mismos nulos (D-PF01-11 y D-PF01-16)';
COMMENT ON COLUMN vw_matriz_riesgo.cuadrante_tcac_directa IS 'Cuadrante por TCAC e índice directo, con la misma codificación 1 a 4 y los mismos nulos; segundo atributo (D-PF01-11 y D-PF01-16)';
COMMENT ON COLUMN vw_matriz_riesgo.cuadrante_tcac_retenida IS 'Cuadrante por TCAC e índice retenido, con la misma codificación 1 a 4 y los mismos nulos; segundo atributo (D-PF01-11 y D-PF01-16)';
COMMENT ON COLUMN vw_matriz_riesgo.situacion IS 'Por qué la fila entra o no en los cuadrantes: «En la matriz», «Bajo el umbral», «No comparable (rentas y SPP)» o «Sin medida definida»';

PROMPT == 7. vw_participacion_empresa_riesgo ==

-- 7. vw_participacion_empresa_riesgo: apertura por empresa y riesgo (D-PF01-13 y D-PF01-14).
--    Agrupa las columnas de empresa por empresa_id (Mapfre Perú publica dos hasta 2022,
--    hallazgo 1); la participación se calcula sobre la suma de las columnas de empresa del
--    riesgo en el corte, para que sume 100 %.
CREATE OR REPLACE VIEW vw_participacion_empresa_riesgo AS
WITH p AS (SELECT * FROM vw_parametros_analisis),
celdas AS (
    SELECT f.fecha_corte, ce.empresa_id, f.riesgo_id, f.hoja, f.valor, f.columna_id
      FROM fct_riesgo f
      JOIN dim_columna_empresa ce ON ce.columna_id = f.columna_id
     WHERE ce.tipo_columna = 'empresa'
),
por_celda AS (
    SELECT c.fecha_corte, c.empresa_id, c.riesgo_id,
           COUNT(DISTINCT c.columna_id)                        AS n_columnas,
           SUM(CASE WHEN c.hoja = 'P009' THEN c.valor END)     AS primas_netas,
           SUM(CASE WHEN c.hoja = 'P011' THEN c.valor END)     AS primas_retenidas,
           SUM(CASE WHEN c.hoja = 'P012' THEN c.valor END)     AS siniestros_netos,
           SUM(CASE WHEN c.hoja = 'P014' THEN c.valor END)     AS siniestros_retenidos,
           MAX(CASE WHEN c.hoja = 'P015' THEN c.valor END)     AS indice_directa_publicado,
           MAX(CASE WHEN c.hoja = 'P016' THEN c.valor END)     AS indice_retenida_publicado
      FROM celdas c
     GROUP BY c.fecha_corte, c.empresa_id, c.riesgo_id
),
riesgo_total AS (
    SELECT fecha_corte, riesgo_id, SUM(primas_netas) AS primas_netas_riesgo
      FROM por_celda
     GROUP BY fecha_corte, riesgo_id
)
SELECT c.fecha_corte,
       co.meses_acumulados,
       c.empresa_id,
       em.empresa,
       c.riesgo_id,
       r.riesgo,
       r.ramo,
       r.riesgo_comparable,
       r.siniestralidad_comparable,
       c.n_columnas,
       ROUND(c.primas_netas, 2)            AS primas_netas,
       ROUND(c.primas_retenidas, 2)        AS primas_retenidas,
       ROUND(c.siniestros_netos, 2)        AS siniestros_netos,
       ROUND(c.siniestros_retenidos, 2)    AS siniestros_retenidos,
       CASE WHEN t.primas_netas_riesgo > 0
            THEN ROUND(100 * c.primas_netas / t.primas_netas_riesgo, 6) END          AS participacion_riesgo,
       CASE WHEN c.primas_netas > 0
            THEN ROUND(100 * c.siniestros_netos / c.primas_netas, 6) END             AS indice_siniestralidad_directa,
       CASE WHEN c.primas_retenidas > 0
            THEN ROUND(100 * c.siniestros_retenidos / c.primas_retenidas, 6) END     AS indice_siniestralidad_retenida,
       CASE WHEN c.n_columnas = 1 THEN ROUND(c.indice_directa_publicado, 6) END      AS indice_directa_publicado,
       CASE WHEN c.n_columnas = 1 THEN ROUND(c.indice_retenida_publicado, 6) END     AS indice_retenida_publicado,
       CASE WHEN c.primas_netas IS NULL OR c.siniestros_netos IS NULL THEN 'sin_dato'
            WHEN c.primas_netas = 0 THEN 'sin_primas'
            WHEN c.primas_netas < 0 THEN 'primas_negativas'
            WHEN c.siniestros_netos < 0 THEN 'negativo'
            WHEN 100 * c.siniestros_netos / c.primas_netas > 100 THEN 'mayor_100'
            ELSE 'en_rango' END                                                      AS clasificacion_directa,
       CASE WHEN c.primas_retenidas IS NULL OR c.siniestros_retenidos IS NULL THEN 'sin_dato'
            WHEN c.primas_retenidas = 0 THEN 'sin_primas'
            WHEN c.primas_retenidas < 0 THEN 'primas_negativas'
            WHEN c.siniestros_retenidos < 0 THEN 'negativo'
            WHEN 100 * c.siniestros_retenidos / c.primas_retenidas > 100 THEN 'mayor_100'
            ELSE 'en_rango' END                                                      AS clasificacion_retenida,
       p.umbral_primas,
       CASE WHEN c.primas_netas >= p.umbral_primas THEN 'S' ELSE 'N' END             AS sobre_umbral
  FROM por_celda c
  JOIN riesgo_total t ON t.fecha_corte = c.fecha_corte AND t.riesgo_id = c.riesgo_id
  JOIN dim_riesgo r   ON r.riesgo_id = c.riesgo_id
  JOIN dim_empresa em ON em.empresa_id = c.empresa_id
  JOIN dim_corte co   ON co.fecha_corte = c.fecha_corte
 CROSS JOIN p
 WHERE r.tipo = 'riesgo';

COMMENT ON TABLE vw_participacion_empresa_riesgo IS 'Apertura por corte, empresa (columnas agrupadas por empresa_id) y riesgo de tipo riesgo: primas y siniestros (miles de soles, 2 decimales), participación en el riesgo, índices de siniestralidad calculados y publicados (porcentaje, 6 decimales) y clasificación de cada celda (D-PF01-13 y D-PF01-14)';
COMMENT ON COLUMN vw_participacion_empresa_riesgo.n_columnas IS 'Columnas de la fuente agrupadas en la empresa en ese corte (2 en Mapfre Perú hasta 2022; 1 en las demás); los índices publicados solo se muestran si es 1';
COMMENT ON COLUMN vw_participacion_empresa_riesgo.primas_netas IS 'Primas de seguros netas (P009), en miles de soles, acumuladas en el año; 2 decimales';
COMMENT ON COLUMN vw_participacion_empresa_riesgo.primas_retenidas IS 'Primas retenidas (P011), en miles de soles, acumuladas en el año; 2 decimales';
COMMENT ON COLUMN vw_participacion_empresa_riesgo.siniestros_netos IS 'Siniestros de primas de seguros netos (P012), en miles de soles, acumulados en el año; 2 decimales';
COMMENT ON COLUMN vw_participacion_empresa_riesgo.siniestros_retenidos IS 'Siniestros retenidos (P014), en miles de soles, acumulados en el año; 2 decimales';
COMMENT ON COLUMN vw_participacion_empresa_riesgo.participacion_riesgo IS 'Primas netas de la empresa sobre la suma de las columnas de empresa del riesgo en el corte, en porcentaje; 6 decimales; nula si esa suma es 0 o negativa';
COMMENT ON COLUMN vw_participacion_empresa_riesgo.indice_siniestralidad_directa IS 'Índice de siniestralidad directa calculado: 100 × siniestros netos / primas netas, en porcentaje; 6 decimales; nulo si las primas netas son 0 o negativas (D-PF01-14); no se trunca (D-PF01-13)';
COMMENT ON COLUMN vw_participacion_empresa_riesgo.indice_siniestralidad_retenida IS 'Índice de siniestralidad retenida calculado: 100 × siniestros retenidos / primas retenidas, en porcentaje; 6 decimales; nulo si las primas retenidas son 0 o negativas (D-PF01-14); no se trunca (D-PF01-13)';
COMMENT ON COLUMN vw_participacion_empresa_riesgo.indice_directa_publicado IS 'Índice de siniestralidad directa publicado por la SBS (P015), en porcentaje; 6 decimales; solo si la empresa tiene una columna en el corte';
COMMENT ON COLUMN vw_participacion_empresa_riesgo.indice_retenida_publicado IS 'Índice de siniestralidad retenida publicado por la SBS (P016), en porcentaje; 6 decimales; solo si la empresa tiene una columna en el corte';
COMMENT ON COLUMN vw_participacion_empresa_riesgo.clasificacion_directa IS 'Clasificación de la celda con netos y netas (D-PF01-13): sin_dato (falta una cifra), sin_primas (primas 0), primas_negativas, negativo (siniestros negativos), mayor_100 (índice > 100 %) o en_rango';
COMMENT ON COLUMN vw_participacion_empresa_riesgo.clasificacion_retenida IS 'Clasificación de la celda con retenidos y retenidas (D-PF01-13): sin_dato, sin_primas, primas_negativas, negativo, mayor_100 o en_rango';
COMMENT ON COLUMN vw_participacion_empresa_riesgo.umbral_primas IS 'Umbral de materialidad de vw_parametros_analisis, en miles de soles';
COMMENT ON COLUMN vw_participacion_empresa_riesgo.sobre_umbral IS 'S si las primas netas de la celda alcanzan el umbral de materialidad; N si no';

PROMPT == Fin de 04_vistas_analisis.sql ==
