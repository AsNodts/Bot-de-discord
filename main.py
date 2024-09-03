from datetime import datetime
from discord.ext import commands, tasks
from my_token import MY_TOKEN
import discord
from easy_pil import Editor, font, load_image_async, Canvas
from random import choice
from random import randint
from discord import app_commands
import requests
import json
import time
import asyncio
from collections import defaultdict



permissoes = discord.Intents.default()
permissoes.message_content = True 
permissoes.members = True
permissoes.guilds = True


bot = commands.Bot(command_prefix="!!",intents=discord.Intents.all(),application_id= 1277972608893321218)

# Variáveis para o cooldown do on_message
last_interaction_time = {}
cooldown_seconds = 20

help_command=None

@bot.event
async def on_ready():
    print(f'{bot.user} está online e pronto para uso!')
    try:
        synced = await bot.tree.sync()  # Sincroniza os comandos do bot
        print(f'Sincronizados {len(synced)} comandos de barra.')
    except Exception as e:
        print(f'Erro ao sincronizar comandos: {e}')
    troca_status.start()


#loop alteração de status
bot_status = ['any status you want']


@tasks.loop(minutes=30)
async def troca_status():
    random_status = choice(bot_status)
    await bot.change_presence(activity=discord.Game(random_status))


# Função para pegar a cor do primeiro cargo com cor definida
def get_first_role_color(membro):
    for role in membro.roles:
        if role.color.value != 0:  # Verifica se o cargo tem uma cor definida (diferente de preto padrão)
            return role.color.to_rgb()
    return (255, 255, 255)  # Retorna branco se nenhum cargo tiver cor definida



#eventos aqui ----------------
@bot.event
async def on_member_join(membro: discord.Member):
    # Carregar a imagem de fundo
    bg = Editor('imagens/background.jpg')

    # Carregar o avatar do membro
    perfil = await load_image_async(membro.display_avatar.url)
    perfil = Editor(perfil).resize((350, 350)).circle_image()

     # Criar a borda ao redor do avatar
    border_size = 10  # Tamanho da borda
    border_color = "white"  # Cor da borda
    borda = Editor(Canvas((perfil.image.width + border_size*2, perfil.image.height + border_size*2), color=border_color))
    borda = borda.circle_image()
    borda.paste(perfil, (border_size, border_size))

    # Dimensões da imagem de fundo
    bg_largura = bg.image.width
    bg_altura = bg.image.height

    # Centralizar o avatar na imagem de fundo
    avatar_x = (bg_largura - perfil.image.width) // 2
    avatar_y = (bg_altura - perfil.image.height) // 2 - 100  # Ajuste vertical

    bg.paste(borda.image, (avatar_x, avatar_y))

    # Definir as fontes
    fonte1 = font.Font.poppins(size=70)
    # fonte2 = font.Font.poppins(size=50)
    fonte3 = font.Font.poppins(size=30)

    # Centralizar e adicionar o nome do membro
    text_x = bg_largura // 2
    text_y1 = avatar_y + perfil.image.height + 50
    text_y2 = text_y1 + 80

    bg.text((text_x, text_y1), membro.name, align='center', color='white', font=fonte1)
    bg.text((text_x, text_y2), 'Bem vindo(a)!', align='center', color='white', font=fonte3)

    # Salvar a imagem como bytes para enviar no Discord
    imagem = discord.File(fp=bg.image_bytes, filename='bemvindo.png')

    canal_bemvindo = membro.guild.get_channel(ID do cana de boas vindas) #com ""

    join_role = discord.utils.get(membro.guild.roles, name= cargo que sera atribuido automaticamente) #com ""
    await membro.add_roles(join_role)


    embed = discord.Embed(
    title= f'Bem vindo(a) {membro.display_name}, espero que se divirta!',
    description= 'vem toma um cafézinho com a gente!',
    color= discord.Color.orange()
    )
    embed.set_image(url=imagem)

    # Definir a imagem do embed como o nome do arquivo
    embed.set_image(url="attachment://bemvindo.png")
    
    # Enviar o embed com o arquivo de imagem
    await canal_bemvindo.send(membro.mention)
    await canal_bemvindo.send(embed=embed, file=imagem)


