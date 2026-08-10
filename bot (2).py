import discord
from discord.ext import commands, tasks
import threading
import asyncio
import time
import os
import sys
import subprocess
import json
from dotenv import load_dotenv
 
load_dotenv()
 
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
 
bot = commands.Bot(command_prefix="$", intents=intents)
 
canais_auto_limpeza = set()
CANAL_ANUNCIO_ID = 1536176747446538341
CARGO_ALERTA_ID = 1536176715108458616
encerrar_bot = False
reiniciar_bot = False
CAMINHO_BACKUP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backup_servidor.json")
 
CARGOS_DISPONIVEIS = {
    1: 1536176701417984001,  # The father
    2: 1536176702940516392,  # The son
    3: 1536176703712530505, # The holy spirit
    4: 1536176706979766302, # The holy ghost
    5: 1536176707999113237, # The factore 
    6: 1536176709999657081, # Children of Justice
}
 
@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")
    if not limpeza_automatica.is_running():
        limpeza_automatica.start()
    threading.Thread(target=escutar_terminal, daemon=True).start()
 
# ---------- COMANDO $clear ----------
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, quantidade: int = 10):
    """Apaga uma quantidade de mensagens do canal. Ex: $clear 20"""
    if quantidade < 1 or quantidade > 100:
        await ctx.send("Escolha um número entre 1 e 100.", delete_after=5)
        return
    apagadas = await ctx.channel.purge(limit=quantidade + 1)
    msg = await ctx.send(f"🧹 {len(apagadas) - 1} mensagens apagadas.")
    await msg.delete(delay=3)
 
@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Você precisa da permissão 'Gerenciar Mensagens' pra usar esse comando.", delete_after=5)
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Use um número válido. Ex: $clear 20", delete_after=5)
 
# ---------- LIGAR/DESLIGAR LIMPEZA AUTOMÁTICA ----------
@bot.command()
@commands.has_permissions(manage_messages=True)
async def autoclear(ctx, estado: str):
    """Liga ou desliga a limpeza automática (a cada 10 minutos) neste canal."""
    if estado.lower() == "on":
        canais_auto_limpeza.add(ctx.channel.id)
        await ctx.send("✅ Limpeza automática ativada neste canal (a cada 10 minutos).")
    elif estado.lower() == "off":
        canais_auto_limpeza.discard(ctx.channel.id)
        await ctx.send("🛑 Limpeza automática desativada neste canal.")
    else:
        await ctx.send("Use: `$autoclear on` ou `$autoclear off`")
 
# ---------- COMANDO $admin (atribuir cargos) ----------
@bot.group(invoke_without_command=True)
@commands.has_permissions(administrator=True)
async def admin(ctx, user_id: int = None, opcao: int = None):
    """
    Uso:
    $admin listar            -> mostra a lista de cargos disponíveis
    $admin <id_usuario> <n>  -> dá o cargo da opção "n" para o usuário
    """
    if user_id is None or opcao is None:
        await ctx.send("Use: `$admin listar` para ver as opções, ou `$admin <id_usuario> <numero>` para aplicar um cargo.")
        return
 
    if opcao not in CARGOS_DISPONIVEIS:
        await ctx.send("Opção inválida. Use `$admin listar` para ver as opções disponíveis.")
        return
 
    try:
        membro = await ctx.guild.fetch_member(user_id)
    except discord.NotFound:
        await ctx.send("Usuário não encontrado neste servidor. Confira o ID.")
        return
 
    cargo = ctx.guild.get_role(CARGOS_DISPONIVEIS[opcao])
    if cargo is None:
        await ctx.send("Esse cargo não existe mais neste servidor.")
        return
 
    if cargo >= ctx.guild.me.top_role:
        await ctx.send(f"❌ Não tenho permissão para atribuir o cargo **{cargo.name}** (ele está acima ou igual ao meu cargo mais alto).")
        return
 
    try:
        await membro.add_roles(cargo)
        await ctx.send(f"✅ Cargo **{cargo.name}** adicionado para {membro.mention}.")
    except discord.Forbidden:
        await ctx.send(f"❌ Sem permissão para atribuir o cargo **{cargo.name}**.")
 
