-- ============================================================
-- ACTA CIVIUM — Schema PostgreSQL (Supabase)
-- ============================================================

-- Extensiones
create extension if not exists "uuid-ossp";
create extension if not exists "unaccent";
create extension if not exists "pg_trgm";  -- búsqueda full-text difusa

-- ============================================================
-- MUNICIPIOS
-- ============================================================
create table municipios (
  id               uuid primary key default uuid_generate_v4(),
  nombre           text not null,
  nombre_alt       text,                        -- "Donostia" para San Sebastián
  slug             text unique,                 -- URL slug, e.g. "san-sebastian"
  provincia        text not null,
  comunidad        text not null,
  poblacion        integer,
  n_concejales     integer,
  alcalde          text,                        -- nombre del alcalde/alcaldesa actual
  partido_gobierno text,                        -- siglas del partido gobernante
  color_gobierno   text default '#1a3a2a',      -- color hex del partido
  web_oficial      text,
  url_actas        text,                        -- URL base que monitoriza el scraper
  activo           boolean not null default true,
  created_at       timestamptz not null default now()
);

-- Datos iniciales
insert into municipios (nombre, nombre_alt, slug, provincia, comunidad, poblacion,
                        n_concejales, alcalde, partido_gobierno, color_gobierno,
                        web_oficial, url_actas)
values (
  'San Sebastián', 'Donostia', 'san-sebastian',
  'Gipuzkoa', 'País Vasco', 188102, 27,
  'Juan Karlos Izagirre Hortelano', 'EH Bildu', '#5B2D8E',
  'https://www.donostia.eus',
  'https://www.donostia.eus/secretaria/AsuntosPleno.nsf/fwHome?ReadForm&idioma=cas&id=C511345'
);

-- ============================================================
-- PARTIDOS POLÍTICOS
-- ============================================================
create table partidos (
  id            uuid primary key default uuid_generate_v4(),
  municipio_id  uuid references municipios(id),  -- null = partido nacional/regional
  nombre        text not null,
  siglas        text not null,
  color_hex     text not null default '#888888',
  posicion      text check (posicion in (
                  'izquierda', 'centro_izquierda', 'centro',
                  'centro_derecha', 'derecha', 'otro'
                )) default 'otro',
  activo        boolean not null default true
);

-- Partidos iniciales de San Sebastián
with muni as (select id from municipios where nombre = 'San Sebastián' limit 1)
insert into partidos (municipio_id, nombre, siglas, color_hex, posicion) values
  ((select id from muni), 'Euzko Alderdi Jeltzalea / Partido Nacionalista Vasco', 'EAJ/PNV', '#007A3D', 'centro'),
  ((select id from muni), 'EH Bildu', 'EH Bildu', '#5B2D8E', 'izquierda'),
  ((select id from muni), 'Partido Socialista de Euskadi - Euskadiko Ezkerra', 'PSE-EE', '#E4003A', 'centro_izquierda'),
  ((select id from muni), 'Partido Popular', 'PP', '#003A94', 'derecha'),
  ((select id from muni), 'Elkarrekin Donostia', 'Elkarrekin', '#E53935', 'izquierda');

-- ============================================================
-- CONCEJALES
-- ============================================================
create table concejales (
  id            uuid primary key default uuid_generate_v4(),
  municipio_id  uuid not null references municipios(id),
  partido_id    uuid references partidos(id),
  nombre        text not null,
  cargo         text check (cargo in ('alcalde', 'teniente_alcalde', 'concejal')) default 'concejal',
  activo        boolean not null default true,
  fecha_inicio  date,
  fecha_fin     date
);

-- ============================================================
-- PLENOS
-- ============================================================
create table plenos (
  id                    uuid primary key default uuid_generate_v4(),
  municipio_id          uuid not null references municipios(id),
  numero_acta           integer not null,
  fecha                 date not null,
  tipo_sesion           text not null check (tipo_sesion in ('ordinaria', 'extraordinaria', 'urgente')),
  hora_inicio           time,
  hora_fin              time,
  alcalde_nombre        text,
  secretaria_nombre     text,
  url_pdf_original      text,
  texto_completo        text,                   -- full text extraído
  resumen_ia            text,                   -- generado por Claude
  n_puntos              integer,
  n_asistentes          integer,
  n_ausentes            integer,
  estado                text not null default 'pendiente'
                          check (estado in ('pendiente', 'procesado', 'error')),
  error_msg             text,
  created_at            timestamptz not null default now(),
  procesado_at          timestamptz,
  unique (municipio_id, numero_acta)
);

-- Índices para búsqueda
create index plenos_fecha_idx on plenos (fecha desc);
create index plenos_municipio_idx on plenos (municipio_id);
create index plenos_texto_fts on plenos using gin (to_tsvector('spanish', coalesce(texto_completo, '')));

-- ============================================================
-- ASISTENCIA A PLENOS
-- ============================================================
create table asistencia (
  id            uuid primary key default uuid_generate_v4(),
  pleno_id      uuid not null references plenos(id) on delete cascade,
  concejal_id   uuid references concejales(id),
  nombre_raw    text not null,                  -- nombre tal como aparece en el acta
  partido_id    uuid references partidos(id),
  asistio       boolean not null default true,
  cargo         text
);

