import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import discord
from discord.ext import commands

# Mini servidor web robusto para Render
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot de Faccion Activo")
    
    # Evita que los logs de Render se llenen de errores de peticiones vacías
    def log_message(self, format, *args):
        return

def iniciar_web():
    puerto = int(os.environ.get("PORT", 10000))
    servidor = HTTPServer(("0.0.0.0", puerto), Handler)
    print(f"Servidor web escuchando en el puerto {puerto}")
    servidor.serve_forever()

# Arrancamos el servidor web antes de iniciar Discord
hilo_web = threading.Thread(target=iniciar_web, daemon=True)
hilo_web.start()

# Configuración del Bot de Discord
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"¡Bot conectado con éxito como {bot.user}!")

@bot.command(name="miembros")
async def miembros(ctx):
    lista_faccion = (
        "**--- LISTA DE MIEMBROS DE LA FACCIÓN ---**\n"
        "1. [Líder] Zadriansi - En Servicio\n"
        "2. [Oficial] Oficial_01 - Activo\n"
        "3. [Oficial] Oficial_02 - Activo\n"
        "\n*Total de oficiales en servicio: 3*"
    )
    await ctx.send(lista_faccion)

TOKEN = os.getenv("TOKEN_BOT")

if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: No se encontró la variable de entorno TOKEN_BOT.")