@admin.command(name="listar")
@commands.has_permissions(administrator=True)
async def admin_listar(ctx):
    """Mostra os cargos disponíveis e se o bot pode atribuí-los."""
    linhas = ["**Cargos disponíveis:**\n"]
    for numero, cargo_id in CARGOS_DISPONIVEIS.items():
        cargo = ctx.guild.get_role(cargo_id)
        if cargo is None:
            linhas.append(f"`{numero}` — (cargo não encontrado no servidor) ❌")
            continue
        pode_atribuir = cargo < ctx.guild.me.top_role
        status = "✅" if pode_atribuir else "❌"
        linhas.append(f"`{numero}` — {cargo.name} {status}")
 
    linhas.append("\nUso: `$admin <id_usuario> <numero>`")
    await ctx.send("\n".join(linhas))
 
@admin.error
async def admin_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Você precisa ser administrador para usar esse comando.", delete_after=5)
 
# ---------- COMANDO $userinfo ----------
@bot.command()
async def userinfo(ctx, user_id: int = None):
    """Mostra informações de um usuário. Ex: $userinfo 123456789012345678"""
    if user_id is None:
        membro = ctx.author
    else:
        try:
            membro = await ctx.guild.fetch_member(user_id)
        except discord.NotFound:
            await ctx.send("Usuário não encontrado neste servidor. Confira o ID.")
            return
 
    cargos = [cargo.mention for cargo in membro.roles if cargo.name != "@everyone"]
    cargos_texto = ", ".join(cargos) if cargos else "Nenhum"
 
    embed = discord.Embed(
        title=f"Informações de {membro}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=membro.display_avatar.url)
    embed.add_field(name="ID", value=membro.id, inline=False)
    embed.add_field(name="Conta criada em", value=membro.created_at.strftime("%d/%m/%Y %H:%M"), inline=True)
    embed.add_field(name="Entrou no servidor em", value=membro.joined_at.strftime("%d/%m/%Y %H:%M") if membro.joined_at else "Desconhecido", inline=True)
    embed.add_field(name=f"Cargos ({len(cargos)})", value=cargos_texto, inline=False)
    embed.add_field(name="Bot?", value="Sim" if membro.bot else "Não", inline=True)
 
    await ctx.send(embed=embed)
 
@userinfo.error
async def userinfo_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send("Use um ID válido. Ex: `$userinfo 123456789012345678`", delete_after=5)
 
# ---------- COMANDO $kick ----------
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, user_id: int, *, motivo: str = "Não especificado"):
    """Expulsa um usuário do servidor. Ex: $kick 123456789012345678 spam"""
    try:
        membro = await ctx.guild.fetch_member(user_id)
    except discord.NotFound:
        await ctx.send("Usuário não encontrado neste servidor. Confira o ID.")
        return
 
    if membro.top_role >= ctx.guild.me.top_role:
        await ctx.send(f"❌ Não posso expulsar {membro.mention} (cargo dele é igual ou maior que o meu).")
        return
 
    try:
        await membro.kick(reason=f"Por {ctx.author}: {motivo}")
        await ctx.send(f"👢 {membro} foi expulso. Motivo: {motivo}")
    except discord.Forbidden:
        await ctx.send("❌ Sem permissão para expulsar este usuário.")
 
@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Você precisa da permissão 'Expulsar Membros' pra usar esse comando.", delete_after=5)
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Use: `$kick <id_usuario> [motivo]`", delete_after=5)
 
