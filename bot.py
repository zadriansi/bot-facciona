import os
import discord
from discord import app_commands
import sqlite3
import re

# =========================================================================
# CONFIGURACIÓN DEL TOKEN Y CANAL
# El Token se lee de forma segura desde las variables de entorno de Render/Sistema.
# (Si lo ejecutas localmente en tu PC para pruebas, puedes poner tu token entre comillas aquí temporalmente).
# =========================================================================
TOKEN_BOT = os.getenv("TOKEN_BOT") or "PEGA_AQUI_TU_TOKEN_SI_PRUEBAS_LOCAL"
ID_CANAL_REPORTES = 1557518224067793048  # <--- REEMPLAZA ESTE NÚMERO POR EL ID REAL DE TU CANAL DE DISCORD

class FaccionBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"Bot encendido y listo como: {self.user}")

client = FaccionBot()

def inicializar_bd():
    conexion = sqlite3.connect("faccion.db")
    cursor = conexion.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS miembros (
            nombre TEXT PRIMARY KEY,
            rango_texto TEXT,
            rango_num INTEGER,
            ult_vez TEXT,
            stats TEXT
        )
    """)
    conexion.commit()
    conexion.close()

inicializar_bd()

@client.event
async def on_message(message):
    if message.channel.id == ID_CANAL_REPORTES and message.webhook_id and message.attachments:
        for adjunto in message.attachments:
            if adjunto.filename == "Reporte_Faccion.txt":
                contenido = (await adjunto.read()).decode("latin-1", errors="ignore")
                
                conexion = sqlite3.connect("faccion.db")
                cursor = conexion.cursor()
                cursor.execute("DELETE FROM miembros")
                
                contador = 0
                for linea in contenido.splitlines():
                    if "|" in linea and not linea.startswith("NOMBRE") and not linea.startswith("Generado"):
                        partes = [p.strip() for p in linea.split("|")]
                        if len(partes) >= 4:
                            nombre = partes[0]
                            rango_texto = partes[1]
                            ult_vez = partes[2]
                            stats = " | ".join(partes[3:])
                            
                            match_rango = re.search(r"\((\d+)\)", rango_texto)
                            rango_num = int(match_rango.group(1)) if match_rango else 0
                            
                            cursor.execute("INSERT OR REPLACE INTO miembros VALUES (?, ?, ?, ?, ?)",
                                           (nombre, rango_texto, rango_num, ult_vez, stats))
                            contador += 1
                            
                conexion.commit()
                conexion.close()
                await message.channel.send(f"🤖 **Base de datos actualizada:** Se indexaron **{contador} miembros** correctamente.")

@client.tree.command(name="buscar", description="Consulta el rango, última conexión y eventos de un miembro")
@app_commands.describe(nombre="Nombre del jugador (ej: Addel_Fullmer)")
async def buscar(interaction: discord.Interaction, nombre: str):
    conexion = sqlite3.connect("faccion.db")
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM miembros WHERE nombre LIKE ?", (f"%{nombre}%",))
    res = cursor.fetchone()
    conexion.close()
    
    if not res:
        await interaction.response.send_message(f"❌ No encontré a nadie llamado `{nombre}` en el último reporte.", ephemeral=True)
        return
        
    embed = discord.Embed(title=f"📋 Ficha de {res[0]}", color=discord.Color.green())
    embed.add_field(name="Rango", value=res[1], inline=True)
    embed.add_field(name="Última Conexión", value=res[3], inline=True)
    embed.add_field(name="Actividad (Conq / Air / Graf)", value=res[4], inline=False)
    await interaction.response.send_message(embed=embed)

@client.tree.command(name="top_rangos", description="Muestra los 20 miembros con mayor rango de la facción")
async def top_rangos(interaction: discord.Interaction):
    conexion = sqlite3.connect("faccion.db")
    cursor = conexion.cursor()
    cursor.execute("SELECT nombre, rango_texto, ult_vez, stats FROM miembros ORDER BY rango_num DESC LIMIT 20")
    resultados = cursor.fetchall()
    conexion.close()
    
    if not resultados:
        await interaction.response.send_message("❌ Aún no se ha subido ningún reporte al canal.", ephemeral=True)
        return
        
    texto = ""
    for m in resultados:
        texto += f"**{m[0]}** — `{m[1]}` | Últ: `{m[2]}` | Stats: `{m[3]}`\n"
        
    embed = discord.Embed(title="👑 Altos Mandos de la Facción (Top 20)", description=texto, color=discord.Color.gold())
    await interaction.response.send_message(embed=embed)

@client.tree.command(name="inactivos", description="Muestra los miembros desconectados hace más tiempo")
async def inactivos(interaction: discord.Interaction):
    conexion = sqlite3.connect("faccion.db")
    cursor = conexion.cursor()
    cursor.execute("SELECT nombre, rango_texto, ult_vez FROM miembros WHERE ult_vez NOT LIKE 'ID:%' ORDER BY ult_vez ASC LIMIT 25")
    resultados = cursor.fetchall()
    conexion.close()
    
    if not resultados:
        await interaction.response.send_message("✅ Todos los miembros están conectados o no hay datos.", ephemeral=True)
        return
        
    texto = ""
    for m in resultados:
        texto += f"• **{m[0]}** ({m[1]}) — Última vez: `{m[2]}`\n"
        
    embed = discord.Embed(title="⚠️ Miembros con mayor tiempo desconectados", description=texto, color=discord.Color.red())
    await interaction.response.send_message(embed=embed)

@client.tree.command(name="miembros", description="Muestra la lista completa de la facción ordenada por rango (25 por página)")
@app_commands.describe(pagina="Número de página (1 = puestos 1-25, 2 = 26-50, etc.)")
async def miembros(interaction: discord.Interaction, pagina: int = 1):
    if pagina < 1:
        pagina = 1
        
    por_pagina = 25
    offset = (pagina - 1) * por_pagina
    
    conexion = sqlite3.connect("faccion.db")
    cursor = conexion.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM miembros")
    total_miembros = cursor.fetchone()[0]
    
    if total_miembros == 0:
        conexion.close()
        await interaction.response.send_message("❌ Aún no hay datos cargados. Usa `/exportar` en el juego primero.", ephemeral=True)
        return

    cursor.execute("""
        SELECT nombre, rango_texto, ult_vez, stats 
        FROM miembros 
        ORDER BY rango_num DESC, nombre ASC 
        LIMIT ? OFFSET ?
    """, (por_pagina, offset))
    resultados = cursor.fetchall()
    conexion.close()
    
    total_paginas = (total_miembros + por_pagina - 1) // por_pagina
    
    if not resultados:
        await interaction.response.send_message(f"❌ La página **{pagina}** está vacía. Solo hay **{total_paginas}** páginas disponibles.", ephemeral=True)
        return

    texto = ""
    for i, m in enumerate(resultados, start=offset + 1):
        estado = "🟢" if "ID:" in m[2] else "⚫"
        texto += f"`#{i:02d}` {estado} **{m[0]}** | `{m[1]}`\n      └ Últ: `{m[2]}` • Stats: `{m[3]}`\n"

    embed = discord.Embed(
        title=f"📋 Lista de Miembros — Página {pagina} de {total_paginas}",
        description=texto,
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"Total en facción: {total_miembros} miembros | Usa /miembros pagina:2 para ver más")
    
    await interaction.response.send_message(embed=embed)

# Arrancar el bot con el token seguro
if TOKEN_BOT:
    client.run(TOKEN_BOT)
else:
    print("❌ ERROR CRÍTICO: No se encontró el TOKEN_BOT en las variables de entorno.")