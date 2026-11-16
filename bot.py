import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import discord
from discord.ext import commands

# 1. Mini servidor web para satisfacer el requisito de puertos de Render
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot de Faccion Activo")

def iniciar_web():
    puerto = int(os.environ.get("PORT", 8080))
    servidor = HTTPServer(("0.0.0.0", puerto), Handler)
    servidor.serve_forever()

# Arrancamos el servidor web en segundo plano
threading.Thread(target=iniciar_web, daemon=True).start()

# 2. Configuración del Bot de Discord
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Definimos el prefijo de los comandos
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"¡Bot conectado con éxito como {bot.user}!")

# 3. Comando /miembros (responde en el mismo canal donde se escriba)
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

# 4. Ejecución segura usando la variable de entorno de Render
TOKEN = os.getenv("TOKEN_BOT")

if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: No se encontró la variable de entorno TOKEN_BOT.")