# ---------- COMANDO $ban ----------
@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, user_id: int, *, motivo: str = "Não especificado"):
    """Bane um usuário do servidor. Ex: $ban 123456789012345678 raid"""
    try:
        membro = await ctx.guild.fetch_member(user_id)
        if membro.top_role >= ctx.guild.me.top_role:
            await ctx.send(f"❌ Não posso banir {membro.mention} (cargo dele é igual ou maior que o meu).")
            return
    except discord.NotFound:
        pass  # usuário pode não estar mais no servidor mas ainda dá pra banir pelo ID
 
    try:
        await ctx.guild.ban(discord.Object(id=user_id), reason=f"Por {ctx.author}: {motivo}")
        await ctx.send(f"🔨 Usuário `{user_id}` foi banido. Motivo: {motivo}")
    except discord.Forbidden:
        await ctx.send("❌ Sem permissão para banir este usuário.")
    except discord.NotFound:
        await ctx.send("Usuário não encontrado. Confira o ID.")
 
@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Você precisa da permissão 'Banir Membros' pra usar esse comando.", delete_after=5)
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Use: `$ban <id_usuario> [motivo]`", delete_after=5)
 
# ---------- COMANDO $unban ----------
@bot.command()
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int):
    """Remove o banimento de um usuário. Ex: $unban 123456789012345678"""
    try:
        await ctx.guild.unban(discord.Object(id=user_id))
        await ctx.send(f"✅ Usuário `{user_id}` foi desbanido.")
    except discord.NotFound:
        await ctx.send("Esse usuário não está banido.")
    except discord.Forbidden:
        await ctx.send("❌ Sem permissão para desbanir usuários.")
 
@unban.error
async def unban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Você precisa da permissão 'Banir Membros' pra usar esse comando.", delete_after=5)
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Use: `$unban <id_usuario>`", delete_after=5)
 
# ---------- COMANDO $serverinfo ----------
@bot.command()
async def serverinfo(ctx):
    """Mostra estatísticas do servidor."""
    guild = ctx.guild
 
    total_membros = guild.member_count
    total_bots = sum(1 for m in guild.members if m.bot)
    total_humanos = total_membros - total_bots
 
    total_canais_texto = len(guild.text_channels)
    total_canais_voz = len(guild.voice_channels)
    total_cargos = len(guild.roles)
 
    embed = discord.Embed(
        title=f"Informações de {guild.name}",
        color=discord.Color.green()
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="ID do servidor", value=guild.id, inline=False)
    embed.add_field(name="Dono", value=guild.owner.mention if guild.owner else "Desconhecido", inline=True)
    embed.add_field(name="Criado em", value=guild.created_at.strftime("%d/%m/%Y %H:%M"), inline=True)
    embed.add_field(name="Membros", value=f"{total_membros} (👤 {total_humanos} / 🤖 {total_bots})", inline=False)
    embed.add_field(name="Canais de texto", value=total_canais_texto, inline=True)
    embed.add_field(name="Canais de voz", value=total_canais_voz, inline=True)
    embed.add_field(name="Cargos", value=total_cargos, inline=True)
    embed.add_field(name="Nível de boost", value=f"Nível {guild.premium_tier} ({guild.premium_subscription_count} boosts)", inline=False)
 
    await ctx.send(embed=embed)
 
# ---------- COMANDO $logo ----------
@bot.command()
async def logo(ctx):
    """Envia a logo estilo matrix do servidor."""
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo_matrix.png")
    try:
        await ctx.send(file=discord.File(caminho))
    except FileNotFoundError:
        await ctx.send("Arquivo da logo não encontrado. Confira se `logo_matrix.png` está na pasta do bot.")
 
@tasks.loop(minutes=10)
async def limpeza_automatica():
    for canal_id in list(canais_auto_limpeza):
        canal = bot.get_channel(canal_id)
        if canal is None:
            continue
        try:
            apagadas = await canal.purge(limit=100)
            print(f"[{canal.name}] {len(apagadas)} mensagens apagadas automaticamente.")
        except discord.Forbidden:
            print(f"Sem permissão para limpar #{canal.name}")
        except discord.HTTPException as e:
            print(f"Erro ao limpar #{canal.name}: {e}")
 
