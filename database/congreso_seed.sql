-- ============================================================
-- ACTA CIVIUM — Seed: Congreso de los Diputados
-- Ejecutar después de schema.sql
-- ============================================================

-- Municipio (usamos la tabla municipios como contenedor genérico de instituciones)
insert into municipios (
    nombre, nombre_alt, slug, provincia, comunidad, poblacion,
    n_concejales, alcalde, partido_gobierno, color_gobierno,
    web_oficial, url_actas
) values (
    'Congreso de los Diputados',
    'Congreso',
    'congreso',
    'Madrid',
    'Nacional',
    48000000,
    350,
    'Francina Armengol Socías',   -- Presidenta del Congreso
    'PSOE',
    '#E31C23',
    'https://www.congreso.es',
    'https://www.congreso.es/public_oficiales/L15/CONG/DS/PL/'
);

-- Grupos parlamentarios (XV Legislatura, composición aproximada 2024)
-- municipio_id se resuelve por nombre para evitar depender del UUID generado

with muni as (
    select id from municipios where slug = 'congreso' limit 1
)
insert into partidos (municipio_id, nombre, siglas, color_hex, posicion, n_concejales) values
    ((select id from muni), 'Grupo Parlamentario Popular',                'PP',      '#003A94', 'derecha',         137),
    ((select id from muni), 'Grupo Parlamentario Socialista',             'PSOE',    '#E31C23', 'centro_izquierda',117),
    ((select id from muni), 'Grupo Parlamentario Vox',                    'VOX',     '#5FC946', 'derecha',          33),
    ((select id from muni), 'Grupo Plurinacional Sumar',                  'SUMAR',   '#9B3CA0', 'izquierda',        29),
    ((select id from muni), 'Grupo Parlamentario Junts per Catalunya',    'Junts',   '#ED1B34', 'centro_derecha',   11),
    ((select id from muni), 'Grupo Parlamentario Republicano',            'ERC',     '#FFBB22', 'izquierda',         9),
    ((select id from muni), 'Grupo Parlamentario Euskal Herria Bildu',    'EH Bildu','#5B2D8E', 'izquierda',         6),
    ((select id from muni), 'Grupo Parlamentario Vasco EAJ-PNV',         'PNV',     '#FFCC00', 'centro',            5),
    ((select id from muni), 'Grupo Mixto',                               'Mixto',   '#AAAAAA', 'otro',              3);
