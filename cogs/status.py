import discord
from discord.ext import commands
from discord.commands import Option, slash_command
import time

import db


class Status(commands.Cog):
        
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command()
    async def user_status(self, ctx):
        '''Returns the users amount along with any unpaid wagers.'''
        user = [str(ctx.author.id), str(ctx.author.name)]
        user_amount = db.user_lookup(user)[0][-1]
        bets = db.unpaid_bets_lookup(str(ctx.author.id))
        bet_str = _bet_str(bets)

        #embed info
        info_embed = discord.Embed(title='User Status', color=0x00FF00)
        info_embed.set_author(
            name=ctx.author.display_name, icon_url=ctx.author.display_avatar
        )
        info_embed.add_field(
            name="Your Points", value=user_amount, inline=False
        )
        info_embed.add_field(
            name="Gametime | Team Choice | Bet Amount, Reward", value=bet_str, inline=False
        )    
        info_embed.add_field(
            name="_", value='View this project on [GitHub](https://github.com/JonathanRJoyner/Discord_Wagering_Bot).', inline=False
        )
        info_embed.set_footer(
            text=f'Generated at <t:{time.time()}:R'
        )
        await ctx.send_response(
            ' ',embed=info_embed
        )

    @discord.slash_command()
    async def global_leaderboard(self, ctx):
        '''Returns top 10 users'''
        users = db.top_10_users()
        users = _users_str(users)

        #embed info
        info_embed = discord.Embed(title='Global Leaderboard', color=0x00FF00)
        info_embed.add_field(
            name="Username | Amount", value=users, inline=False
        )    
        info_embed.add_field(
            name="_", value='View this project on [GitHub](https://github.com/JonathanRJoyner/Discord_Wagering_Bot).', inline=False
        )
        info_embed.add_field(
            name='_', value=f'As of: <t:{int(time.time())}:R>'
        )
        await ctx.send_response(
            ' ',embed=info_embed
        )

def _users_str(users):
    '''Takes users and outputs as a string'''
    user_str = ''
    for user in users:
        user = f'{user[0]} | {user[1]}\n'
        user_str += user

    return user_str

def _bet_str(bets):
    '''Takes user bets and outputs as a string.'''
    bet_str = ''
    for bet in bets:
        bet = f'{bet[2]} | {bet[5]} | {bet[6]}, {bet[7]}\n'
        bet_str += bet
    
    return bet_str

def setup(bot):
    bot.add_cog(Status(bot))