# ---------- ANÚNCIO PELO TERMINAL ----------
def enviar_anuncio(texto):
    canal = bot.get_channel(CANAL_ANUNCIO_ID)
    if canal is None:
        print("Canal não encontrado — confira o CANAL_ANUNCIO_ID.")
        return
    mensagem = f"📢 **Anúncio:** {texto}\n<@&{CARGO_ALERTA_ID}>"
    asyncio.run_coroutine_threadsafe(
        canal.send(mensagem),
        bot.loop
    )
    print("Anúncio enviado!")
 
def admin_listar_terminal():
    guild = bot.guilds[0] if bot.guilds else None  # usa o primeiro servidor que o bot está
    if guild is None:
        print("Bot não está em nenhum servidor.")
        return
    print("\n--- Cargos disponíveis ---")
    for numero, cargo_id in CARGOS_DISPONIVEIS.items():
        cargo = guild.get_role(cargo_id)
        if cargo is None:
            print(f"{numero} — (cargo não encontrado) ❌")
            continue
        pode_atribuir = cargo < guild.me.top_role
        status = "✅" if pode_atribuir else "❌"
        print(f"{numero} — {cargo.name} {status}")
    print("--------------------------\n")
 
def admin_atribuir_terminal(user_id, opcao):
    guild = bot.guilds[0] if bot.guilds else None
    if guild is None:
        print("Bot não está em nenhum servidor.")
        return
 
    if opcao not in CARGOS_DISPONIVEIS:
        print("Opção inválida.")
        return
 
    cargo = guild.get_role(CARGOS_DISPONIVEIS[opcao])
    if cargo is None:
        print("Esse cargo não existe mais neste servidor.")
        return
 
    if cargo >= guild.me.top_role:
        print(f"❌ Não tenho permissão para atribuir o cargo {cargo.name} (hierarquia).")
        return
 
    async def atribuir():
        try:
            membro = await guild.fetch_member(user_id)
        except discord.NotFound:
            print("Usuário não encontrado neste servidor. Confira o ID.")
            return
        try:
            await membro.add_roles(cargo)
            print(f"✅ Cargo {cargo.name} adicionado para {membro}.")
        except discord.Forbidden:
            print(f"❌ Sem permissão para atribuir o cargo {cargo.name}.")
 
    asyncio.run_coroutine_threadsafe(atribuir(), bot.loop)
 
def userinfo_terminal(user_id):
    guild = bot.guilds[0] if bot.guilds else None
    if guild is None:
        print("Bot não está em nenhum servidor.")
        return
 
    async def buscar():
        try:
            membro = await guild.fetch_member(user_id)
        except discord.NotFound:
            print("Usuário não encontrado neste servidor. Confira o ID.")
            return
 
        cargos = [cargo.name for cargo in membro.roles if cargo.name != "@everyone"]
        cargos_texto = ", ".join(cargos) if cargos else "Nenhum"
 
        print(f"""
--- Informações de {membro} ---
ID: {membro.id}
Conta criada em: {membro.created_at.strftime('%d/%m/%Y %H:%M')}
Entrou no servidor em: {membro.joined_at.strftime('%d/%m/%Y %H:%M') if membro.joined_at else 'Desconhecido'}
Cargos ({len(cargos)}): {cargos_texto}
Bot?: {'Sim' if membro.bot else 'Não'}
--------------------------------
""")
 
    asyncio.run_coroutine_threadsafe(buscar(), bot.loop)
 
def serverinfo_terminal():
    guild = bot.guilds[0] if bot.guilds else None
    if guild is None:
        print("Bot não está em nenhum servidor.")
        return
 
    total_membros = guild.member_count
    total_bots = sum(1 for m in guild.members if m.bot)
    total_humanos = total_membros - total_bots
 
    print(f"""
--- Informações de {guild.name} ---
ID do servidor: {guild.id}
Dono: {guild.owner if guild.owner else 'Desconhecido'}
Criado em: {guild.created_at.strftime('%d/%m/%Y %H:%M')}
Membros: {total_membros} (Humanos: {total_humanos} / Bots: {total_bots})
Canais de texto: {len(guild.text_channels)}
Canais de voz: {len(guild.voice_channels)}
Cargos: {len(guild.roles)}
Nível de boost: Nível {guild.premium_tier} ({guild.premium_subscription_count} boosts)
--------------------------------
""")
 