-- ============================================================
-- PUNTOS DEL ORDEN DEL DÍA (corazón de la BD)
-- ============================================================
create table puntos (
  id                    uuid primary key default uuid_generate_v4(),
  pleno_id              uuid not null references plenos(id) on delete cascade,
  numero                integer not null,
  es_urgencia           boolean not null default false,

  -- Clasificación
  comision              text check (comision in (
                          'territorio', 'servicios_personas', 'servicios_generales',
                          'hacienda', 'informacion_control', 'pleno', 'otro'
                        )),
  tipo                  text check (tipo in (
                          'aprobacion_definitiva', 'aprobacion_inicial', 'dar_cuenta',
                          'proposicion_normativa', 'mocion', 'ruego',
                          'pregunta_oral', 'pregunta_escrita', 'interpelacion',
                          'declaracion_institucional', 'otro'
                        )),
  categoria             text check (categoria in (
                          'urbanismo', 'vivienda', 'hacienda', 'medio_ambiente',
                          'servicios_sociales', 'movilidad', 'cultura', 'gobernanza',
                          'derechos', 'seguridad', 'educacion', 'sanidad', 'otro'
                        )),

  -- Contenido
  titulo                text not null,
  texto_completo        text,
  grupo_proponente_id   uuid references partidos(id),  -- quien propone (oposición)

  -- Resultado
  resultado             text check (resultado in (
                          'aprobado', 'rechazado', 'enterado',
                          'retirado', 'aplazado', 'sin_votacion'
                        )),
  unanimidad            boolean,

  -- IA
  resumen_ia            text,                   -- resumen enfocado en impacto social
  relevancia_social     smallint check (relevancia_social between 1 and 5),
  -- 1=trámite administrativo, 5=alto impacto ciudadano

  created_at            timestamptz not null default now()
);

create index puntos_pleno_idx on puntos (pleno_id);
create index puntos_categoria_idx on puntos (categoria);
create index puntos_tipo_idx on puntos (tipo);
create index puntos_resultado_idx on puntos (resultado);
create index puntos_texto_fts on puntos using gin (to_tsvector('spanish', coalesce(titulo, '') || ' ' || coalesce(texto_completo, '')));

-- ============================================================
-- VOTACIONES POR PARTIDO (desglose fino)
-- ============================================================
create table votaciones (
  id              uuid primary key default uuid_generate_v4(),
  punto_id        uuid not null references puntos(id) on delete cascade,
  partido_id      uuid not null references partidos(id),
  votos_favor     smallint not null default 0,
  votos_contra    smallint not null default 0,
  abstenciones    smallint not null default 0,
  ausentes        smallint not null default 0,
  unique (punto_id, partido_id)
);

create index votaciones_punto_idx on votaciones (punto_id);
create index votaciones_partido_idx on votaciones (partido_id);

-- ============================================================
-- TAGS TEMÁTICOS (granulares, para filtros y SEO)
-- ============================================================
create table tags (
  id      uuid primary key default uuid_generate_v4(),
  nombre  text not null unique,   -- "alquiler", "IBI", "PGOU", "violencia de género"
  slug    text not null unique
);

create table punto_tags (
  punto_id  uuid not null references puntos(id) on delete cascade,
  tag_id    uuid not null references tags(id) on delete cascade,
  primary key (punto_id, tag_id)
);

-- ============================================================
-- LOG DE SCRAPING (para debug y trazabilidad)
-- ============================================================
create table scraping_log (
  id            uuid primary key default uuid_generate_v4(),
  municipio_id  uuid references municipios(id),
  ejecutado_at  timestamptz not null default now(),
  pdfs_nuevos   integer default 0,
  pdfs_error    integer default 0,
  duracion_seg  numeric,
  detalle       jsonb
);

-- ============================================================
-- VISTAS ÚTILES
-- ============================================================

-- Vista: resumen de pleno con conteo de puntos y votaciones
create or replace view v_plenos as
select
  p.id,
  p.numero_acta,
  p.fecha,
  p.tipo_sesion,
  p.resumen_ia,
  p.estado,
  m.nombre as municipio,
  p.n_asistentes,
  count(pu.id) as total_puntos,
  count(pu.id) filter (where pu.resultado = 'aprobado') as aprobados,
  count(pu.id) filter (where pu.resultado = 'rechazado') as rechazados,
  count(pu.id) filter (where pu.unanimidad = true) as unanimes
from plenos p
join municipios m on m.id = p.municipio_id
left join puntos pu on pu.pleno_id = p.id
group by p.id, m.nombre;

-- Vista: posición de cada partido por categoría temática
create or replace view v_votos_por_partido_categoria as
select
  pa.siglas as partido,
  pu.categoria,
  sum(v.votos_favor) as total_favor,
  sum(v.votos_contra) as total_contra,
  sum(v.abstenciones) as total_abstenciones
from votaciones v
join puntos pu on pu.id = v.punto_id
join partidos pa on pa.id = v.partido_id
where pu.categoria is not null
group by pa.siglas, pu.categoria
order by pa.siglas, pu.categoria;

-- Vista: puntos de alto impacto social
create or replace view v_puntos_relevantes as
select
  pu.id,
  pu.pleno_id,
  pu.titulo,
  pu.categoria,
  pu.tipo,
  pu.resultado,
  pu.unanimidad,
  pu.relevancia_social,
  pu.resumen_ia,
  pl.fecha,
  pl.numero_acta,
  m.nombre as municipio
from puntos pu
join plenos pl on pl.id = pu.pleno_id
join municipios m on m.id = pl.municipio_id
where pu.relevancia_social >= 4
order by pl.fecha desc, pu.relevancia_social desc;
