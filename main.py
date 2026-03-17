#this is a Music Bot For Discord In Python
#imported Stuff Or Requirements
import discord, asyncio, yaml, yt_dlp
from discord.ext import commands
from collections import deque

#our config file data colocter
with open("config.yml", "r") as (f):
    config = yaml.safe_load(f)


col = config["Embed_Color"]
bot_name = config["Bot_Name"]

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -loglevel panic'
}
YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'nocheckcertificate': True,
    'noplaylist': True,
    'ignoreerrors': True,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

#Main Bot Function
class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = deque()
        self.is_playing = False

#play next Song And The Current Song using YT_DLP to fetch music and music data
    async def play_next(self, ctx):
        if len(self.queue) > 0:
            self.is_playing = True
            
            url, title, webpage_url, duration, thumbnail, view_count, uploader, likes = self.queue.popleft()
            
            try:
                source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
                
                ctx.voice_client.play(source, after=lambda e: self.bot.loop.create_task(self.play_next(ctx)))
                
                embed = discord.Embed(title=f"{bot_name} Started a Song", description=f"**Song Name**: [{title}]({webpage_url}) \n**Video By**: {uploader}")
                if duration:
                    minutes, seconds = divmod(duration, 60)
                    embed.add_field(name="Duration", value=f"{int(minutes)}:{int(seconds):02d}", inline=True)
                embed.add_field(name="Requested by", value=ctx.author.mention, inline=True)
                embed.set_footer(text=f"Views: {view_count} | Likes: {likes}")
                embed.color=col
                if thumbnail:
                    embed.set_thumbnail(url=thumbnail)
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                print(f"Error in playback: {e}")
                await self.play_next(ctx)
        else:
            self.is_playing = False

    @commands.command()
    async def play(self, ctx, *, search: str):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect(self_deaf=True)
            else:
                return await ctx.send("Join a voice channel first!")

        async with ctx.typing():
            try:
                options = YDL_OPTIONS.copy()
                options['noplaylist'] = False 
                
                with yt_dlp.YoutubeDL(options) as ydl:
                    query = f"ytsearch1:{search}" if not search.startswith("http") else search
                    info = ydl.extract_info(query, download=False)

                if 'entries' in info:
                    # This is a playlist or search results list
                    songs_added = 0
                    for entry in info['entries']:
                        if entry:
                            self.queue.append((entry['url'], entry['title'], entry['webpage_url'], entry['duration'], entry['thumbnail'], entry['view_count'], entry['uploader'], entry['like_count']))
                            songs_added += 1
                    em = discord.Embed(title=f"{bot_name} Added", description=f"Added **{songs_added}** Song to Queue",color=col)
                    em.add_field(name="Requested By:",value=f"{ctx.author.mention}")
                    await ctx.send(embed=em)
                else:
                    # This is a single song
                    self.queue.append((info['url'], info['title']))
                    em = discord.Embed(title=f"{bot_name} Added", description=f"Added to queue: **{info['title']}**",color=col)
                    em.add_field(name="Requested By:",value=f"{ctx.author.mention}")
                    await ctx.send(embed=em)

            except Exception as e:
                await ctx.send(f"An error occurred: {e}")
                return

        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

    @commands.command()
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            em = discord.Embed(title=f"{bot_name} Skipped the Song", description="Skipped the Song")
            em.set_footer(text=f"Requsted By: {ctx.author.username}")
            await ctx.send(embed=em)
        else:
            em = discord.Embed(title=f"{bot_name} Skip Failed", description="Nothing is Playing Right Now")
            em.set_footer(text=f"Requsted By: {ctx.author.username}")
            await ctx.send(embed=em)

    @commands.command()
    async def stop(self, ctx):
        self.queue.clear()
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            embed = discord.Embed(title=f"{bot_name} Disconnected", description="⏹️ **Stopped and Disconnected.**\nCleared The Queue...")
            await ctx.send(embed=embed)




intents = discord.Intents.default()
intents.message_content = True 
intents.voice_states = True 
intents.guilds = True 

bot = commands.Bot(command_prefix=config['Bot_Prefix'], intents=intents)

async def main():
    await bot.add_cog(Music(bot))
    await bot.start(config["Token"])
    await print("Bot Is Online")

asyncio.run(main())