def kick_terminal(user_id, motivo="Não especificado"):
    guild = bot.guilds[0] if bot.guilds else None
    if guild is None:
        print("Bot não está em nenhum servidor.")
        return
 
    async def executar():
        try:
            membro = await guild.fetch_member(user_id)
        except discord.NotFound:
            print("Usuário não encontrado neste servidor. Confira o ID.")
            return
 
        if membro.top_role >= guild.me.top_role:
            print(f"❌ Não posso expulsar {membro} (cargo dele é igual ou maior que o meu).")
            return
 
        try:
            await membro.kick(reason=f"Via terminal: {motivo}")
            print(f"👢 {membro} foi expulso. Motivo: {motivo}")
        except discord.Forbidden:
            print("❌ Sem permissão para expulsar este usuário.")
 
    asyncio.run_coroutine_threadsafe(executar(), bot.loop)
 
def ban_terminal(user_id, motivo="Não especificado"):
    guild = bot.guilds[0] if bot.guilds else None
    if guild is None:
        print("Bot não está em nenhum servidor.")
        return
 
    async def executar():
        try:
            membro = await guild.fetch_member(user_id)
            if membro.top_role >= guild.me.top_role:
                print(f"❌ Não posso banir {membro} (cargo dele é igual ou maior que o meu).")
                return
        except discord.NotFound:
            pass
 
        try:
            await guild.ban(discord.Object(id=user_id), reason=f"Via terminal: {motivo}")
            print(f"🔨 Usuário {user_id} foi banido. Motivo: {motivo}")
        except discord.Forbidden:
            print("❌ Sem permissão para banir este usuário.")
        except discord.NotFound:
            print("Usuário não encontrado. Confira o ID.")
 
    asyncio.run_coroutine_threadsafe(executar(), bot.loop)
 
def unban_terminal(user_id):
    guild = bot.guilds[0] if bot.guilds else None
    if guild is None:
        print("Bot não está em nenhum servidor.")
        return
 
    async def executar():
        try:
            await guild.unban(discord.Object(id=user_id))
            print(f"✅ Usuário {user_id} foi desbanido.")
        except discord.NotFound:
            print("Esse usuário não está banido.")
        except discord.Forbidden:
            print("❌ Sem permissão para desbanir usuários.")
 
    asyncio.run_coroutine_threadsafe(executar(), bot.loop)
 
# ---------- BACKUP E NUKE DO SERVIDOR (SÓ TERMINAL) ----------
def overwrite_para_dict(ow: discord.PermissionOverwrite) -> dict:
    allow, deny = ow.pair()
    return {"allow": allow.value, "deny": deny.value}
 
def dict_para_overwrite(d: dict) -> discord.PermissionOverwrite:
    ow = discord.PermissionOverwrite()
    allow = discord.Permissions(d["allow"])
    deny = discord.Permissions(d["deny"])
    for nome, valor in allow:
        if valor:
            setattr(ow, nome, True)
    for nome, valor in deny:
        if valor:
            setattr(ow, nome, False)
    return ow
 
