-- =============================================================================
-- PF-01 · Producción y siniestralidad por riesgo del mercado asegurador
-- peruano, 2019-2026
-- Script:  sql/oracle/03_carga_modelo.sql
-- Paquete: 2.3 Modelo de datos Oracle (issue #6)
-- =============================================================================
--
-- Propósito
--   Llena desde las tablas stg_ las dimensiones dim_cuadro, dim_cuenta,
--   dim_indicador y las columnas Total de dim_columna_empresa, y las tres
--   tablas de hechos (fct_estado_financiero, fct_indicador y fct_riesgo).
--
-- Orden de ejecución
--   Después de 01_ddl_tablas.sql, 02_vistas.sql, la carga de las tablas stg_ y
--   la de las dimensiones de catálogo (dim_empresa, dim_corte, dim_riesgo y
--   las columnas de empresa de dim_columna_empresa), que hace
--   src/pf_01_siniestralidad_sbs/carga.py. scripts/cargar_oracle.py ejecuta
--   todo en ese orden.
--
-- Requisitos
--   - Oracle Database 23ai o posterior.
--   - Archivo en UTF-8: la regla de normalización traduce letras con tilde.
--   - Ejecución con scripts/ejecutar_sql.py, SQLcl o SQL*Plus.
--
-- Idempotencia
--   Reemplazo completo en una sola transacción: borra los hechos y las
--   dimensiones que llena este script, las vuelve a insertar con
--   INSERT ... SELECT y confirma al final. Con los mismos datos, la segunda
--   ejecución deja las mismas filas y los mismos identificadores. Antes de
--   confirmar, comprueba que cada tabla de hechos tenga tantas filas como su
--   tabla stg_ en la serie S-367; si no, el error deshace todo. Después del
--   COMMIT reúne las estadísticas del optimizador de dim_ y fct_ (las de stg_
--   las reúne carga.py al cargarlas).
--
-- Rendimiento
--   Cada rótulo distinto se normaliza una sola vez y las tablas de
--   correspondencia (rótulo -> columna, fila -> cuenta o indicador) se
--   materializan; las celdas se cruzan con ellas por igualdad.
--
-- Reglas de carga
--   - Clave normalizada: mayúsculas, sin tildes y sin espacios repetidos, el
--     mismo criterio que validacion.normalizar() y los catálogos:
--       TRIM(REGEXP_REPLACE(UPPER(TRANSLATE(texto, con tilde, sin tilde)),
--            '[[:space:]]+', ' '))
--   - dim_cuenta.clave: el rótulo normalizado. Si el rótulo se repite en la
--     misma hoja y corte (en P001, en las partes corriente y no corriente), la
--     2.ª aparición lleva « (2)» (decisión del director, 2026-10-14).
--   - Una cuenta por fila de P001 y P002. Si los bloques de empresas publican
--     rótulos distintos en la misma fila (P001 de 2021 a 2023: el primer
--     bloque ya usa los rótulos del plan nuevo en 2 filas), vale el del bloque
--     de la columna Total, que es el que suma esa fila.
--   - dim_cuenta.nivel: orden de la sangría en la hoja (0 = sin sangría), en
--     el corte más reciente en que aparece la cuenta.
--   - dim_indicador.seccion: en P004, la sección publicada; en P003, el tramo
--     de la hoja, separado por el mayor salto de filas: CIFRAS AL CORTE y
--     SALDOS PROMEDIO ULTIMOS 12 MESES (decisión del director, 2026-10-14).
--   - dim_columna_empresa: las columnas Total llevan tipo_columna total_simple
--     o total_ampliado, en_total_simple = 'N' y empresa_id nulo (D-PF01-07).
--   - dim_cuadro: grupo es la tabla de data/interim de la hoja y medida, lo que
--     publica la hoja; título y unidad del corte más reciente del Boletín.
--   - Rótulo de cuentas e indicadores: el del corte más reciente.
--   - Hechos solo de la serie S-367 (D-PF01-08).
--
-- Decisiones: D-PF01-03 (desarrollo en la base nativa), D-PF01-05 (nombres en
-- español), D-PF01-06 (valor sin redondear), D-PF01-07 (tipo_columna y
-- en_total_simple) y D-PF01-08 (fct_riesgo solo con S-367).
-- =============================================================================

WHENEVER SQLERROR EXIT FAILURE ROLLBACK

PROMPT == 1. Borrado de hechos y de dimensiones que salen de stg_ ==

DELETE FROM fct_estado_financiero;
DELETE FROM fct_indicador;
DELETE FROM fct_riesgo;
DELETE FROM dim_cuenta;
DELETE FROM dim_indicador;
DELETE FROM dim_cuadro;
DELETE FROM dim_columna_empresa WHERE tipo_columna <> 'empresa';

PROMPT == 2. dim_cuadro ==

INSERT INTO dim_cuadro (hoja, cuadro, unidad, grupo, medida)
WITH hojas AS (
    SELECT hoja, corte, cuadro, unidad, 'estados_financieros' AS grupo
      FROM stg_estados_financieros
     WHERE serie = 'S-367'
    UNION ALL
    SELECT hoja, corte, cuadro, unidad, 'indicadores'
      FROM stg_indicadores
     WHERE serie = 'S-367'
    UNION ALL
    SELECT hoja, corte, cuadro, unidad, 'riesgos'
      FROM stg_riesgos
     WHERE serie = 'S-367'
)
SELECT h.hoja,
       MAX(h.cuadro) KEEP (DENSE_RANK LAST ORDER BY h.corte),
       MAX(h.unidad) KEEP (DENSE_RANK LAST ORDER BY h.corte),
       MAX(h.grupo),
       -- Una hoja nueva queda sin medida y falla por NOT NULL: hay que agregarla aquí.
       CASE h.hoja
           WHEN 'P001' THEN 'estado_situacion_financiera'
           WHEN 'P002' THEN 'estado_resultados'
           WHEN 'P003' THEN 'cifras_indicadores'
           WHEN 'P004' THEN 'indicadores'
           WHEN 'P009' THEN 'primas_netas'
           WHEN 'P010' THEN 'primas_cedidas'
           WHEN 'P011' THEN 'primas_retenidas'
           WHEN 'P012' THEN 'siniestros_netos'
           WHEN 'P013' THEN 'siniestros_cedidos'
           WHEN 'P014' THEN 'siniestros_retenidos'
           WHEN 'P015' THEN 'indice_siniestralidad_directa'
           WHEN 'P016' THEN 'indice_siniestralidad_retenida'
       END
  FROM hojas h
 GROUP BY h.hoja;

PROMPT == 3. dim_columna_empresa: columnas Total ==

INSERT INTO dim_columna_empresa (
    columna_id, clave_fuente, corte_desde, corte_hasta, tipo_columna, entidad,
    estado, en_total_simple, evento, fuente_evento, empresa_id
)
WITH rotulos AS (
    -- Rótulos de columna distintos por corte.
    SELECT /*+ MATERIALIZE */ corte, empresa
      FROM (SELECT corte, empresa FROM stg_estados_financieros
            UNION
            SELECT corte, empresa FROM stg_indicadores
            UNION
            SELECT corte, empresa FROM stg_riesgos)
),
etiquetas AS (
    -- Cada rótulo distinto se normaliza una sola vez.
    SELECT /*+ MATERIALIZE */ e.empresa,
           TRIM(REGEXP_REPLACE(UPPER(TRANSLATE(e.empresa,
               'ÁÉÍÓÚÀÈÌÒÙÄËÏÖÜÂÊÎÔÛÑÇáéíóúàèìòùäëïöüâêîôûñç',
               'AEIOUAEIOUAEIOUAEIOUNCaeiouaeiouaeiouaeiounc')), '[[:space:]]+', ' ')) AS clave_fuente
      FROM (SELECT DISTINCT empresa FROM rotulos) e
),
normalizados AS (
    SELECT r.corte, r.empresa, e.clave_fuente
      FROM rotulos r
      JOIN etiquetas e ON e.empresa = r.empresa
),
totales AS (
    -- Mismos rótulos que validacion.tipo_total(): «Total» y «Total empresas de
    -- seguros» son el total simple; «Total + …», el total ampliado.
    SELECT n.clave_fuente,
           CASE
               WHEN n.clave_fuente IN ('TOTAL', 'TOTAL EMPRESAS DE SEGUROS') THEN 'total_simple'
               ELSE 'total_ampliado'
           END                                                 AS tipo_columna,
           MIN(n.corte)                                        AS corte_desde,
           MAX(n.corte)                                        AS corte_hasta,
           MAX(n.empresa) KEEP (DENSE_RANK LAST ORDER BY n.corte) AS entidad
      FROM normalizados n
     WHERE n.clave_fuente IN ('TOTAL', 'TOTAL EMPRESAS DE SEGUROS')
        OR n.clave_fuente LIKE 'TOTAL +%'
     GROUP BY n.clave_fuente
)
SELECT (SELECT NVL(MAX(columna_id), 0) FROM dim_columna_empresa)
           + ROW_NUMBER() OVER (ORDER BY t.tipo_columna DESC, t.clave_fuente),
       t.clave_fuente,
       t.corte_desde,
       t.corte_hasta,
       t.tipo_columna,
       t.entidad,
       NULL,
       'N',
       NULL,
       NULL,
       NULL
  FROM totales t;

PROMPT == 4. dim_cuenta ==

INSERT INTO dim_cuenta (cuenta_id, clave, cuenta, nivel, hoja)
WITH filas AS (
    -- Una cuenta por corte, hoja y fila: todas las empresas comparten las filas. Si los
    -- bloques de empresas publican rótulos distintos en una fila, vale el del bloque de la
    -- columna Total (o el más frecuente).
    SELECT corte,
           hoja,
           fila,
           COALESCE(MAX(CASE WHEN es_total THEN concepto END), STATS_MODE(concepto)) AS concepto,
           MIN(sangria) AS sangria
      FROM stg_estados_financieros
     WHERE serie = 'S-367'
     GROUP BY corte, hoja, fila
),
normalizadas AS (
    SELECT f.corte,
           f.hoja,
           f.fila,
           f.concepto,
           TRIM(REGEXP_REPLACE(UPPER(TRANSLATE(f.concepto,
               'ÁÉÍÓÚÀÈÌÒÙÄËÏÖÜÂÊÎÔÛÑÇáéíóúàèìòùäëïöüâêîôûñç',
               'AEIOUAEIOUAEIOUAEIOUNCaeiouaeiouaeiouaeiounc')), '[[:space:]]+', ' ')) AS clave_base,
           DENSE_RANK() OVER (PARTITION BY f.corte, f.hoja ORDER BY f.sangria) - 1 AS nivel
      FROM filas f
),
apariciones AS (
    SELECT n.corte,
           n.hoja,
           n.fila,
           n.concepto,
           n.nivel,
           n.clave_base,
           DENSE_RANK() OVER (PARTITION BY n.corte, n.hoja, n.clave_base ORDER BY n.fila) AS aparicion
      FROM normalizadas n
),
claves AS (
    SELECT a.corte,
           a.hoja,
           a.fila,
           a.concepto,
           a.nivel,
           a.clave_base || CASE WHEN a.aparicion > 1 THEN ' (' || a.aparicion || ')' END AS clave
      FROM apariciones a
),
cuentas AS (
    SELECT k.hoja,
           k.clave,
           MAX(k.concepto) KEEP (DENSE_RANK LAST ORDER BY k.corte) AS cuenta,
           MAX(k.nivel)    KEEP (DENSE_RANK LAST ORDER BY k.corte) AS nivel,
           MAX(k.fila)     KEEP (DENSE_RANK LAST ORDER BY k.corte) AS fila
      FROM claves k
     GROUP BY k.hoja, k.clave
)
SELECT ROW_NUMBER() OVER (ORDER BY c.hoja, c.fila, c.clave),
       c.clave,
       c.cuenta,
       c.nivel,
       c.hoja
  FROM cuentas c;

PROMPT == 5. dim_indicador ==

INSERT INTO dim_indicador (indicador_id, seccion, clave, indicador, hoja)
WITH filas AS (
    SELECT DISTINCT corte, hoja, fila, seccion, concepto
      FROM stg_indicadores
     WHERE serie = 'S-367'
),
saltos AS (
    SELECT corte, fila, fila - LAG(fila) OVER (PARTITION BY corte ORDER BY fila) AS salto
      FROM filas
     WHERE hoja = 'P003'
),
inicio_tramo AS (
    -- El 2.º tramo de P003 empieza después del mayor salto de filas (notas al
    -- pie y encabezado repetido entre los dos tramos).
    SELECT corte, MAX(fila) KEEP (DENSE_RANK FIRST ORDER BY salto DESC NULLS LAST) AS fila_inicio
      FROM saltos
     GROUP BY corte
),
claves AS (
    SELECT f.corte,
           f.hoja,
           f.fila,
           f.concepto,
           CASE
               WHEN f.hoja <> 'P003' THEN f.seccion
               WHEN f.fila >= t.fila_inicio THEN 'SALDOS PROMEDIO ULTIMOS 12 MESES'
               ELSE 'CIFRAS AL CORTE'
           END AS seccion,
           TRIM(REGEXP_REPLACE(UPPER(TRANSLATE(f.concepto,
               'ÁÉÍÓÚÀÈÌÒÙÄËÏÖÜÂÊÎÔÛÑÇáéíóúàèìòùäëïöüâêîôûñç',
               'AEIOUAEIOUAEIOUAEIOUNCaeiouaeiouaeiouaeiounc')), '[[:space:]]+', ' ')) AS clave
      FROM filas f
      LEFT JOIN inicio_tramo t ON t.corte = f.corte
),
indicadores AS (
    SELECT k.hoja,
           k.seccion,
           k.clave,
           MAX(k.concepto) KEEP (DENSE_RANK LAST ORDER BY k.corte) AS indicador,
           MAX(k.fila)     KEEP (DENSE_RANK LAST ORDER BY k.corte) AS fila
      FROM claves k
     GROUP BY k.hoja, k.seccion, k.clave
)
SELECT ROW_NUMBER() OVER (ORDER BY i.hoja, i.fila, i.seccion, i.clave),
       i.seccion,
       i.clave,
       i.indicador,
       i.hoja
  FROM indicadores i;

PROMPT == 6. fct_estado_financiero ==

INSERT INTO fct_estado_financiero (moneda, valor, columna_id, cuenta_id, fecha_corte)
WITH filas AS (
    -- Misma regla que dim_cuenta: un rótulo por fila, el del bloque de la columna Total.
    SELECT corte,
           hoja,
           fila,
           COALESCE(MAX(CASE WHEN es_total THEN concepto END), STATS_MODE(concepto)) AS concepto
      FROM stg_estados_financieros
     WHERE serie = 'S-367'
     GROUP BY corte, hoja, fila
),
normalizadas AS (
    SELECT f.corte,
           f.hoja,
           f.fila,
           TRIM(REGEXP_REPLACE(UPPER(TRANSLATE(f.concepto,
               'ÁÉÍÓÚÀÈÌÒÙÄËÏÖÜÂÊÎÔÛÑÇáéíóúàèìòùäëïöüâêîôûñç',
               'AEIOUAEIOUAEIOUAEIOUNCaeiouaeiouaeiouaeiounc')), '[[:space:]]+', ' ')) AS clave_base
      FROM filas f
),
apariciones AS (
    SELECT n.corte,
           n.hoja,
           n.fila,
           n.clave_base,
           DENSE_RANK() OVER (PARTITION BY n.corte, n.hoja, n.clave_base ORDER BY n.fila) AS aparicion
      FROM normalizadas n
),
cuentas AS (
    -- Cuenta de cada fila; misma regla que dim_cuenta: « (2)» en la 2.ª aparición del
    -- rótulo. Se calcula una vez (MATERIALIZE) y las celdas la cruzan por igualdad.
    SELECT /*+ MATERIALIZE */ a.corte, a.hoja, a.fila, cu.cuenta_id
      FROM apariciones a
      JOIN dim_cuenta cu
        ON cu.hoja = a.hoja
       AND cu.clave = a.clave_base || CASE WHEN a.aparicion > 1 THEN ' (' || a.aparicion || ')' END
),
columnas AS (
    -- Columna de empresa de cada rótulo publicado y corte: se normaliza una vez por rótulo.
    SELECT /*+ MATERIALIZE */ r.corte, r.empresa, ce.columna_id
      FROM (SELECT DISTINCT corte, empresa
              FROM stg_estados_financieros
             WHERE serie = 'S-367') r
      JOIN dim_columna_empresa ce
        ON ce.clave_fuente = TRIM(REGEXP_REPLACE(UPPER(TRANSLATE(r.empresa,
               'ÁÉÍÓÚÀÈÌÒÙÄËÏÖÜÂÊÎÔÛÑÇáéíóúàèìòùäëïöüâêîôûñç',
               'AEIOUAEIOUAEIOUAEIOUNCaeiouaeiouaeiouaeiounc')), '[[:space:]]+', ' '))
       AND r.corte BETWEEN ce.corte_desde AND ce.corte_hasta
)
SELECT s.moneda,
       s.valor,
       co.columna_id,
       cu.cuenta_id,
       s.corte
  FROM stg_estados_financieros s
  JOIN cuentas cu  ON cu.corte = s.corte AND cu.hoja = s.hoja AND cu.fila = s.fila
  JOIN columnas co ON co.corte = s.corte AND co.empresa = s.empresa
 WHERE s.serie = 'S-367';

PROMPT == 7. fct_indicador ==

INSERT INTO fct_indicador (valor, fecha_corte, columna_id, indicador_id)
WITH filas AS (
    SELECT DISTINCT corte, hoja, fila, seccion, concepto
      FROM stg_indicadores
     WHERE serie = 'S-367'
),
saltos AS (
    SELECT corte, fila, fila - LAG(fila) OVER (PARTITION BY corte ORDER BY fila) AS salto
      FROM filas
     WHERE hoja = 'P003'
),
inicio_tramo AS (
    -- Misma regla que dim_indicador.
    SELECT corte, MAX(fila) KEEP (DENSE_RANK FIRST ORDER BY salto DESC NULLS LAST) AS fila_inicio
      FROM saltos
     GROUP BY corte
),
claves AS (
    SELECT f.corte,
           f.hoja,
           f.fila,
           CASE
               WHEN f.hoja <> 'P003' THEN f.seccion
               WHEN f.fila >= t.fila_inicio THEN 'SALDOS PROMEDIO ULTIMOS 12 MESES'
               ELSE 'CIFRAS AL CORTE'
           END AS seccion,
           TRIM(REGEXP_REPLACE(UPPER(TRANSLATE(f.concepto,
               'ÁÉÍÓÚÀÈÌÒÙÄËÏÖÜÂÊÎÔÛÑÇáéíóúàèìòùäëïöüâêîôûñç',
               'AEIOUAEIOUAEIOUAEIOUNCaeiouaeiouaeiouaeiounc')), '[[:space:]]+', ' ')) AS clave
      FROM filas f
      LEFT JOIN inicio_tramo t ON t.corte = f.corte
),
indicadores AS (
    -- Indicador de cada fila; se calcula una vez (MATERIALIZE) y las celdas lo cruzan por
    -- igualdad.
    SELECT /*+ MATERIALIZE */ k.corte, k.hoja, k.fila, i.indicador_id
      FROM claves k
      JOIN dim_indicador i ON i.hoja = k.hoja AND i.seccion = k.seccion AND i.clave = k.clave
),
columnas AS (
    -- Columna de empresa de cada rótulo publicado y corte: se normaliza una vez por rótulo.
    SELECT /*+ MATERIALIZE */ r.corte, r.empresa, ce.columna_id
      FROM (SELECT DISTINCT corte, empresa
              FROM stg_indicadores
             WHERE serie = 'S-367') r
      JOIN dim_columna_empresa ce
        ON ce.clave_fuente = TRIM(REGEXP_REPLACE(UPPER(TRANSLATE(r.empresa,
               'ÁÉÍÓÚÀÈÌÒÙÄËÏÖÜÂÊÎÔÛÑÇáéíóúàèìòùäëïöüâêîôûñç',
               'AEIOUAEIOUAEIOUAEIOUNCaeiouaeiouaeiouaeiounc')), '[[:space:]]+', ' '))
       AND r.corte BETWEEN ce.corte_desde AND ce.corte_hasta
)
SELECT s.valor,
       s.corte,
       co.columna_id,
       i.indicador_id
  FROM stg_indicadores s
  JOIN indicadores i ON i.corte = s.corte AND i.hoja = s.hoja AND i.fila = s.fila
  JOIN columnas co   ON co.corte = s.corte AND co.empresa = s.empresa
 WHERE s.serie = 'S-367';

PROMPT == 8. fct_riesgo (solo S-367, D-PF01-08) ==

INSERT INTO fct_riesgo (valor, fecha_corte, columna_id, riesgo_id, hoja)
WITH riesgos AS (
    -- Riesgo de cada rótulo publicado: se normaliza una vez por rótulo.
    SELECT /*+ MATERIALIZE */ c.concepto, r.riesgo_id
      FROM (SELECT DISTINCT concepto
              FROM stg_riesgos
             WHERE serie = 'S-367') c
      JOIN dim_riesgo r
        ON r.clave = TRIM(REGEXP_REPLACE(UPPER(TRANSLATE(c.concepto,
               'ÁÉÍÓÚÀÈÌÒÙÄËÏÖÜÂÊÎÔÛÑÇáéíóúàèìòùäëïöüâêîôûñç',
               'AEIOUAEIOUAEIOUAEIOUNCaeiouaeiouaeiouaeiounc')), '[[:space:]]+', ' '))
),
columnas AS (
    -- Columna de empresa de cada rótulo publicado y corte: se normaliza una vez por rótulo.
    SELECT /*+ MATERIALIZE */ r.corte, r.empresa, ce.columna_id
      FROM (SELECT DISTINCT corte, empresa
              FROM stg_riesgos
             WHERE serie = 'S-367') r
      JOIN dim_columna_empresa ce
        ON ce.clave_fuente = TRIM(REGEXP_REPLACE(UPPER(TRANSLATE(r.empresa,
               'ÁÉÍÓÚÀÈÌÒÙÄËÏÖÜÂÊÎÔÛÑÇáéíóúàèìòùäëïöüâêîôûñç',
               'AEIOUAEIOUAEIOUAEIOUNCaeiouaeiouaeiouaeiounc')), '[[:space:]]+', ' '))
       AND r.corte BETWEEN ce.corte_desde AND ce.corte_hasta
)
SELECT s.valor,
       s.corte,
       co.columna_id,
       ri.riesgo_id,
       s.hoja
  FROM stg_riesgos s
  JOIN riesgos ri  ON ri.concepto = s.concepto
  JOIN columnas co ON co.corte = s.corte AND co.empresa = s.empresa
 WHERE s.serie = 'S-367';

PROMPT == 9. Control: cada tabla de hechos tiene todas las celdas de su stg_ ==

DECLARE
    v_hechos NUMBER;
    v_stg    NUMBER;

    PROCEDURE comprobar(p_tabla IN VARCHAR2, p_hechos IN NUMBER, p_stg IN NUMBER) IS
    BEGIN
        IF p_hechos <> p_stg THEN
            RAISE_APPLICATION_ERROR(-20001, p_tabla || ': ' || p_hechos || ' filas cargadas de '
                || p_stg || ' celdas S-367 en stg_; una celda no tiene equivalencia única en '
                || 'alguna dimensión');
        END IF;
    END comprobar;
BEGIN
    SELECT COUNT(*) INTO v_hechos FROM fct_estado_financiero;
    SELECT COUNT(*) INTO v_stg FROM stg_estados_financieros WHERE serie = 'S-367';
    comprobar('fct_estado_financiero', v_hechos, v_stg);

    SELECT COUNT(*) INTO v_hechos FROM fct_indicador;
    SELECT COUNT(*) INTO v_stg FROM stg_indicadores WHERE serie = 'S-367';
    comprobar('fct_indicador', v_hechos, v_stg);

    SELECT COUNT(*) INTO v_hechos FROM fct_riesgo;
    SELECT COUNT(*) INTO v_stg FROM stg_riesgos WHERE serie = 'S-367';
    comprobar('fct_riesgo', v_hechos, v_stg);
END;
/

COMMIT;

PROMPT == 10. Estadísticas del optimizador de dim_ y fct_ ==

-- Después del COMMIT: DBMS_STATS confirma de forma implícita.
BEGIN
    FOR t IN (SELECT table_name
                FROM user_tables
               WHERE SUBSTR(table_name, 1, 4) IN ('DIM_', 'FCT_')
               ORDER BY table_name) LOOP
        DBMS_STATS.GATHER_TABLE_STATS(ownname => USER, tabname => t.table_name);
    END LOOP;
END;
/

PROMPT == Fin de 03_carga_modelo.sql ==
