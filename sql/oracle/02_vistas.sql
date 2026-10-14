-- =============================================================================
-- PF-01 · Producción y siniestralidad por riesgo del mercado asegurador
-- peruano, 2019-2026
-- Script:  sql/oracle/02_vistas.sql
-- Paquete: 2.3 Modelo de datos Oracle (issue #6)
-- =============================================================================
--
-- Propósito
--   Crea las vistas vw_ del modelo de datos.
--   Vistas analíticas, sobre las tablas dim_ y fct_:
--   - vw_produccion_riesgo: primas netas, cedidas y retenidas (P009 a P011).
--   - vw_siniestralidad_riesgo: siniestros netos, cedidos y retenidos (P012 a
--     P014) e índices de siniestralidad directa y retenida (P015 y P016).
--   Controles del objetivo O1:
--   - vw_cuadre_balance: Activo = Pasivo + Patrimonio por corte y columna de
--     empresa (hoja P001, moneda TOTAL), sobre dim_ y fct_.
--   - vw_cuadre_totales: suma de las columnas de empresa frente a las
--     columnas Total publicadas (P001 a P003 y P009 a P014), sobre dim_ y
--     fct_ (D-PF01-01 y D-PF01-07).
--   - vw_cuadre_cuadros_sbs: P009 a P016 del Boletín Mensual (S-367) frente a
--     los cuadros S-401, S-402 y S-403, sobre stg_riesgos, porque fct_riesgo
--     solo guarda la serie S-367 (D-PF01-08).
--
-- Orden de ejecución
--   Después de 01_ddl_tablas.sql, que crea las tablas que usan las vistas.
--   Las vistas no dependen entre sí.
--
-- Requisitos
--   - Oracle Database 23ai o posterior: las marcas de cumplimiento son de tipo
--     BOOLEAN. Desarrollo en la base nativa 23.6 (D-PF01-03); validación final
--     en el contenedor gvenzl/oracle-free:23.26.3.
--   - Usuario del proyecto con privilegio CREATE VIEW.
--   - Ejecución con SQLcl o SQL*Plus, por ejemplo:
--       sql pf01@localhost:1521/FREEPDB1 @sql/oracle/02_vistas.sql
--
-- Idempotencia
--   CREATE OR REPLACE VIEW (Oracle no admite IF NOT EXISTS junto con OR
--   REPLACE: ORA-11541) y COMMENT ON, que reemplaza el texto en cada ejecución.
--
-- Convenciones
--   - Grano: una fila por corte, columna de empresa publicada y riesgo (o por
--     corte y columna de empresa en el balance). Las columnas Total publicadas
--     también son filas: su empresa_id es nulo.
--   - Para agregar por empresa a lo largo del tiempo se suma por empresa_id;
--     los índices publicados (P015 y P016) no se suman.
--   - En las vistas de riesgo, dim_riesgo.tipo distingue total, agregado,
--     riesgo y detalle: sumar varios tipos duplica cifras.
--   - Redondeo solo en las vistas (D-PF01-06), con la escala del estándar 6.1:
--     montos en miles de soles a 2 decimales e índices en porcentaje a 6
--     decimales. Las tablas guardan la cifra publicada sin redondear.
--   - Cuadres: tolerancia de 1 mil soles (acta, O1), salvo
--     vw_cuadre_cuadros_sbs, que exige igualdad exacta. La marca de
--     cumplimiento se calcula con la diferencia sin redondear, como en
--     src/pf_01_siniestralidad_sbs/validacion.py.
--   - Las columnas Total se identifican por dim_columna_empresa.tipo_columna
--     (empresa, total_simple o total_ampliado) y el total simple suma solo
--     las empresas con en_total_simple = 'S' (D-PF01-07).
--   - Las hojas se identifican por su código (P001 a P016), que es el dato
--     publicado en fct_riesgo.hoja y dim_cuenta.hoja; los rubros del balance,
--     por dim_cuenta.clave, el rótulo normalizado (mayúsculas, sin tildes) con
--     el mismo criterio que los catálogos del proyecto.
--
-- Decisiones: D-PF01-01 (total simple y total ampliado), D-PF01-03
-- (desarrollo en la base nativa), D-PF01-05 (nombres en español, prefijo
-- vw_), D-PF01-06 (redondeo solo en las vistas), D-PF01-07 (dominios de
-- tipo_columna y en_total_simple) y D-PF01-08 (cuadre con S-401, S-402 y
-- S-403 sobre stg_riesgos).
-- =============================================================================

WHENEVER SQLERROR EXIT FAILURE

PROMPT == 1. vw_produccion_riesgo ==

CREATE OR REPLACE VIEW vw_produccion_riesgo AS
WITH primas AS (
    -- Una fila por corte, columna y riesgo; cada hoja aporta una medida.
    SELECT f.fecha_corte,
           f.columna_id,
           f.riesgo_id,
           MAX(CASE WHEN f.hoja = 'P009' THEN f.valor END) AS primas_netas,
           MAX(CASE WHEN f.hoja = 'P010' THEN f.valor END) AS primas_cedidas,
           MAX(CASE WHEN f.hoja = 'P011' THEN f.valor END) AS primas_retenidas
      FROM fct_riesgo f
     WHERE f.hoja IN ('P009', 'P010', 'P011')
     GROUP BY f.fecha_corte, f.columna_id, f.riesgo_id
)
SELECT p.fecha_corte,
       co.meses_acumulados,
       p.columna_id,
       ce.clave_fuente,
       ce.tipo_columna,
       ce.empresa_id,
       em.empresa,
       ce.entidad,
       ce.estado,
       p.riesgo_id,
       r.riesgo,
       r.nivel                    AS nivel_riesgo,
       r.tipo                     AS tipo_riesgo,
       r.ramo,
       r.riesgo_comparable,
       ROUND(p.primas_netas, 2)     AS primas_netas,
       ROUND(p.primas_cedidas, 2)   AS primas_cedidas,
       ROUND(p.primas_retenidas, 2) AS primas_retenidas
  FROM primas p
  JOIN dim_corte co           ON co.fecha_corte = p.fecha_corte
  JOIN dim_columna_empresa ce ON ce.columna_id = p.columna_id
  LEFT JOIN dim_empresa em    ON em.empresa_id = ce.empresa_id
  JOIN dim_riesgo r           ON r.riesgo_id = p.riesgo_id;

COMMENT ON TABLE vw_produccion_riesgo IS 'Primas netas, cedidas y retenidas (hojas P009, P010 y P011 del Boletín Mensual S-367) por corte, columna de empresa y riesgo, en miles de soles redondeados a 2 decimales';
COMMENT ON COLUMN vw_produccion_riesgo.primas_netas IS 'Primas de seguros netas (P009), en miles de soles, acumuladas en el año; 2 decimales';
COMMENT ON COLUMN vw_produccion_riesgo.primas_cedidas IS 'Primas cedidas netas (P010), en miles de soles, acumuladas en el año; 2 decimales';
COMMENT ON COLUMN vw_produccion_riesgo.primas_retenidas IS 'Primas retenidas (P011), en miles de soles, acumuladas en el año; 2 decimales';
COMMENT ON COLUMN vw_produccion_riesgo.empresa_id IS 'Empresa para el análisis en el tiempo; nulo en las columnas Total publicadas';
COMMENT ON COLUMN vw_produccion_riesgo.tipo_riesgo IS 'total, agregado, riesgo o detalle (catálogo de riesgos); sumar varios tipos duplica cifras';

PROMPT == 2. vw_siniestralidad_riesgo ==

CREATE OR REPLACE VIEW vw_siniestralidad_riesgo AS
WITH siniestros AS (
    -- Una fila por corte, columna y riesgo; cada hoja aporta una medida.
    SELECT f.fecha_corte,
           f.columna_id,
           f.riesgo_id,
           MAX(CASE WHEN f.hoja = 'P012' THEN f.valor END) AS siniestros_netos,
           MAX(CASE WHEN f.hoja = 'P013' THEN f.valor END) AS siniestros_cedidos,
           MAX(CASE WHEN f.hoja = 'P014' THEN f.valor END) AS siniestros_retenidos,
           MAX(CASE WHEN f.hoja = 'P015' THEN f.valor END) AS indice_siniestralidad_directa,
           MAX(CASE WHEN f.hoja = 'P016' THEN f.valor END) AS indice_siniestralidad_retenida
      FROM fct_riesgo f
     WHERE f.hoja IN ('P012', 'P013', 'P014', 'P015', 'P016')
     GROUP BY f.fecha_corte, f.columna_id, f.riesgo_id
)
SELECT s.fecha_corte,
       co.meses_acumulados,
       s.columna_id,
       ce.clave_fuente,
       ce.tipo_columna,
       ce.empresa_id,
       em.empresa,
       ce.entidad,
       ce.estado,
       s.riesgo_id,
       r.riesgo,
       r.nivel                                  AS nivel_riesgo,
       r.tipo                                   AS tipo_riesgo,
       r.ramo,
       r.riesgo_comparable,
       ROUND(s.siniestros_netos, 2)               AS siniestros_netos,
       ROUND(s.siniestros_cedidos, 2)             AS siniestros_cedidos,
       ROUND(s.siniestros_retenidos, 2)           AS siniestros_retenidos,
       ROUND(s.indice_siniestralidad_directa, 6)  AS indice_siniestralidad_directa,
       ROUND(s.indice_siniestralidad_retenida, 6) AS indice_siniestralidad_retenida
  FROM siniestros s
  JOIN dim_corte co           ON co.fecha_corte = s.fecha_corte
  JOIN dim_columna_empresa ce ON ce.columna_id = s.columna_id
  LEFT JOIN dim_empresa em    ON em.empresa_id = ce.empresa_id
  JOIN dim_riesgo r           ON r.riesgo_id = s.riesgo_id;

COMMENT ON TABLE vw_siniestralidad_riesgo IS 'Siniestros netos, cedidos y retenidos (P012 a P014, miles de soles, 2 decimales) e índices de siniestralidad directa y retenida publicados (P015 y P016, porcentaje, 6 decimales) por corte, columna de empresa y riesgo';
COMMENT ON COLUMN vw_siniestralidad_riesgo.siniestros_netos IS 'Siniestros de primas de seguros netos (P012), en miles de soles, acumulados en el año; 2 decimales';
COMMENT ON COLUMN vw_siniestralidad_riesgo.siniestros_cedidos IS 'Siniestros de primas cedidas netos (P013), en miles de soles, acumulados en el año; 2 decimales';
COMMENT ON COLUMN vw_siniestralidad_riesgo.siniestros_retenidos IS 'Siniestros retenidos (P014), en miles de soles, acumulados en el año; 2 decimales';
COMMENT ON COLUMN vw_siniestralidad_riesgo.indice_siniestralidad_directa IS 'Índice de siniestralidad directa publicado por la SBS (P015), en porcentaje; 6 decimales; no se suma entre columnas';
COMMENT ON COLUMN vw_siniestralidad_riesgo.indice_siniestralidad_retenida IS 'Índice de siniestralidad retenida publicado por la SBS (P016), en porcentaje; 6 decimales; no se suma entre columnas';
COMMENT ON COLUMN vw_siniestralidad_riesgo.empresa_id IS 'Empresa para el análisis en el tiempo; nulo en las columnas Total publicadas';
COMMENT ON COLUMN vw_siniestralidad_riesgo.tipo_riesgo IS 'total, agregado, riesgo o detalle (catálogo de riesgos); sumar varios tipos duplica cifras';

PROMPT == 3. vw_cuadre_balance ==

CREATE OR REPLACE VIEW vw_cuadre_balance AS
WITH rubros AS (
    -- Los cuatro rubros del estado de situación financiera (P001) en moneda
    -- TOTAL: el patrimonio se presenta en moneda nacional, así que la
    -- igualdad no se exige por moneda.
    SELECT f.fecha_corte,
           f.columna_id,
           SUM(CASE WHEN cu.clave = 'TOTAL ACTIVO' THEN f.valor END)              AS total_activo,
           SUM(CASE WHEN cu.clave = 'TOTAL PASIVO' THEN f.valor END)              AS total_pasivo,
           SUM(CASE WHEN cu.clave = 'PATRIMONIO' THEN f.valor END)                AS patrimonio,
           SUM(CASE WHEN cu.clave = 'TOTAL PASIVO Y PATRIMONIO' THEN f.valor END) AS total_pasivo_y_patrimonio
      FROM fct_estado_financiero f
      JOIN dim_cuenta cu ON cu.cuenta_id = f.cuenta_id
     WHERE cu.hoja = 'P001'
       AND cu.clave IN ('TOTAL ACTIVO', 'TOTAL PASIVO', 'PATRIMONIO', 'TOTAL PASIVO Y PATRIMONIO')
       AND f.moneda = 'TOTAL'
     GROUP BY f.fecha_corte, f.columna_id
),
diferencias AS (
    SELECT r.fecha_corte,
           r.columna_id,
           r.total_activo,
           r.total_pasivo,
           r.patrimonio,
           r.total_pasivo_y_patrimonio,
           r.total_activo - (r.total_pasivo + r.patrimonio)              AS diferencia_activo,
           (r.total_pasivo + r.patrimonio) - r.total_pasivo_y_patrimonio AS diferencia_total_publicado
      FROM rubros r
)
SELECT d.fecha_corte,
       d.columna_id,
       ce.clave_fuente,
       ce.tipo_columna,
       ce.empresa_id,
       em.empresa,
       ROUND(d.total_activo, 2)                    AS total_activo,
       ROUND(d.total_pasivo, 2)                    AS total_pasivo,
       ROUND(d.patrimonio, 2)                      AS patrimonio,
       ROUND(d.total_pasivo + d.patrimonio, 2)     AS pasivo_mas_patrimonio,
       ROUND(d.total_pasivo_y_patrimonio, 2)       AS total_pasivo_y_patrimonio,
       ROUND(d.diferencia_activo, 2)               AS diferencia_activo,
       ROUND(d.diferencia_total_publicado, 2)      AS diferencia_total_publicado,
       -- Tolerancia de 1 mil soles (O1); un rubro faltante no cumple.
       CASE
           WHEN ABS(d.diferencia_activo) <= 1
            AND ABS(d.diferencia_total_publicado) <= 1 THEN TRUE
           ELSE FALSE
       END                                         AS cumple
  FROM diferencias d
  JOIN dim_columna_empresa ce ON ce.columna_id = d.columna_id
  LEFT JOIN dim_empresa em    ON em.empresa_id = ce.empresa_id;

COMMENT ON TABLE vw_cuadre_balance IS 'Control del objetivo O1: Activo = Pasivo + Patrimonio por corte y columna de empresa (P001, moneda TOTAL), con tolerancia de 1 mil soles; montos en miles de soles a 2 decimales';
COMMENT ON COLUMN vw_cuadre_balance.pasivo_mas_patrimonio IS 'Total pasivo + patrimonio, calculado';
COMMENT ON COLUMN vw_cuadre_balance.total_pasivo_y_patrimonio IS 'Total pasivo y patrimonio publicado en P001';
COMMENT ON COLUMN vw_cuadre_balance.diferencia_activo IS 'Total activo - (total pasivo + patrimonio)';
COMMENT ON COLUMN vw_cuadre_balance.diferencia_total_publicado IS '(Total pasivo + patrimonio) - total pasivo y patrimonio publicado';
COMMENT ON COLUMN vw_cuadre_balance.cumple IS 'Verdadero si las dos diferencias, sin redondear, son de 1 mil soles o menos y no falta ningún rubro';

PROMPT == 4. vw_cuadre_totales ==

CREATE OR REPLACE VIEW vw_cuadre_totales AS
WITH celdas AS (
    -- Celdas de las hojas con columna Total. En el modelo, la fila se
    -- identifica por su concepto: cuenta (P001 y P002), indicador (P003) o
    -- riesgo (P009 a P014). La moneda solo existe en P001 y P002.
    SELECT f.fecha_corte, cu.hoja, f.cuenta_id AS concepto_id, cu.cuenta AS concepto,
           f.moneda, f.columna_id, f.valor
      FROM fct_estado_financiero f
      JOIN dim_cuenta cu ON cu.cuenta_id = f.cuenta_id
     WHERE cu.hoja IN ('P001', 'P002')
    UNION ALL
    SELECT f.fecha_corte, i.hoja, f.indicador_id, i.indicador,
           CAST(NULL AS VARCHAR2(5)), f.columna_id, f.valor
      FROM fct_indicador f
      JOIN dim_indicador i ON i.indicador_id = f.indicador_id
     WHERE i.hoja = 'P003'
    UNION ALL
    SELECT f.fecha_corte, f.hoja, f.riesgo_id, r.riesgo,
           CAST(NULL AS VARCHAR2(5)), f.columna_id, f.valor
      FROM fct_riesgo f
      JOIN dim_riesgo r ON r.riesgo_id = f.riesgo_id
     WHERE f.hoja IN ('P009', 'P010', 'P011', 'P012', 'P013', 'P014')
),
agregados AS (
    -- Una fila por corte, hoja, concepto y moneda: sumas de las columnas de
    -- empresa y totales publicados.
    SELECT c.fecha_corte, c.hoja, c.concepto_id, c.concepto, c.moneda,
           SUM(CASE WHEN ce.tipo_columna = 'empresa' AND ce.en_total_simple = 'S' THEN c.valor END) AS suma_simple,
           SUM(CASE WHEN ce.tipo_columna = 'empresa' THEN c.valor END)                              AS suma_ampliada,
           SUM(CASE WHEN ce.tipo_columna = 'total_simple' THEN c.valor END)                         AS total_simple,
           SUM(CASE WHEN ce.tipo_columna = 'total_ampliado' THEN c.valor END)                       AS total_ampliado
      FROM celdas c
      JOIN dim_columna_empresa ce ON ce.columna_id = c.columna_id
     GROUP BY c.fecha_corte, c.hoja, c.concepto_id, c.concepto, c.moneda
),
controles AS (
    -- Total simple: empresas con en_total_simple = 'S' frente a «Total».
    SELECT a.fecha_corte, a.hoja, a.concepto_id, a.concepto, a.moneda,
           'total_simple'        AS tipo_total,
           NVL(a.suma_simple, 0) AS suma_empresas,
           a.total_simple        AS total_publicado
      FROM agregados a
     WHERE a.total_simple IS NOT NULL
    UNION ALL
    -- Total ampliado: todas las columnas de empresa frente a «Total + …».
    SELECT a.fecha_corte, a.hoja, a.concepto_id, a.concepto, a.moneda,
           'total_ampliado',
           NVL(a.suma_ampliada, 0),
           a.total_ampliado
      FROM agregados a
     WHERE a.total_ampliado IS NOT NULL
)
SELECT k.fecha_corte,
       k.hoja,
       k.concepto_id,
       k.concepto,
       k.moneda,
       k.tipo_total,
       ROUND(k.suma_empresas, 2)                     AS suma_empresas,
       ROUND(k.total_publicado, 2)                   AS total_publicado,
       ROUND(k.suma_empresas - k.total_publicado, 2) AS diferencia,
       -- Tolerancia de 1 mil soles (O1), sobre la diferencia sin redondear.
       CASE
           WHEN ABS(k.suma_empresas - k.total_publicado) <= 1 THEN TRUE
           ELSE FALSE
       END                                           AS cumple
  FROM controles k;

COMMENT ON TABLE vw_cuadre_totales IS 'Control del objetivo O1: suma de las columnas de empresa frente a la columna Total publicada, por corte, hoja, concepto (fila) y moneda, en P001 a P003 y P009 a P014; tolerancia de 1 mil soles (D-PF01-01 y D-PF01-07)';
COMMENT ON COLUMN vw_cuadre_totales.concepto_id IS 'Fila de la hoja en el modelo: cuenta_id (P001 y P002), indicador_id (P003) o riesgo_id (P009 a P014)';
COMMENT ON COLUMN vw_cuadre_totales.moneda IS 'MN, ME o TOTAL en P001 y P002; nula en las demás hojas';
COMMENT ON COLUMN vw_cuadre_totales.tipo_total IS 'total_simple: empresas con en_total_simple = S frente a «Total»; total_ampliado: todas las columnas de empresa frente a «Total + …»';
COMMENT ON COLUMN vw_cuadre_totales.suma_empresas IS 'Suma de las columnas de empresa que integran el total, en miles de soles; 2 decimales';
COMMENT ON COLUMN vw_cuadre_totales.diferencia IS 'suma_empresas - total_publicado, en miles de soles; 2 decimales';
COMMENT ON COLUMN vw_cuadre_totales.cumple IS 'Verdadero si la diferencia, sin redondear, es de 1 mil soles o menos';

PROMPT == 5. vw_cuadre_cuadros_sbs ==

CREATE OR REPLACE VIEW vw_cuadre_cuadros_sbs AS
-- Réplica de consistencia_cuadros (validacion.py) sobre stg_riesgos
-- (D-PF01-08): cada celda de los cuadros S-401, S-402 y S-403 se cruza con la
-- celda del Boletín Mensual (S-367) del mismo corte, hoja, fila y columna.
-- Una celda del cuadro sin par en el Boletín no cumple.
SELECT c.corte   AS fecha_corte,
       c.hoja,
       c.serie   AS serie_cuadro,
       c.fila,
       c.columna,
       c.concepto,
       c.empresa,
       c.unidad,
       CASE WHEN c.hoja IN ('P015', 'P016') THEN ROUND(b.valor, 6) ELSE ROUND(b.valor, 2) END AS valor_boletin,
       CASE WHEN c.hoja IN ('P015', 'P016') THEN ROUND(c.valor, 6) ELSE ROUND(c.valor, 2) END AS valor_cuadro,
       b.valor - c.valor AS diferencia,
       CASE WHEN b.valor = c.valor THEN TRUE ELSE FALSE END AS cumple
  FROM stg_riesgos c
  LEFT JOIN stg_riesgos b
    ON  b.serie   = 'S-367'
    AND b.corte   = c.corte
    AND b.hoja    = c.hoja
    AND b.fila    = c.fila
    AND b.columna = c.columna
 WHERE c.serie IN ('S-401', 'S-402', 'S-403');

COMMENT ON TABLE vw_cuadre_cuadros_sbs IS 'Control del objetivo O1: hojas P009 a P016 del Boletín Mensual (S-367) frente a los cuadros S-401, S-402 y S-403, celda por celda (corte, hoja, fila y columna), sobre stg_riesgos; exige igualdad exacta (D-PF01-08)';
COMMENT ON COLUMN vw_cuadre_cuadros_sbs.serie_cuadro IS 'Cuadro publicado por separado: S-401 (primas), S-402 (siniestros) o S-403 (índices de siniestralidad)';
COMMENT ON COLUMN vw_cuadre_cuadros_sbs.valor_boletin IS 'Cifra del Boletín Mensual (S-367); miles de soles a 2 decimales o porcentaje a 6 decimales (P015 y P016); nula si la celda no está en el Boletín';
COMMENT ON COLUMN vw_cuadre_cuadros_sbs.valor_cuadro IS 'Cifra del cuadro S-401, S-402 o S-403; miles de soles a 2 decimales o porcentaje a 6 decimales (P015 y P016)';
COMMENT ON COLUMN vw_cuadre_cuadros_sbs.diferencia IS 'valor del Boletín - valor del cuadro, sin redondear, para que una diferencia mínima no quede oculta';
COMMENT ON COLUMN vw_cuadre_cuadros_sbs.cumple IS 'Verdadero si las dos cifras son iguales; falso si difieren o si la celda no está en el Boletín';

PROMPT == Fin de 02_vistas.sql ==