async def montar_backup(guild):
    backup = {
        "nome_servidor": guild.name,
        "roles": [],
        "categorias": [],
        "canais": [],
    }
 
    for role in guild.roles:
        if role.name == "@everyone" or role.managed:
            continue
        backup["roles"].append({
            "nome": role.name,
            "cor": role.color.value,
            "permissoes": role.permissions.value,
            "hoist": role.hoist,
            "mentionable": role.mentionable,
            "posicao": role.position,
        })
 
    for cat in guild.categories:
        overwrites = {}
        for alvo, ow in cat.overwrites.items():
            if isinstance(alvo, discord.Role):
                overwrites[alvo.name] = overwrite_para_dict(ow)
        backup["categorias"].append({
            "nome": cat.name,
            "posicao": cat.position,
            "overwrites": overwrites,
        })
 
    for canal in guild.channels:
        if isinstance(canal, discord.CategoryChannel):
            continue
        if isinstance(canal, discord.TextChannel):
            tipo = "texto"
        elif isinstance(canal, discord.VoiceChannel):
            tipo = "voz"
        else:
            continue  # ignora tipos não suportados (forum, stage, etc.)
 
        overwrites = {}
        for alvo, ow in canal.overwrites.items():
            if isinstance(alvo, discord.Role):
                overwrites[alvo.name] = overwrite_para_dict(ow)
 
        backup["canais"].append({
            "nome": canal.name,
            "tipo": tipo,
            "categoria": canal.category.name if canal.category else None,
            "posicao": canal.position,
            "topico": getattr(canal, "topic", None),
            "overwrites": overwrites,
        })
 
    return backup
 
def backup_terminal():
    guild = bot.guilds[0] if bot.guilds else None
    if guild is None:
        print("Bot não está em nenhum servidor.")
        return
 
    async def executar():
        backup = await montar_backup(guild)
        with open(CAMINHO_BACKUP, "w", encoding="utf-8") as f:
            json.dump(backup, f, ensure_ascii=False, indent=2)
        print(f"✅ Backup salvo em {CAMINHO_BACKUP}")
        print(f"   {len(backup['roles'])} cargos, {len(backup['categorias'])} categorias, {len(backup['canais'])} canais.")
 
    asyncio.run_coroutine_threadsafe(executar(), bot.loop)
 
async def executar_nuke(guild, backup):
    print("💣 Apagando canais...")
    for canal in list(guild.channels):
        try:
            await canal.delete()
        except Exception as e:
            print(f"   Erro ao apagar canal {canal.name}: {e}")
 
    print("💣 Apagando cargos...")
    for role in list(guild.roles):
        if role.name == "@everyone" or role.managed:
            continue
        try:
            await role.delete()
        except Exception as e:
            print(f"   Erro ao apagar cargo {role.name}: {e}")
 
    print("🔨 Recriando cargos...")
    role_map = {}
    for role_data in sorted(backup["roles"], key=lambda r: r["posicao"]):
        try:
            novo = await guild.create_role(
                name=role_data["nome"],
                colour=discord.Color(role_data["cor"]),
                permissions=discord.Permissions(role_data["permissoes"]),
                hoist=role_data["hoist"],
                mentionable=role_data["mentionable"],
            )
            role_map[role_data["nome"]] = novo
        except Exception as e:
            print(f"   Erro ao criar cargo {role_data['nome']}: {e}")
 
    print("🔨 Recriando categorias...")
    cat_map = {}
    for cat_data in sorted(backup["categorias"], key=lambda c: c["posicao"]):
        overwrites = {}
        for nome_cargo, ow_data in cat_data["overwrites"].items():
            cargo = role_map.get(nome_cargo)
            if cargo:
                overwrites[cargo] = dict_para_overwrite(ow_data)
        try:
            nova = await guild.create_category(cat_data["nome"], overwrites=overwrites)
            cat_map[cat_data["nome"]] = nova
        except Exception as e:
            print(f"   Erro ao criar categoria {cat_data['nome']}: {e}")
 
    print("🔨 Recriando canais...")
    for canal_data in sorted(backup["canais"], key=lambda c: c["posicao"]):
        overwrites = {}
        for nome_cargo, ow_data in canal_data["overwrites"].items():
            cargo = role_map.get(nome_cargo)
            if cargo:
                overwrites[cargo] = dict_para_overwrite(ow_data)
        categoria = cat_map.get(canal_data["categoria"]) if canal_data["categoria"] else None
        try:
            if canal_data["tipo"] == "texto":
                await guild.create_text_channel(
                    canal_data["nome"], category=categoria,
                    topic=canal_data["topico"], overwrites=overwrites,
                )
            elif canal_data["tipo"] == "voz":
                await guild.create_voice_channel(
                    canal_data["nome"], category=categoria, overwrites=overwrites,
                )
        except Exception as e:
            print(f"   Erro ao criar canal {canal_data['nome']}: {e}")
 
    print("✅ Reconstrução concluída. Confira as posições dos cargos/canais — a ordem exata pode precisar de ajuste manual.")
 