@bot.event
async def on_member_remove(member: discord.Member):
    # Verifica os registros de auditoria
    guild = member.guild
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
        if entry.target.id == member.id:
            # Se o último log for uma expulsão e o membro for o alvo, interrompe o evento
            return

    # Verifica os registros de auditoria para banimentos (ban)
    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
        if entry.target.id == member.id:
            # Se o último log for um banimento e o membro for o alvo, interrompe o evento
            return

    # Obtém o canal onde você deseja enviar a mensagem
    channel = discord.utils.get(member.guild.text_channels, name='canal de saida')

    if channel:
        # Cria o embed
        embed = discord.Embed(
            title=f"{member.name} saiu do servidor",
            description="Correu pra longe da gente!",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url=member.avatar.url)
        embed.set_footer(text="Até mais, esperamos nunca mais vê-lo novamente!")

        # Envia o embed para o canal
        await channel.send(embed=embed)


# Configurações do anti-flood
MESSAGE_LIMIT = 5  # Limite de mensagens
TIME_FRAME = 10   # Intervalo de tempo (em segundos)
MUTE_DURATION = 60 # Duração do mute (em segundos)

# Dicionário para rastrear as mensagens por usuário
user_messages = defaultdict(list)
muted_users = defaultdict(bool)


@bot.event
async def on_message(message):
    autor = message.author
    if autor.bot:
        return

    if isinstance(message.channel, discord.DMChannel):

        embed = discord.Embed(
            title='Não respondo a DM',
            description='Desculpa, peço que use os comandos no servidor pode ser? Ou pode usar aqui mesmo, eles funcionam. Não diga que eu não tentei.',
            color=discord.Color.dark_orange()
        )
        embed.set_image(url='https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExczRodjBqMzRhdXlmcnhzemhqam1sOHY3NzlxODAzc24zNzZ3NnFraiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/eXUEJIGa2BXWjh8q6l/giphy.gif')

        await message.channel.send(embed=embed)
    else:
        # Se o usuário estiver silenciado, deletar a mensagem imediatamente
        if muted_users[message.author.id]:
            await message.delete()
            return

        await bot.process_commands(message)


    # Obter a hora atual
    current_time = time.time()

    # Atualizar a lista de mensagens do usuário
    user_messages[message.author.id].append(current_time)

    # Filtrar mensagens que estão fora do intervalo de tempo definido
    user_messages[message.author.id] = [msg_time for msg_time in user_messages[message.author.id] if current_time - msg_time <= TIME_FRAME]

    # Verificar se o usuário ultrapassou o limite de mensagens
    
    if len(user_messages[message.author.id]) > MESSAGE_LIMIT:
        print(f"Usuário {message.author} ultrapassou o limite de mensagens.")
        
        # Verificar se o usuário já está silenciado para evitar múltiplos silenciamentos
        if not muted_users[message.author.id]:
            try:
                muted_users[message.author.id] = True

                muted_role = discord.utils.get(message.guild.roles, name="Muted")
                if not muted_role:
                    muted_role = await message.guild.create_role(name="Muted", reason="Criado para mutar usuários que flodam")
                    for channel in message.guild.channels:
                        await channel.set_permissions(muted_role, send_messages=False)

                await message.author.add_roles(muted_role)

                mute_embed = discord.Embed(
                    title="Usuário(a) Silenciado(a)",
                    description=f'{message.author.mention} foi silenciado(a) por {MUTE_DURATION} segundos por flood.',
                    color=discord.Color.red()
                )
                mute_embed.add_field(name="Número de Mensagens", value=f"{len(user_messages[message.author.id])} em menos de 10 segundos", inline=False)
                mute_embed.add_field(name="Tempo de Silenciamento", value=f"{MUTE_DURATION} segundos", inline=False)
                mute_embed.set_thumbnail(url=message.author.avatar.url)
                mute_embed.set_footer(text="Sistema Anti-Flood")
                
                await message.channel.send(embed=mute_embed)

                await asyncio.sleep(MUTE_DURATION)

                await message.author.remove_roles(muted_role)

                unmute_embed = discord.Embed(
                    title="Usuário(a) Desmutado(a)",
                    description=f'{message.author.mention} foi desmutado(a).',
                    color=discord.Color.green()
                )
                unmute_embed.set_thumbnail(url=message.author.avatar.url)
                unmute_embed.set_footer(text="Sistema Anti-Flood")
                
                await message.channel.send(embed=unmute_embed)

                # Desmarcar o usuário como silenciado após o período de mute
                muted_users[message.author.id] = False

            except discord.Forbidden:
                error_embed = discord.Embed(
                    title="Erro de Permissão",
                    description=f'Não tenho permissão para mutar {message.author.mention}.',
                    color=discord.Color.orange()
                )
                await message.channel.send(embed=error_embed)
            except Exception as e:
                error_embed = discord.Embed(
                    title="Erro",
                    description=f'Ocorreu um erro ao tentar mutar {message.author.mention}: {e}',
                    color=discord.Color.orange()
                )
                await message.channel.send(embed=error_embed)
    else:
        print(f"Usuário {message.author} ainda não ultrapassou o limite de mensagens.")

    if 'eai' in message.content.lower():
        usuario = message.author.display_name
        await message.channel.send(f'opa {usuario} ❤️!')



