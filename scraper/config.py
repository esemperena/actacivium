import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

# Directorio temporal para PDFs descargados antes de procesarlos
PDF_TEMP_DIR = os.environ.get("PDF_TEMP_DIR", "/tmp/actacivium_pdfs")

# Número máximo de páginas a extraer del PDF para el resumen IA
# Las actas pueden tener 200+ páginas; limitamos para no saturar el contexto de Claude
PDF_MAX_PAGES_FOR_SUMMARY = int(os.environ.get("PDF_MAX_PAGES_FOR_SUMMARY", "60"))

# Comando claude CLI (Claude Code instalado en el sistema)
CLAUDE_CMD = os.environ.get("CLAUDE_CMD", "claude")

# Nivel mínimo de relevancia social para incluir en la newsletter (1-5)
NEWSLETTER_MIN_RELEVANCIA = int(os.environ.get("NEWSLETTER_MIN_RELEVANCIA", "3"))