def nuke_terminal():
    guild = bot.guilds[0] if bot.guilds else None
    if guild is None:
        print("Bot não está em nenhum servidor.")
        return
 
    if not os.path.exists(CAMINHO_BACKUP):
        print("❌ Nenhum backup encontrado. Rode `!backup` antes de usar `!nuke`.")
        return
 
    with open(CAMINHO_BACKUP, "r", encoding="utf-8") as f:
        backup = json.load(f)
 
    print("⚠️  ATENÇÃO: isso vai APAGAR TODOS os canais e cargos do servidor")
    print(f"   e reconstruir com base no backup salvo em {CAMINHO_BACKUP}")
    print(f"   (backup do servidor '{backup['nome_servidor']}', {len(backup['roles'])} cargos, {len(backup['canais'])} canais).")
    print("   Isso NÃO pode ser desfeito.")
 
    confirm1 = input(f"Digite o nome do servidor ({guild.name}) para confirmar: ")
    if confirm1 != guild.name:
        print("Nome não confere. Operação cancelada.")
        return
 
    confirm2 = input("Digite CONFIRMAR NUKE para prosseguir: ")
    if confirm2 != "CONFIRMAR NUKE":
        print("Confirmação inválida. Operação cancelada.")
        return
 
    print("💣 Iniciando nuke e reconstrução...")
    asyncio.run_coroutine_threadsafe(executar_nuke(guild, backup), bot.loop)
 
def stop_terminal():
    global encerrar_bot
    encerrar_bot = True
    print("🛑 Encerrando o bot...")
    asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)
 
def restart_terminal():
    global reiniciar_bot
    reiniciar_bot = True
    print("🔄 Reiniciando o bot...")
    asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)
 
def mostrar_ajuda():
    print("""
==================== COMANDOS DISPONÍVEIS ====================
 
--- Terminal (aqui no VS Code) ---
!anuncio   -> Envia um anúncio no canal configurado, marcando o cargo de alerta
!help      -> Mostra esta lista de comandos
!admin listar         -> Mostra os cargos disponíveis (com ✅/❌ de permissão)
!admin <id_usuario> <numero> -> Atribui o cargo da opção escolhida ao usuário
!userinfo <id_usuario> -> Mostra informações de um usuário
!serverinfo            -> Mostra estatísticas do servidor
!kick <id_usuario> [motivo]  -> Expulsa um usuário do servidor
!ban <id_usuario> [motivo]   -> Bane um usuário do servidor
!unban <id_usuario>          -> Remove o banimento de um usuário
!backup                      -> Salva cargos, categorias e canais em backup_servidor.json
!nuke                        -> Apaga TUDO (canais e cargos) e reconstrói a partir do backup
                                 (pede confirmação dupla no terminal antes de rodar)
!stop                        -> Encerra o bot completamente
!restart                     -> Reinicia o bot do zero
 
--- Discord (digitados no chat do servidor) ---
$clear <quantidade>   -> Apaga mensagens do canal (padrão: 10, máx: 100)
                          Ex: $clear 20
$autoclear on/off     -> Liga ou desliga a limpeza automática (a cada 10 minutos)
                          neste canal
$admin listar         -> Mostra os cargos disponíveis (com ✅/❌ de permissão)
$admin <id_usuario> <numero> -> Atribui o cargo da opção escolhida ao usuário
$userinfo <id_usuario> -> Mostra informações de um usuário (ou seu próprio, sem ID)
$serverinfo            -> Mostra estatísticas do servidor
$kick <id_usuario> [motivo]  -> Expulsa um usuário do servidor
$ban <id_usuario> [motivo]   -> Bane um usuário do servidor
$unban <id_usuario>          -> Remove o banimento de um usuário
$logo                        -> Envia a logo estilo matrix
 
================================================================
""")
 