@bot.event
async def on_guild_channel_create(canal: discord.abc.GuildChannel):
    if isinstance(canal, discord.TextChannel):
        embed = discord.Embed(
            title= f'Novo canal criado: {canal.name}',
            description='Aproveite que está vazio, converse comigo!',
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=bot.user.display_avatar.url)
        embed.set_footer(text='aceita um café?')

        await canal.send(embed=embed)



# comandos aqui ---------------------
@bot.tree.command(description='Verifique seu XP no servidor (não funciona, mas ta ai) 🧑🏻‍🏭')
async def xp(interaction: discord.Interaction):
    # Carregar a imagem de fundo
    bg = Editor('imagens/xpxphehe.jpg').resize((800, 220))

    # Carregar o avatar do usuário
    perfil = await load_image_async(interaction.user.display_avatar.url)
    perfil = Editor(perfil).resize((160, 160)).circle_image()

    # Criar a borda branca ao redor do avatar
    border_size = 10  # Tamanho da borda
    border_color = "white"  # Cor da borda
    borda = Editor(Canvas((perfil.image.width + border_size*2, perfil.image.height + border_size*2), color=border_color))
    borda = borda.circle_image()
    borda.paste(perfil, (border_size, border_size))

    # Colar o avatar com a borda na posição original (50, 220//2 - 80)
    bg.paste(borda.image, (50, 220//2 - 80))

    # Definir as fontes
    font1 = font.Font.poppins(size=40)

    # Adicionar o nome do usuário
    bg.text((222, 50), interaction.user.display_name, color='white', font=font1)

    # Adicionar a barra de XP
    bg.rectangle((222, 100), width=500, height=50, outline='white', stroke_width=3)
    bg.bar((227, 105), 490, 40, 100, fill='green')
    bg.text((330, 102), 'É VAGABUNDO', color='black', font=font1)
    
    # Adicionar o texto "XP" e "Nivel: Infinito"
    bg.text((666, 51), 'XP', color='white', font=font1)
    bg.text((550, 180), 'Nivel: Infinito', color='white', font=font1)

    # Salvar a imagem como bytes para enviar no Discord
    imagem = discord.File(fp=bg.image_bytes, filename='xp.png')
    await interaction.response.send_message(file=imagem)



@bot.tree.command(description='Responde usuario com olá 👋🏻')
async def ola(interact:discord.Interaction):
    await interact.response.send_message(f'Olá, {interact.user.mention} Sou a {bot.user.mention}, muito prazer ❤️')


@bot.tree.command(description="Envia uma mensagem dentro de um embed contendo o que o usuário digitou 📨")
async def falar(interact: discord.Interaction, frase: str):
    # Cria o embed com o conteúdo da frase
    embed = discord.Embed(
        title=frase,
        color=discord.Color.blue()  # Cor do embed
    )

    # Envia a resposta com o embed
    await interact.response.send_message(embed=embed)


@bot.tree.command(description='Sorteia entre Cara ou Coroa 🪙')
async def jogar_moeda(interact: discord.Interaction):

    # Resultado do sorteio
    resultado = choice(['Caiu Cara!', 'Caiu Coroa!'])

    # Cria o embed com o resultado
    embed = discord.Embed(
        title=resultado,
        color=discord.Color.green()  # Cor verde para o embed
    )
    await interact.response.send_message(embed=embed)


@bot.tree.command(description='Informações do Usuário 📜')
async def user_info(interaction: discord.Interaction, user: discord.Member = None):
    if user is None:
        user = interaction.user  # Obter o usuário que executou o comando, se nenhum for especificado

    rlist = [role.mention for role in user.roles if role.name != '@everyone']
    b = ', '.join(rlist) if rlist else 'Nenhum cargo'

    embed = discord.Embed(
        colour=user.color,
        timestamp=discord.utils.utcnow()
    )

    embed.set_author(name=f'Informações do usuário - {user.display_name}', icon_url=user.display_avatar.url)
    embed.set_thumbnail(url=user.display_avatar.url)
    
    embed.add_field(name='Criado em:', value=user.created_at.strftime("%d/%m/%Y %H:%M:%S"), inline=False)
    embed.add_field(name='Entrou em:', value=user.joined_at.strftime("%d/%m/%Y %H:%M:%S"), inline=False)
    embed.add_field(name=f'Cargos ({len(rlist)}):', value=b, inline=False)
    embed.add_field(name='Maior cargo:', value=user.top_role.mention, inline=False)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(description='Informações do servidor 📜')
async def server_info(interaction: discord.Interaction):
    guild = interaction.guild
    user = interaction.user
    user_color = user.color
    embed = discord.Embed(
        color=user_color,
        title={guild.name},
        description=f'**Quantos Membros:** `{guild.member_count}`\n'
                    f'**criador:** {guild.owner.mention}\n'
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    embed.set_footer(text="Forever AsNodt")
    
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="avatar", description="Obtém a URL do avatar de um usuário 🧑🏾‍💻")
async def avatar(interaction: discord.Interaction, user: discord.User):
    # Pega a URL do avatar usando a propriedade 'display_avatar.url'
    avatar_url = user.display_avatar.url
    
    # Cria o embed para mostrar a URL do avatar
    embed = discord.Embed(
        title=f"Avatar de {user.name}",
        description=f"[Clique aqui para ver a imagem]({avatar_url})",
        colour=user.color
    )
    
    # Adiciona o avatar como imagem no embed
    embed.set_image(url=avatar_url)
    
    # Responde à interação com o embed
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="banner", description="Obtém a URL do banner de um usuário 🤓")
async def banner(interaction: discord.Interaction, user: discord.User):
    # Usa o método fetch_user para pegar o objeto completo do usuário   
    full_user = await bot.fetch_user(user.id)

    banner_url = full_user.banner.url
    
    # Cria o embed para mostrar a URL do avatar
    embed = discord.Embed(
        title=f"Banner de {user.name}",
        description=f"[Clique aqui para ver a imagem]({banner_url})",
        colour=user.color
    )
    
    # Adiciona o avatar como imagem no embed
    embed.set_image(url=banner_url)
    
    # Responde à interação com o embed
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name='joga_um_d20_ai', description='Joga um dado de 20 lados para testar suas sorte 🍀')
async def joga_um_D20_ai(interaction: discord.Interaction):
    resultado_dado = randint(1, 20)
    embed = discord.Embed(
        title = f'caiu no {resultado_dado} 🎲',
        color = discord.Color.random()
    )
    match resultado_dado:
        case 1:
            embed.description = 'Que isso? bateu com uma pena??'
            embed.set_image(url= 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExZzVvcmo5MWZsazFqNGhjM2tscHU2OXc5anI1N3J6dm5hc25sMWJqMiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/xUySTBrWM65BXvWjKg/giphy.gif')

        case 2:
            embed.description = 'Nossa, nem teve efeito sua ação.'

            embed.set_image(url= 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExYjk2OTZ6azJxcmx5bmR5aHp5Z3Y3OWlmNHAwYXpqZTk2MnVsc3B3dSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/joYf3Ba2phD15ch9Nt/giphy.gif')

        case 3:
            embed.description = "Bem, você tentou... mas foi tipo um peteleco."
            embed.set_image(url= 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExY2tlMWxnajJyYmp6ZHQ1dzVoNmp3Z20yc2pnZHhraXRia3BjanU4eSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3o7ZeAgHVHDH0jCTN6/giphy.gif')

        case 4:
            embed.description = "Esse golpe até acertou, mas foi só uma raspadinha."
            embed.set_image(url= 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExbzdqc2FzenNhaDB1dWQ1eDlwYXpjZXBvNXQzN2k4NnpyN2Y3ODR1aCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3osxYqCSpqee9FWISs/giphy.gif')

        case 5:
            embed.description = "Ok, não foi o pior, mas também não foi grande coisa."
            embed.set_image(url= 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExMGhsZXJ0Z2U3YjlsOHVjZ21ya2hicWlpbmxqOGdwa3E3emU3d2N4NyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/o2Lwy4g7Dzptu/giphy.gif')

        case 6:
            embed.description = "Um dano decente, mas nada que faça o inimigo se preocupar muito."
            embed.set_image(url= 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExaXF3czNqN3Y1NWp1bDN3bXhraTRieXlkN25ycGlxZzFhaGtxZ2YxeSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/LFiOdYoOlEKac/giphy.gif')

        case 7:
            embed.description = 'Acho que você fez um corte bonito de cabelo no inimigo.'
            embed.set_image(url= 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExd2JxZGdyZHU5NG5vY3dpMHRlZml6ejAyMzdvNG5pa3V0dDBoMnE3aiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/sxENmjMbkKZ4A/giphy.gif')
        case 8:
            embed.description = "Rolou um dano médio, o inimigo até fez uma careta."
            embed.set_image(url= 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExN21tNmloZDN0aTc5Z2hna3E1YzduaGFoaWU4NmRud3JtaWRoMnoxMSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/jOpLbiGmHR9S0/giphy.gif')

        case 9:
            embed.description = "Boa! Você fez o inimigo se contorcer um pouquinho."
            embed.set_image(url= 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExMjhsNW9xNjJ1dDZ6MDA0Y29yNTR1NWttYjhxc2JtcTlkYnFvbWVwaSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/WBea8bEI90ViM/giphy.gif')

        case 10:
            embed.description = 'Esse com certeza doeu..'
            embed.set_image(url= 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExdWc5dTcybDNza2F5eHh0b3VieGVmZ2psb3phdDg4bDdxc2psdWU0NyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/gfBelJmvuZnsuva4gR/giphy.gif')

        case 11:
            embed.description = "Agora sim, você fez o inimigo pensar duas vezes!"
            embed.set_image(url= 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExZmcwc3M1OXljejB3cTc1cDlzbDdzb2F2ZGEweHN4ZmEwb3c0b3FoNSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/1wqqlaQ7IX3TXibXZE/giphy.gif')

        case 12:
            embed.description = "O dano foi forte! O inimigo já está começando a ficar preocupado."
            embed.set_image(url= 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExeWcwZm40NWFjc2wwMmpiNWo4MXN3YmlpOTJscTF2czBsdnA2bnNmZiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/XKwWJQuBJTT8Y/giphy.gif')


        case 13:
            embed.description = "Você acertou bem! O dano fez o inimigo cambalear."
            embed.set_image(url= 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExdXZ1ampqZjlwOTFtazV0bGRuaXFka2RqdjlsajUwOGRqYnc1NDl4eiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/FsoJPj4j0xpPG/giphy.gif')

        case 14:
            embed.description = "Esse sim foi um ataque de respeito! O inimigo está mal."
            embed.set_image(url= 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExd3plcnQxbTh3NGxzaDQzY2s2cWJpNW91bG41aXJmY2Y4dG4xd2NqayZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/IUxFvKwD3jXisqR5w7/giphy.gif')

        case 15:
            embed.description = "Aí sim! O golpe pegou em cheio e deu uma bela machucada."
            embed.set_image(url= 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExZWVxbTd4dnBzcWZnNW8xOTVodTd5MDVtdTVsYTY2YXZydmY0cWNmMyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/jwKC0qlOoXmcLDB4vC/giphy.gif')

        case 16:
            embed.description = "Seu ataque fez estrago, o inimigo sentiu o impacto."
            embed.set_image(url= 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExYXhoOGYzejRndGpjbGc3NGZqOHJ3OGZ0cThkYXU5c3luYnZiMnJkaSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/KtNuQVJUJAItw7psGw/giphy.gif')

        case 17:
            embed.description = 'caramba!! Otimo efeito. Com certeza seu oponente ficou chocado.'
            embed.set_image(url='https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExbWx2dWoyN3VhZWs0NnB3aWtyc2FwY2F6NzhnZ3p1Y3Rqc2k4amsxMiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/CLPSFbwMqpsvf5cRe8/giphy.gif')
        case 18:
            embed.description = "Seu ataque foi excelente, o dano foi alto e deixou o inimigo à beira da derrota."
            embed.set_image(url= 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExZTd0bm5sd2RxanN5dGk0emZwcHR6NWIyd3c2czcyajBveDRyYXZ4eiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/iOg2W5LiVrrAlN2snB/giphy.gif')

        case 19:
            embed.description = "Seu ataque foi quase perfeito, o dano foi devastador!"
            embed.set_image(url= 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExdHFuazR1eHZ2d3ZoNnp0d3Fvd3Uyc2pyMnh3dThieXlyOWtvejNjcCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/gw3zMXiPDkOyVBsc/giphy.gif')

        case 20:
            embed.description = '🔥CRITICO🔥!!!! Você explodiu seu oponente em um unico golpe!!!'
            embed.set_image(url= 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExYTMwbGttY2NhZmYxaHFodzhtOTZjd2Z1enAzaG5sNGF3dnRybmU4dyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/xTiTnoHt2NwerFMsCI/giphy.gif')



    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="sortear_jogo", description="Sorteia um dos jogos fornecidos 🎊")
@app_commands.describe(jogos= 'separe o nome dos jogos com ","')
async def sortear_jogo(interaction: discord.Interaction, jogos: str): 
    # Divide a lista de jogos pelo separador ','
    lista_jogos = jogos.split(',')

    # Remove espaços extras
    lista_jogos = [jogo.strip() for jogo in lista_jogos]
    
    # Sorteia um dos jogos da lista
    jogo_sorteado = choice(lista_jogos)
    

    # Envia a resposta de volta ao usuário
    embed = discord.Embed(
        title= f"O jogo sorteado é:  **{jogo_sorteado}**",
        colour= discord.Color.orange()
    )
    embed.set_image(url= 'https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExMzNpMXpjcGZxZWw0anBxbmxmeDB6N2UyZ3BqYm5uNjB6bG9leG9tMyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/uk6itdnB0IeqZf2FKS/giphy.gif')


    await interaction.response.send_message(embed= embed)


@bot.tree.command(name='match', description='Verifica a porcentagem de match que um usuário tem com outro 🧑‍🤝‍🧑')
async def match(interaction: discord.Interaction, usuario1: discord.Member, usuario2: discord.Member):
    await interaction.response.defer()  # Defer the interaction to give more time

    try:
        avatar_url_usuario1 = usuario1.display_avatar.url
        avatar_url_usuario2 = usuario2.display_avatar.url
        usu1 = await load_image_async(avatar_url_usuario1)
        usu2 = await load_image_async(avatar_url_usuario2)
    except Exception as e:
        await interaction.followup.send(f"Erro ao carregar avatares: {e}")
        return

    # Continue with image processing as before
    try:
        bg = Editor('imagens/background_kiss.jpg').resize((600, 300))
        perfil1 = Editor(usu1).resize((160, 160)).circle_image()
        perfil2 = Editor(usu2).resize((160, 160)).circle_image()

        color_usuario1 = get_first_role_color(usuario1)
        color_usuario2 = get_first_role_color(usuario2)

        border_size = 8
        borda1 = Editor(Canvas((perfil1.image.width + border_size*2, perfil1.image.height + border_size*2), color=color_usuario1))
        borda1 = borda1.circle_image()
        borda1.paste(perfil1, (border_size, border_size))

        borda2 = Editor(Canvas((perfil2.image.width + border_size*2, perfil2.image.height + border_size*2), color=color_usuario2))
        borda2 = borda2.circle_image()
        borda2.paste(perfil2, (border_size, border_size))

        bg.paste(borda1.image, (50, 220//2 - 80))
        bg.paste(borda2.image, (390, 220//2 - 80))

        fonte1 = font.Font.poppins(size=50)
        fonte2 = font.Font.poppins(size=10)
        fonte3 = font.Font.poppins(size=20)
        resultado_porcento = randint(1, 100)

        bg.rectangle((150, 210), width=300, height=50, outline='white', stroke_width=3)
        bg.bar((155, 215), 290, 40, resultado_porcento, fill='red')
        bg.text((265, 218), str(resultado_porcento) + '%', font=fonte1, color='white')

        bg.text((80, 10), usuario1.display_name, font=fonte3, color=color_usuario1)
        bg.text((420, 10), usuario2.display_name, font=fonte3, color=color_usuario2)


        if resultado_porcento <= 10:
            bg.text((230, 280), 'melhor conversar com o GPT', font= fonte2, color= 'orange')

        elif resultado_porcento <= 20:
            bg.text((225, 280), 'não serve nem pra amizade', font= fonte2, color= 'orange')

        elif resultado_porcento <= 30:
            bg.text((245, 280), 'ETERNA FRIENDZONE', font= fonte2, color= 'orange')

        elif resultado_porcento <= 40:
            bg.text((165, 280), 'Pode haver uma faísca escondida aqui, quem sabe...', font= fonte2, color= 'orange')

        elif resultado_porcento <= 50:
            bg.text((130, 280), 'Vocês são tipo fast food: bons de vez em quando, mas não todo dia.', font= fonte2, color= 'orange')

        elif resultado_porcento <= 60:
            bg.text((135, 280), "Olha só! Já podem sair pra um café e reclamar da vida juntos.", font= fonte2, color= 'orange')

        elif resultado_porcento <= 70:
            bg.text((50, 280), "Essa dupla tem potencial! Se não virarem BFFs, pelo menos memes compartilhados vocês terão.", font= fonte2, color= 'orange')

        elif resultado_porcento <= 80:
            bg.text((110, 280), "Isso aí é quase uma amizade verdadeira... Ou pelo menos uma boa treta!", font= fonte2, color= 'orange')

        elif resultado_porcento <= 90:
            bg.text((80, 280), "Cara, isso aqui é parceria pura. Se não forem BFFs, eu nem sei mais o que é amizade.", font= fonte2, color= 'orange')

        elif resultado_porcento <= 99:
            bg.text((80, 280), "Vocês são tipo o combo de hambúrguer e batata frita. Não tem como dar errado!", font= fonte2, color= 'orange')

        else:
            resp = ["100%! Já podem criar uma banda juntos, lançar um podcast e dominar o mundo.", "MATCH PERFEITO! Vocês são praticamente a dupla dinâmica do Discord!" ]
            bg.text((100, 280), choice(resp), font= fonte2, color= 'orange')

        # Continue with the rest of the code...

        imagem = discord.File(fp=bg.image_bytes, filename='match.png')
        await interaction.followup.send(file=imagem)  # Use followup to send the response after deferring
    except Exception as e:
        await interaction.followup.send(f"Ocorreu um erro ao gerar a imagem: {e}")


@bot.tree.command(name="meme", description="Envia um meme aleatório em inglês infelizmente 🛠️")
async def meme(interaction: discord.Interaction):
    response = requests.get("https://meme-api.com/gimme")
    data = response.json()

    if data:
        meme_url = data["url"]
        meme_title = data["title"]
        embed = discord.Embed(title=meme_title)
        embed.set_image(url=meme_url)
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message("Não consegui encontrar um meme agora, tente novamente!")


@bot.tree.command(name='gif', description= 'envia um gif com base no que o usuario escreveu 🎥')
async def gif(interaction: discord.Interaction, termo: str):
    api_key = 'YOUR KEY FOR API'
    response = requests.get(f"https://api.giphy.com/v1/gifs/search?api_key={api_key}&q={termo}&limit=1&rating=pg")
    data = response.json()

    if data["data"]:
        gif_url = data["data"][0]["images"]["original"]["url"]
        await interaction.response.send_message(gif_url)
    else:
        await interaction.response.send_message("Não encontrei nenhum GIF para essa palavra-chave.")


with open('piadas.json', 'r', encoding='utf-8') as f:
    piadas_data = json.load(f)
    piadas = piadas_data['piadas']

@bot.tree.command(name='piada', description='Manda uma piada braba! 😁')
async def piada(interaction: discord.Interaction):
    piadoca_da_vez = choice(piadas)

    descricoes = ['muito boa né...', 'eu sei, me superei nessa!', 'va dizer que não saiu nem um arzinho do nariz?', 'te fiz rir né..', 'de uma risada pelo menos', 'Capoto o corsa né', 'Até eu ri dessa.', 'com certeza o cesar riu', 'nada a declarar', '', 'só falo verdades.']

    embed = discord.Embed(
        title=piadoca_da_vez,
        description= choice(descricoes),
        color= discord.Color.purple()
    )

    await interaction.response.send_message(embed=embed)


#Função auxiliar para verificar se o alvo tem um cargo superior ou igual
def is_higher_role(author: discord.Member, target: discord.Member) -> bool:
    return author.top_role <= target.top_role

#FIX CARGOS
@bot.tree.command(name="ban", description="Bane um membro (apenas moderadores podem usar)")
@discord.app_commands.checks.has_any_role('cargos que podem usar')
async def ban(interaction: discord.Interaction, member: discord.Member, razao: str = None):
    
    # Impedir que o usuário se bana
    if member == interaction.user:
        await interaction.response.send_message("Você não pode se banir!", ephemeral=True)
        return
    
    # Impedir que o bot seja banido
    if member == bot.user:
        await interaction.response.send_message("Eu não posso me banir!", ephemeral=True)
        return
    
    # Verificar hierarquia de cargos
    if is_higher_role(interaction.user, member):
        await interaction.response.send_message("Você não pode banir alguém com cargo igual ou superior ao seu!", ephemeral=True)
        return
    
    # Definir a razão padrão caso não seja especificada
    if razao is None:
        razao = 'nada declarado'

    try:
        # Banir o membro
        await member.ban(razao=razao)
        
        # Enviar resposta efêmera de sucesso
        await interaction.response.send_message(f"{member.display_name} foi banido com sucesso!", ephemeral=True)

        # Criar o embed
        embed = discord.Embed(title="Usuário Banido 🔨", color=discord.Color.red())
        embed.set_thumbnail(url= member.avatar.url)
        embed.add_field(name='Usuário', value= member.mention, inline=False)
        embed.add_field(name= "Razão", value=razao, inline=False)
        embed.add_field(name= 'Expulso por:', value=interaction.user.mention)

        # Enviar o embed no canal específico (substitua o ID abaixo pelo ID correto)
        channel = bot.get_channel(1200601061883379782)
        if channel is not None:
            await channel.send(embed=embed)

    except discord.Forbidden:
        await interaction.response.send_message("Não tenho permissão para banir este membro!", ephemeral=True)
    except discord.HTTPException:
        await interaction.response.send_message("Ocorreu um erro ao tentar banir o membro.", ephemeral=True)


# FIX CARGOS
@bot.tree.command(name="expulsar", description="Expulsa um membro (apenas moderadores podem usar)")
@discord.app_commands.checks.has_any_role('cargos que podem usar')
async def kick(interaction: discord.Interaction, membro: discord.Member, reason: str = None):

    # Impedir que o usuário se expulse
    if membro == interaction.user:
        await interaction.response.send_message("Você não pode se expulsar!", ephemeral=True)
        return
    
    # Impedir que o bot seja banido
    if membro == bot.user:
        await interaction.response.send_message("Eu não posso me banir!", ephemeral=True)
        return


    # Definir a razão padrão caso não seja especificada
    if reason is None:
        reason = 'nada declarado'

    # Expulsar o membro e enviar resposta efêmera
    await membro.kick(reason=reason)
    await interaction.response.send_message(f"{membro.display_name} foi expulso com sucesso!", ephemeral=True)
    
    # Criar o embed
    embed = discord.Embed(title="Usuário Expulso", color=discord.Color.orange())
    embed.set_thumbnail(url=membro.avatar.url)  # Adiciona o avatar do usuário
    embed.add_field(name='Usuário', value= membro.mention, inline=False)
    embed.add_field(name="Razão", value=reason, inline=False),
    embed.add_field(name= 'Expulso por:', value=interaction.user.mention)

    # Enviar o embed no canal específico
    channel = bot.get_channel('canal a enviar embed do usuario expulso')
    if channel is not None:
        await channel.send(embed=embed)




@bot.tree.command(name="help", description="Mostra informações sobre todos os comandos disponíveis 🆘")
async def help(interaction: discord.Interaction):
    # Cria um embed para a mensagem de ajuda
    embed = discord.Embed(
        title="Lista de Comandos",
        description="Aqui estão todos os comandos disponíveis e o que cada um faz:",
        color=discord.Color.orange()
    )
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    # Adiciona os comandos e suas descrições
    embed.add_field(
        name="/xp", 
        value="Verifica seu XP no servidor (não implementado, apenas um exemplo de imagem).",
        inline=False
    )
    embed.add_field(
        name="/ola", 
        value="Responde com um 'Olá' mencionando o nome do usuário.",
        inline=False
    )
    embed.add_field(
        name="/falar <frase>", 
        value="Envia uma mensagem dentro de um embed contendo o que o usuário digitou.",
        inline=False
    )
    embed.add_field(
        name="/jogar_moeda", 
        value="Sorteia entre 'Cara' ou 'Coroa'.",
        inline=False
    )
    embed.add_field(
        name="/user_info [user]", 
        value="Mostra informações sobre o usuário especificado (ou sobre você se não especificar).",
        inline=False
    )
    embed.add_field(
        name="/server_info", 
        value="Mostra informações sobre o servidor.",
        inline=False
    )
    embed.add_field(
        name="/avatar [user]", 
        value="Mostra o avatar do usuário especificado.",
        inline=False
    )
    embed.add_field(
        name="/banner [user]", 
        value="Mostra o banner do usuário especificado.",
        inline=False
    )
    embed.add_field(
        name='/joga_um_d20_ai',
        value= 'Rola um dado de 20 lados para ver a força do seu ataque.',
        inline=False 
    )
    embed.add_field(
        name= '/sortear_jogo',
        value= 'digite jogos separados por virgula e o bot vai sortear qual você vai jogar.',
        inline=False
    )
    embed.add_field(
        name='/match',
        value= 'Verifica a porcentagem de match que um usuario tem com outro.',
        inline=False
    )
    embed.add_field(
        name= '/meme',
        value= 'Manda um meme aleatório.',
        inline=False
    )
    embed.add_field(
        name= '/gif [palavra-chave gif]',
        value= 'verifica no banco de dados do giphy se tem algum gif relacionado',
        inline=False
    )
    embed.add_field(
        name='/piada',
        value= 'Conta uma piada aleatoria (tem uns Easter eggs no meio delas)',
        inline=False
    )
    # Envia o embed como resposta à interação
    await interaction.response.send_message(embed=embed)


# Executar
if __name__ == "__main__":
    bot.run(MY_TOKEN)
