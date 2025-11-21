import discord

def get_server_context(guild: discord.Guild) -> str:
    if not guild:
        return ""

    channels = [c.name for c in guild.text_channels]
    roles = [r.name for r in guild.roles if r.name != "@everyone"]
    emojis = [f"{e.name} (<:{e.name}:{e.id}>)" for e in guild.emojis]

    context = (
        f"Server Context:\n"
        f"- Server Name: {guild.name}\n"
        f"- Channels: {', '.join(channels[:20])}\n"  # Limit to 20 to save tokens
        f"- Roles: {', '.join(roles[:20])}\n"
        f"- Emojis: {', '.join(emojis[:30])}\n"  # Limit to 30 to save tokens
    )
    return context
