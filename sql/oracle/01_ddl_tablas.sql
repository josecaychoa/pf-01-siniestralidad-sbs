-- =============================================================================
-- PF-01 · Producción y siniestralidad por riesgo del mercado asegurador
-- peruano, 2019-2026
-- Script:  sql/oracle/01_ddl_tablas.sql
-- Paquete: 2.3 Modelo de datos Oracle (issue #6)
-- =============================================================================
--
-- Propósito
--   Crea las tablas del modelo de datos en el esquema del proyecto:
--   - 3 tablas stg_, espejo de los CSV de data/interim/, con las columnas de
--     la sección 1 de docs/03_diccionario_datos.md.
--   - 7 tablas dim_ y 3 tablas fct_ del modelo relacional, con los nombres,
--     columnas, tipos, llaves primarias y llaves foráneas de
--     docs/modelo/ddl_generado_datamodeler.sql.
--   - Restricciones CHECK de dominio en dim_columna_empresa (D-PF01-07).
--   - Índices en las columnas de llave foránea que no encabezan la llave
--     primaria de su tabla.
--   - Comentarios de tabla y de columna (COMMENT ON).
--
-- Orden de ejecución
--   1. Es el primer script de sql/oracle/; después van 02_vistas_*,
--      03_plsql_* y 04_cargas_*.
--   2. Dentro del script: tablas stg_, tablas dim_, tablas fct_, llaves
--      primarias, llaves foráneas, restricciones CHECK, índices y
--      comentarios. Las llaves foráneas van después de todas las llaves
--      primarias porque las referencian.
--
-- Requisitos
--   - Oracle Database 23ai o posterior: usa CREATE TABLE IF NOT EXISTS y el
--     tipo BOOLEAN. Desarrollo en la base nativa 23.6 (D-PF01-03); validación
--     final en el contenedor gvenzl/oracle-free:23.26.3.
--   - Usuario del proyecto (ORACLE_USER en .env) con privilegio CREATE TABLE
--     y cuota en su tablespace por defecto.
--   - Ejecución con SQLcl o SQL*Plus, por ejemplo:
--       sql pf01@localhost:1521/FREEPDB1 @sql/oracle/01_ddl_tablas.sql
--     La contraseña se pide al conectar; no se escribe en el script.
--
-- Idempotencia
--   - Tablas: CREATE TABLE IF NOT EXISTS.
--   - Llaves primarias, llaves foráneas, restricciones CHECK e índices: un
--     bloque PL/SQL por objeto que consulta USER_CONSTRAINTS o USER_INDEXES y
--     lo crea solo si no existe.
--   - Comentarios: COMMENT ON reemplaza el texto en cada ejecución.
--   El script no modifica tablas que ya existen: si una tabla existe con otra
--   estructura, la conserva. Los cambios de estructura van en un script nuevo.
--
-- Tipos de datos
--   - valor: NUMBER sin precisión en stg_ y fct_ (D-PF01-06).
--   - Las tablas stg_ declaran la longitud del texto en caracteres (CHAR),
--     porque la base mide VARCHAR2 en bytes (NLS_LENGTH_SEMANTICS = BYTE) y
--     los rótulos llevan tildes.
--   - es_total usa BOOLEAN, el tipo lógico de Oracle 23ai.
--   - Las tablas dim_ y fct_ conservan los tipos del DDL de referencia.
--
-- Decisiones: D-PF01-03 (desarrollo en la base nativa), D-PF01-05 (nombres en
-- español, snake_case y prefijos stg_, dim_ y fct_), D-PF01-06 (valor NUMBER
-- sin precisión) y D-PF01-07 (dominios de en_total_simple y tipo_columna).
-- =============================================================================

WHENEVER SQLERROR EXIT FAILURE

PROMPT == 1. Tablas stg_ (espejo de data/interim/) ==

-- Espejo de data/interim/estados_financieros.csv: hojas P001 y P002 (S-367).
CREATE TABLE IF NOT EXISTS stg_estados_financieros (
    serie             VARCHAR2(10 CHAR)  NOT NULL,
    corte             DATE               NOT NULL,
    hoja              VARCHAR2(4 CHAR)   NOT NULL,
    cuadro            VARCHAR2(150 CHAR) NOT NULL,
    unidad            VARCHAR2(30 CHAR),
    seccion           VARCHAR2(100 CHAR),
    fila              NUMBER(7)          NOT NULL,
    columna           NUMBER(5)          NOT NULL,
    concepto_original VARCHAR2(200 CHAR) NOT NULL,
    concepto          VARCHAR2(200 CHAR) NOT NULL,
    sangria           NUMBER(3)          NOT NULL,
    llamadas_concepto VARCHAR2(30 CHAR),
    empresa_original  VARCHAR2(150 CHAR) NOT NULL,
    empresa           VARCHAR2(150 CHAR) NOT NULL,
    llamadas_empresa  VARCHAR2(30 CHAR),
    es_total          BOOLEAN            NOT NULL,
    moneda            VARCHAR2(5 CHAR),
    valor             NUMBER             NOT NULL,
    sha256_archivo    VARCHAR2(64 CHAR)  NOT NULL
);

-- Espejo de data/interim/indicadores.csv: hojas P003 y P004 (S-367).
CREATE TABLE IF NOT EXISTS stg_indicadores (
    serie             VARCHAR2(10 CHAR)  NOT NULL,
    corte             DATE               NOT NULL,
    hoja              VARCHAR2(4 CHAR)   NOT NULL,
    cuadro            VARCHAR2(150 CHAR) NOT NULL,
    unidad            VARCHAR2(30 CHAR),
    seccion           VARCHAR2(100 CHAR),
    fila              NUMBER(7)          NOT NULL,
    columna           NUMBER(5)          NOT NULL,
    concepto_original VARCHAR2(200 CHAR) NOT NULL,
    concepto          VARCHAR2(200 CHAR) NOT NULL,
    sangria           NUMBER(3)          NOT NULL,
    llamadas_concepto VARCHAR2(30 CHAR),
    empresa_original  VARCHAR2(150 CHAR) NOT NULL,
    empresa           VARCHAR2(150 CHAR) NOT NULL,
    llamadas_empresa  VARCHAR2(30 CHAR),
    es_total          BOOLEAN            NOT NULL,
    moneda            VARCHAR2(5 CHAR),
    valor             NUMBER             NOT NULL,
    sha256_archivo    VARCHAR2(64 CHAR)  NOT NULL
);

-- Espejo de data/interim/riesgos.csv: hojas P009 a P016 (S-367, S-401,
-- S-402 y S-403).
CREATE TABLE IF NOT EXISTS stg_riesgos (
    serie             VARCHAR2(10 CHAR)  NOT NULL,
    corte             DATE               NOT NULL,
    hoja              VARCHAR2(4 CHAR)   NOT NULL,
    cuadro            VARCHAR2(150 CHAR) NOT NULL,
    unidad            VARCHAR2(30 CHAR),
    seccion           VARCHAR2(100 CHAR),
    fila              NUMBER(7)          NOT NULL,
    columna           NUMBER(5)          NOT NULL,
    concepto_original VARCHAR2(200 CHAR) NOT NULL,
    concepto          VARCHAR2(200 CHAR) NOT NULL,
    sangria           NUMBER(3)          NOT NULL,
    llamadas_concepto VARCHAR2(30 CHAR),
    empresa_original  VARCHAR2(150 CHAR) NOT NULL,
    empresa           VARCHAR2(150 CHAR) NOT NULL,
    llamadas_empresa  VARCHAR2(30 CHAR),
    es_total          BOOLEAN            NOT NULL,
    moneda            VARCHAR2(5 CHAR),
    valor             NUMBER             NOT NULL,
    sha256_archivo    VARCHAR2(64 CHAR)  NOT NULL
);

PROMPT == 2. Tablas dim_ ==

CREATE TABLE IF NOT EXISTS dim_columna_empresa (
    columna_id      NUMBER(6)     NOT NULL,
    clave_fuente    VARCHAR2(120) NOT NULL,
    corte_desde     DATE          NOT NULL,
    corte_hasta     DATE          NOT NULL,
    tipo_columna    VARCHAR2(15)  NOT NULL,
    entidad         VARCHAR2(150),
    estado          VARCHAR2(10),
    en_total_simple VARCHAR2(1)   NOT NULL,
    evento          VARCHAR2(200),
    fuente_evento   VARCHAR2(200),
    empresa_id      VARCHAR2(30)
);

CREATE TABLE IF NOT EXISTS dim_corte (
    fecha_corte      DATE          NOT NULL,
    meses_acumulados NUMBER(2)     NOT NULL,
    plan_de_cuentas  VARCHAR2(100) NOT NULL,
    resolucion_plan  VARCHAR2(20)
);

CREATE TABLE IF NOT EXISTS dim_cuadro (
    hoja   VARCHAR2(4)   NOT NULL,
    cuadro VARCHAR2(150) NOT NULL,
    unidad VARCHAR2(30),
    grupo  VARCHAR2(20)  NOT NULL,
    medida VARCHAR2(40)  NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_cuenta (
    cuenta_id NUMBER(6)     NOT NULL,
    clave     VARCHAR2(150) NOT NULL,
    cuenta    VARCHAR2(150) NOT NULL,
    nivel     NUMBER(2),
    hoja      VARCHAR2(4)   NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_empresa (
    empresa_id VARCHAR2(30)  NOT NULL,
    empresa    VARCHAR2(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_indicador (
    indicador_id NUMBER(6)     NOT NULL,
    seccion      VARCHAR2(100) NOT NULL,
    clave        VARCHAR2(150) NOT NULL,
    indicador    VARCHAR2(150) NOT NULL,
    hoja         VARCHAR2(4)   NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_riesgo (
    riesgo_id         NUMBER(3)     NOT NULL,
    clave             VARCHAR2(80)  NOT NULL,
    riesgo            VARCHAR2(100) NOT NULL,
    nivel             NUMBER(1)     NOT NULL,
    tipo              VARCHAR2(10)  NOT NULL,
    ramo              VARCHAR2(50),
    riesgo_comparable VARCHAR2(100) NOT NULL,
    corte_desde       DATE          NOT NULL,
    nota              VARCHAR2(400),
    riesgo_padre_id   NUMBER(3)
);

PROMPT == 3. Tablas fct_ ==

CREATE TABLE IF NOT EXISTS fct_estado_financiero (
    moneda      VARCHAR2(5) NOT NULL,
    valor       NUMBER      NOT NULL,
    columna_id  NUMBER(6)   NOT NULL,
    cuenta_id   NUMBER(6)   NOT NULL,
    fecha_corte DATE        NOT NULL
);

CREATE TABLE IF NOT EXISTS fct_indicador (
    valor        NUMBER    NOT NULL,
    fecha_corte  DATE      NOT NULL,
    columna_id   NUMBER(6) NOT NULL,
    indicador_id NUMBER(6) NOT NULL
);

CREATE TABLE IF NOT EXISTS fct_riesgo (
    valor       NUMBER      NOT NULL,
    fecha_corte DATE        NOT NULL,
    columna_id  NUMBER(6)   NOT NULL,
    riesgo_id   NUMBER(3)   NOT NULL,
    hoja        VARCHAR2(4) NOT NULL
);

PROMPT == 4. Llaves primarias ==

-- stg_: llave única de la sección 1 del diccionario (serie, corte, hoja,
-- fila y columna).
DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'STG_ESTADOS_FINANCIEROS' AND constraint_name = 'PK_STG_ESTADOS_FINANCIEROS';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE stg_estados_financieros ADD CONSTRAINT pk_stg_estados_financieros PRIMARY KEY (serie, corte, hoja, fila, columna)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'STG_INDICADORES' AND constraint_name = 'PK_STG_INDICADORES';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE stg_indicadores ADD CONSTRAINT pk_stg_indicadores PRIMARY KEY (serie, corte, hoja, fila, columna)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'STG_RIESGOS' AND constraint_name = 'PK_STG_RIESGOS';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE stg_riesgos ADD CONSTRAINT pk_stg_riesgos PRIMARY KEY (serie, corte, hoja, fila, columna)';
    END IF;
END;
/

-- dim_ y fct_: nombres y columnas del DDL de referencia.
DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'DIM_COLUMNA_EMPRESA' AND constraint_name = 'PK_DIM_COLUMNA_EMPRESA';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE dim_columna_empresa ADD CONSTRAINT pk_dim_columna_empresa PRIMARY KEY (columna_id)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'DIM_CORTE' AND constraint_name = 'PK_DIM_CORTE';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE dim_corte ADD CONSTRAINT pk_dim_corte PRIMARY KEY (fecha_corte)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'DIM_CUADRO' AND constraint_name = 'PK_DIM_CUADRO';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE dim_cuadro ADD CONSTRAINT pk_dim_cuadro PRIMARY KEY (hoja)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'DIM_CUENTA' AND constraint_name = 'PK_DIM_CUENTA';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE dim_cuenta ADD CONSTRAINT pk_dim_cuenta PRIMARY KEY (cuenta_id)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'DIM_EMPRESA' AND constraint_name = 'PK_DIM_EMPRESA';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE dim_empresa ADD CONSTRAINT pk_dim_empresa PRIMARY KEY (empresa_id)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'DIM_INDICADOR' AND constraint_name = 'PK_DIM_INDICADOR';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE dim_indicador ADD CONSTRAINT pk_dim_indicador PRIMARY KEY (indicador_id)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'DIM_RIESGO' AND constraint_name = 'PK_DIM_RIESGO';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE dim_riesgo ADD CONSTRAINT pk_dim_riesgo PRIMARY KEY (riesgo_id)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'FCT_ESTADO_FINANCIERO' AND constraint_name = 'PK_FCT_ESTADO_FINANCIERO';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE fct_estado_financiero ADD CONSTRAINT pk_fct_estado_financiero PRIMARY KEY (moneda, columna_id, cuenta_id, fecha_corte)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'FCT_INDICADOR' AND constraint_name = 'PK_FCT_INDICADOR';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE fct_indicador ADD CONSTRAINT pk_fct_indicador PRIMARY KEY (fecha_corte, columna_id, indicador_id)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'FCT_RIESGO' AND constraint_name = 'PK_FCT_RIESGO';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE fct_riesgo ADD CONSTRAINT pk_fct_riesgo PRIMARY KEY (fecha_corte, columna_id, riesgo_id, hoja)';
    END IF;
END;
/

PROMPT == 5. Llaves foráneas ==

-- Nombres y columnas del DDL de referencia.
DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'DIM_COLUMNA_EMPRESA' AND constraint_name = 'FK_DIM_COLUMNA_EMPRESA_EMPRESA';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE dim_columna_empresa ADD CONSTRAINT fk_dim_columna_empresa_empresa FOREIGN KEY (empresa_id) REFERENCES dim_empresa (empresa_id)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'DIM_CUENTA' AND constraint_name = 'FK_DIM_CUENTA_CUADRO';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE dim_cuenta ADD CONSTRAINT fk_dim_cuenta_cuadro FOREIGN KEY (hoja) REFERENCES dim_cuadro (hoja)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'DIM_INDICADOR' AND constraint_name = 'FK_DIM_INDICADOR_CUADRO';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE dim_indicador ADD CONSTRAINT fk_dim_indicador_cuadro FOREIGN KEY (hoja) REFERENCES dim_cuadro (hoja)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'DIM_RIESGO' AND constraint_name = 'FK_DIM_RIESGO_PADRE';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE dim_riesgo ADD CONSTRAINT fk_dim_riesgo_padre FOREIGN KEY (riesgo_padre_id) REFERENCES dim_riesgo (riesgo_id)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'FCT_ESTADO_FINANCIERO' AND constraint_name = 'FK_FCT_ESTFIN_COLUMNA';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE fct_estado_financiero ADD CONSTRAINT fk_fct_estfin_columna FOREIGN KEY (columna_id) REFERENCES dim_columna_empresa (columna_id)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'FCT_ESTADO_FINANCIERO' AND constraint_name = 'FK_FCT_ESTFIN_CORTE';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE fct_estado_financiero ADD CONSTRAINT fk_fct_estfin_corte FOREIGN KEY (fecha_corte) REFERENCES dim_corte (fecha_corte)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'FCT_ESTADO_FINANCIERO' AND constraint_name = 'FK_FCT_ESTFIN_CUENTA';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE fct_estado_financiero ADD CONSTRAINT fk_fct_estfin_cuenta FOREIGN KEY (cuenta_id) REFERENCES dim_cuenta (cuenta_id)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'FCT_INDICADOR' AND constraint_name = 'FK_FCT_INDICADOR_COLUMNA';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE fct_indicador ADD CONSTRAINT fk_fct_indicador_columna FOREIGN KEY (columna_id) REFERENCES dim_columna_empresa (columna_id)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'FCT_INDICADOR' AND constraint_name = 'FK_FCT_INDICADOR_CORTE';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE fct_indicador ADD CONSTRAINT fk_fct_indicador_corte FOREIGN KEY (fecha_corte) REFERENCES dim_corte (fecha_corte)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'FCT_INDICADOR' AND constraint_name = 'FK_FCT_INDICADOR_INDICADOR';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE fct_indicador ADD CONSTRAINT fk_fct_indicador_indicador FOREIGN KEY (indicador_id) REFERENCES dim_indicador (indicador_id)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'FCT_RIESGO' AND constraint_name = 'FK_FCT_RIESGO_COLUMNA';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE fct_riesgo ADD CONSTRAINT fk_fct_riesgo_columna FOREIGN KEY (columna_id) REFERENCES dim_columna_empresa (columna_id)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'FCT_RIESGO' AND constraint_name = 'FK_FCT_RIESGO_CORTE';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE fct_riesgo ADD CONSTRAINT fk_fct_riesgo_corte FOREIGN KEY (fecha_corte) REFERENCES dim_corte (fecha_corte)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'FCT_RIESGO' AND constraint_name = 'FK_FCT_RIESGO_CUADRO';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE fct_riesgo ADD CONSTRAINT fk_fct_riesgo_cuadro FOREIGN KEY (hoja) REFERENCES dim_cuadro (hoja)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'FCT_RIESGO' AND constraint_name = 'FK_FCT_RIESGO_RIESGO';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE fct_riesgo ADD CONSTRAINT fk_fct_riesgo_riesgo FOREIGN KEY (riesgo_id) REFERENCES dim_riesgo (riesgo_id)';
    END IF;
END;
/

PROMPT == 6. Restricciones CHECK ==

-- Dominios de dim_columna_empresa (D-PF01-07).
-- tipo_columna: valores de validacion.tipo_total() y del catálogo empresas.csv.
--   empresa         columna de una empresa (filas de empresas.csv)
--   total_simple    columna «Total» o «Total empresas de seguros»
--   total_ampliado  columna «Total + …», que suma también las empresas que
--                   dejaron de operar en el año (D-PF01-01)
DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'DIM_COLUMNA_EMPRESA' AND constraint_name = 'CK_DIM_COLUMNA_EMPRESA_TIPO_COLUMNA';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE dim_columna_empresa ADD CONSTRAINT ck_dim_columna_empresa_tipo_columna CHECK (tipo_columna IN (''empresa'', ''total_simple'', ''total_ampliado''))';
    END IF;
END;
/

-- en_total_simple: S si la columna entra en el total simple; N en los flujos
-- de empresas que dejaron de operar en el año (D-PF01-01). El catálogo
-- empresas.csv lo guarda como true y false.
DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_constraints
     WHERE table_name = 'DIM_COLUMNA_EMPRESA' AND constraint_name = 'CK_DIM_COLUMNA_EMPRESA_EN_TOTAL_SIMPLE';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'ALTER TABLE dim_columna_empresa ADD CONSTRAINT ck_dim_columna_empresa_en_total_simple CHECK (en_total_simple IN (''S'', ''N''))';
    END IF;
END;
/

PROMPT == 7. Índices de llaves foráneas ==

-- Un índice por llave foránea cuya columna no encabeza la llave primaria de
-- su tabla: acelera los joins con las dimensiones y evita el bloqueo de la
-- tabla hija al borrar o actualizar una fila de la tabla padre. Las llaves
-- fk_fct_indicador_corte y fk_fct_riesgo_corte no lo necesitan, porque
-- fecha_corte encabeza la llave primaria. Nombre: ix_ + sufijo de la fk_.
DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_indexes
     WHERE table_name = 'DIM_COLUMNA_EMPRESA' AND index_name = 'IX_DIM_COLUMNA_EMPRESA_EMPRESA';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'CREATE INDEX ix_dim_columna_empresa_empresa ON dim_columna_empresa (empresa_id)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_indexes
     WHERE table_name = 'DIM_CUENTA' AND index_name = 'IX_DIM_CUENTA_CUADRO';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'CREATE INDEX ix_dim_cuenta_cuadro ON dim_cuenta (hoja)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_indexes
     WHERE table_name = 'DIM_INDICADOR' AND index_name = 'IX_DIM_INDICADOR_CUADRO';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'CREATE INDEX ix_dim_indicador_cuadro ON dim_indicador (hoja)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_indexes
     WHERE table_name = 'DIM_RIESGO' AND index_name = 'IX_DIM_RIESGO_PADRE';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'CREATE INDEX ix_dim_riesgo_padre ON dim_riesgo (riesgo_padre_id)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_indexes
     WHERE table_name = 'FCT_ESTADO_FINANCIERO' AND index_name = 'IX_FCT_ESTFIN_COLUMNA';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'CREATE INDEX ix_fct_estfin_columna ON fct_estado_financiero (columna_id)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_indexes
     WHERE table_name = 'FCT_ESTADO_FINANCIERO' AND index_name = 'IX_FCT_ESTFIN_CORTE';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'CREATE INDEX ix_fct_estfin_corte ON fct_estado_financiero (fecha_corte)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_indexes
     WHERE table_name = 'FCT_ESTADO_FINANCIERO' AND index_name = 'IX_FCT_ESTFIN_CUENTA';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'CREATE INDEX ix_fct_estfin_cuenta ON fct_estado_financiero (cuenta_id)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_indexes
     WHERE table_name = 'FCT_INDICADOR' AND index_name = 'IX_FCT_INDICADOR_COLUMNA';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'CREATE INDEX ix_fct_indicador_columna ON fct_indicador (columna_id)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_indexes
     WHERE table_name = 'FCT_INDICADOR' AND index_name = 'IX_FCT_INDICADOR_INDICADOR';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'CREATE INDEX ix_fct_indicador_indicador ON fct_indicador (indicador_id)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_indexes
     WHERE table_name = 'FCT_RIESGO' AND index_name = 'IX_FCT_RIESGO_COLUMNA';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'CREATE INDEX ix_fct_riesgo_columna ON fct_riesgo (columna_id)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_indexes
     WHERE table_name = 'FCT_RIESGO' AND index_name = 'IX_FCT_RIESGO_CUADRO';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'CREATE INDEX ix_fct_riesgo_cuadro ON fct_riesgo (hoja)';
    END IF;
END;
/

DECLARE
    v_existe PLS_INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_existe FROM user_indexes
     WHERE table_name = 'FCT_RIESGO' AND index_name = 'IX_FCT_RIESGO_RIESGO';
    IF v_existe = 0 THEN
        EXECUTE IMMEDIATE 'CREATE INDEX ix_fct_riesgo_riesgo ON fct_riesgo (riesgo_id)';
    END IF;
END;
/

PROMPT == 8. Comentarios ==

COMMENT ON TABLE stg_estados_financieros IS 'Espejo de data/interim/estados_financieros.csv: celdas numéricas de las hojas P001 y P002 del Boletín Mensual S-367 de la SBS';
COMMENT ON TABLE stg_indicadores IS 'Espejo de data/interim/indicadores.csv: celdas numéricas de las hojas P003 y P004 del Boletín Mensual S-367 de la SBS';
COMMENT ON TABLE stg_riesgos IS 'Espejo de data/interim/riesgos.csv: celdas numéricas de las hojas P009 a P016 del Boletín Mensual S-367 y de los cuadros S-401, S-402 y S-403 de la SBS';
COMMENT ON TABLE dim_columna_empresa IS 'Equivalencia de cada columna de empresa de la fuente con la empresa del análisis, por rango de cortes (catálogo empresas.csv)';
COMMENT ON TABLE dim_corte IS 'Cortes del análisis: meses acumulados y versión del plan de cuentas (catálogo cortes.csv)';
COMMENT ON TABLE dim_cuadro IS 'Hojas del Boletín Mensual S-367 que usa el proyecto, con su título y unidad';
COMMENT ON TABLE dim_cuenta IS 'Cuentas de los estados financieros de las hojas P001 y P002';
COMMENT ON TABLE dim_empresa IS 'Empresas de seguros para el análisis en el tiempo, con su denominación vigente (catálogo empresas.csv)';
COMMENT ON TABLE dim_indicador IS 'Indicadores y cifras para indicadores de las hojas P003 y P004';
COMMENT ON TABLE dim_riesgo IS 'Catálogo de riesgos con jerarquía de cinco niveles (catálogo riesgos.csv)';
COMMENT ON TABLE fct_estado_financiero IS 'Cifras de los estados financieros (P001 y P002) por corte, cuenta, columna de empresa y moneda';
COMMENT ON TABLE fct_indicador IS 'Cifras de las hojas P003 y P004 por corte, indicador y columna de empresa';
COMMENT ON TABLE fct_riesgo IS 'Primas, siniestros e índices de siniestralidad (P009 a P016) por corte, riesgo, columna de empresa y hoja';
COMMENT ON COLUMN dim_columna_empresa.tipo_columna IS 'empresa, total_simple (columna «Total» o «Total empresas de seguros») o total_ampliado (columna «Total + …») (D-PF01-07)';
COMMENT ON COLUMN dim_columna_empresa.en_total_simple IS 'S si la columna entra en el total simple; N en los flujos de empresas que dejaron de operar en el año (D-PF01-01 y D-PF01-07)';

-- Comentarios de columna de las tablas stg_: un texto por columna, tomado de
-- la sección 1 del diccionario, que se aplica a las tres tablas.
DECLARE
    TYPE t_comentarios IS TABLE OF VARCHAR2(500 CHAR) INDEX BY VARCHAR2(30);
    TYPE t_tablas IS TABLE OF VARCHAR2(30);
    v_comentario t_comentarios;
    v_tablas     t_tablas := t_tablas('STG_ESTADOS_FINANCIEROS', 'STG_INDICADORES', 'STG_RIESGOS');
    v_columna    VARCHAR2(30);
BEGIN
    v_comentario('SERIE')             := 'Serie de la SBS: S-367 (Boletín Mensual) o S-401, S-402 y S-403 (cuadros de consistencia)';
    v_comentario('CORTE')             := 'Fecha de corte; se valida contra el rótulo «Al … de … del …» de cada hoja';
    v_comentario('HOJA')              := 'Hoja del libro (P001 … P016), sin espacios';
    v_comentario('CUADRO')            := 'Título de la hoja, sin llamadas a nota';
    v_comentario('UNIDAD')            := 'Unidad declarada bajo el título («En Miles de Soles», «En Porcentaje»); vacía en P004, donde la unidad está en la sección';
    v_comentario('SECCION')           := 'Solo P004: grupo del indicador (p. ej., «DE SOLVENCIA (N° de veces)»)';
    v_comentario('FILA')              := 'Fila de la celda en la hoja, en numeración de Excel (1 = primera)';
    v_comentario('COLUMNA')           := 'Columna de la celda en la hoja, en numeración de Excel (1 = primera)';
    v_comentario('CONCEPTO_ORIGINAL') := 'Etiqueta de la fila tal como se publica (cuenta, riesgo o indicador)';
    v_comentario('CONCEPTO')          := 'Etiqueta sin llamadas a nota y sin espacios repetidos';
    v_comentario('SANGRIA')           := 'Espacios iniciales de la etiqueta; indica el nivel en P001 y P002';
    v_comentario('LLAMADAS_CONCEPTO') := 'Llamadas a nota de la etiqueta («7/ 8/»)';
    v_comentario('EMPRESA_ORIGINAL')  := 'Encabezado de la columna tal como se publica';
    v_comentario('EMPRESA')           := 'Encabezado sin llamadas a nota; la equivalencia entre razones sociales se resuelve en dim_columna_empresa';
    v_comentario('LLAMADAS_EMPRESA')  := 'Llamadas a nota del encabezado («1/», «(3)»)';
    v_comentario('ES_TOTAL')          := 'Verdadero si el encabezado empieza por «Total» (incluye «Total + Mapfre Perú (abs)»)';
    v_comentario('MONEDA')            := 'Solo P001 y P002: MN, ME o TOTAL';
    v_comentario('VALOR')             := 'Cifra publicada (miles de soles, porcentaje o veces, según la hoja); NUMBER sin precisión (D-PF01-06)';
    v_comentario('SHA256_ARCHIVO')    := 'SHA-256 del archivo de origen en data/raw/manifest.csv';

    FOR i IN 1 .. v_tablas.COUNT LOOP
        v_columna := v_comentario.FIRST;
        WHILE v_columna IS NOT NULL LOOP
            EXECUTE IMMEDIATE 'COMMENT ON COLUMN '
                || DBMS_ASSERT.SIMPLE_SQL_NAME(v_tablas(i)) || '.'
                || DBMS_ASSERT.SIMPLE_SQL_NAME(v_columna)
                || ' IS ' || DBMS_ASSERT.ENQUOTE_LITERAL(v_comentario(v_columna));
            v_columna := v_comentario.NEXT(v_columna);
        END LOOP;
    END LOOP;
END;
/

PROMPT == Fin de 01_ddl_tablas.sql ==
