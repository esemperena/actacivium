# Acta Civium

Plataforma de transparencia municipal que extrae, estructura y publica las actas de los plenos del Ayuntamiento de San Sebastián con una mirada ciudadana, social y medioambiental.

## Estructura del proyecto

```
acta-civium/
├── scraper/          Python: descarga PDFs, extrae texto, llama a Claude
├── database/         Schema PostgreSQL para Supabase
├── web/              Frontend Astro + Tailwind (desplegado en Vercel)
├── newsletter/       Script de envío via Brevo
└── .env.example      Variables de entorno necesarias
```

## Stack técnico

| Capa | Herramienta | Coste |
|---|---|---|
| Scraping | Scrapling + pdfplumber | €0 |
| IA (resúmenes) | Claude Code CLI (licencia Pro) | €0 extra |
| Base de datos | Supabase (PostgreSQL) | €0 free tier |
| Frontend | Astro + Tailwind | €0 |
| Hosting | Vercel | €0 |
| Newsletter | Brevo | €0 free tier |
| Scheduler | Windows Task Scheduler | €0 |
| **Total** | | **~€0-5/mes** |

## Configuración inicial

### 1. Clonar y configurar entorno

```bash
git clone https://github.com/esemperena/actacivium.git
cd actacivium
cp .env.example .env
# editar .env con tus credenciales
```

### 2. Supabase

1. Crear proyecto en [supabase.com](https://supabase.com)
2. Ejecutar `database/schema.sql` en el SQL Editor
3. Copiar URL y claves al `.env`

### 3. Instalar dependencias del scraper

```bash
cd scraper
python -m pip install -r requirements.txt
```

### 4. Probar el scraper (dry-run)

```bash
cd scraper
python run.py --dry-run
```

Esto muestra las actas disponibles en donostia.eus sin insertar nada en la BD.

### 5. Primer scraping completo

```bash
python run.py
```

### 6. Frontend local

```bash
cd web
npm install
npm run dev
```

### 7. Configurar Windows Task Scheduler

Crear una tarea que ejecute semanalmente:
```
python C:\ruta\al\proyecto\actacivium\scraper\run.py
```

## Comandos útiles

```bash
# Scraper
python run.py                    # procesar actas nuevas
python run.py --dry-run          # solo listar, no procesar
python run.py --reprocess 39     # reprocesar el acta nº 39

# Newsletter
python newsletter/send_newsletter.py --pleno-id <uuid> --test tu@email.com
python newsletter/send_newsletter.py --pleno-id <uuid>  # envío real
```

## Añadir un nuevo municipio

1. Insertar en la tabla `municipios` con su URL de actas
2. Crear `scraper/<municipio>.py` extendiendo el patrón de `donostia.py`
3. Añadir el municipio al listado en `scraper/run.py`

## Licencia

Código: MIT · Datos: CC BY 4.0 (fuente: Ayuntamiento de San Sebastián / donostia.eus)