def escutar_terminal():
    while True:
        comando = input()
        comando = comando.strip()
 
        if comando == "!anuncio":
            texto = input("Digite a mensagem do anúncio: ")
            enviar_anuncio(texto)
 
        elif comando == "!help":
            mostrar_ajuda()
 
        elif comando == "!admin listar":
            admin_listar_terminal()
 
        elif comando.startswith("!admin "):
            partes = comando.split()
            if len(partes) == 3:
                try:
                    user_id = int(partes[1])
                    opcao = int(partes[2])
                    admin_atribuir_terminal(user_id, opcao)
                except ValueError:
                    print("Uso: !admin <id_usuario> <numero>")
            else:
                print("Uso: !admin listar  OU  !admin <id_usuario> <numero>")
 
        elif comando == "!serverinfo":
            serverinfo_terminal()
 
        elif comando.startswith("!userinfo"):
            partes = comando.split()
            if len(partes) == 2:
                try:
                    user_id = int(partes[1])
                    userinfo_terminal(user_id)
                except ValueError:
                    print("Uso: !userinfo <id_usuario>")
            else:
                print("Uso: !userinfo <id_usuario>")
 
        elif comando.startswith("!kick"):
            partes = comando.split(maxsplit=2)
            if len(partes) >= 2:
                try:
                    user_id = int(partes[1])
                    motivo = partes[2] if len(partes) == 3 else "Não especificado"
                    kick_terminal(user_id, motivo)
                except ValueError:
                    print("Uso: !kick <id_usuario> [motivo]")
            else:
                print("Uso: !kick <id_usuario> [motivo]")
 
        elif comando.startswith("!ban"):
            partes = comando.split(maxsplit=2)
            if len(partes) >= 2:
                try:
                    user_id = int(partes[1])
                    motivo = partes[2] if len(partes) == 3 else "Não especificado"
                    ban_terminal(user_id, motivo)
                except ValueError:
                    print("Uso: !ban <id_usuario> [motivo]")
            else:
                print("Uso: !ban <id_usuario> [motivo]")
 
        elif comando.startswith("!unban"):
            partes = comando.split()
            if len(partes) == 2:
                try:
                    user_id = int(partes[1])
                    unban_terminal(user_id)
                except ValueError:
                    print("Uso: !unban <id_usuario>")
            else:
                print("Uso: !unban <id_usuario>")
 
        elif comando == "!backup":
            backup_terminal()
 
        elif comando == "!nuke":
            nuke_terminal()
 
        elif comando == "!stop":
            stop_terminal()
 
        elif comando == "!restart":
            restart_terminal()
 
# ---------- RODAR O BOT ----------
TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "")
if not TOKEN:
    print("❌ Defina a variável de ambiente DISCORD_BOT_TOKEN (arquivo .env) antes de rodar o bot.")
    sys.exit(1)
 
def rodar_bot():
    global encerrar_bot, reiniciar_bot
    while True:
        try:
            bot.run(TOKEN)
        except Exception as e:
            print(f"Bot caiu com erro: {e}")
 
        if encerrar_bot:
            print("Bot encerrado. Até mais!")
            sys.exit(0)
 
        if reiniciar_bot:
            print("Reiniciando processo...")
            script = os.path.abspath(sys.argv[0])
            if os.name == "nt":
                subprocess.Popen([sys.executable, script], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen([sys.executable, script])
            sys.exit(0)
 
        print("Reiniciando em 5 segundos...")
        time.sleep(5)
 
if __name__ == "__main__":
    rodar_bot()
