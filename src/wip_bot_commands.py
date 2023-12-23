import requests
import asyncio


import discord 
import discord.ext
# from discord.ext import commands

from cache import tournament_cache, set_cache, get_cache_data
from bot_ui_models import dropdownView
# from bot import client, check #should probably have a config file for everything for setup


#First we get a list of tournaments that the user can join.
    #Since this information will not be changing that much we can cache it in the bot
    #We look for tournaments that were created in the server and and that are open
    #If that result is cached we will take it form there, if not we will make the 

discord.ext.commands

async def join_t(ctx,client): 

    
    if tournament_cache.get(ctx.guild.id) is None:

        r = requests.get(f'http://127.0.0.1:5556//returntournaments/{ctx.guild.id}')
        data = []

        if r.ok:
            #Create a list of discord.Select_Options
            #need to see that r has data. 
            for tournament in r.json():
                data.append(discord.SelectOption(label=f'{tournament["name"]}, Game: {tournament["game"]} Format: {tournament["format"]}', value=tournament["id"]))

            options_list = await set_cache(tournament_cache,ctx.guild.id,data)
            print(options_list)
            print(data)
        else:
            message = 'Cannot fetch tournaments'
    else:
        options_list = await get_cache_data(tournament_cache,ctx.guild.id)
    
    #Now create the dropdown items for the person to select from. 
 
    await ctx.send("",view=dropdownView(options=options_list), ephemeral=True)
    
    #Now check for interaction with the dropdown and then 


    def check_interaction(interaction):
        #Not sure if this will be a cause for issue but how can i be sure that the interaction is associated with the command that created it.  I tried a test where i use the testjoin command twice in a row without selecting a dropdown option. What ended up happening was that 1 dropdown selection was applied to both interactions. 
        #Maybe add an identifier to the dropdown class that we are creating and use that 
        #Or make a timeout where the user cannot use this command again 
        

        return interaction.user.id == ctx.author.id

    try:
        interaction = await client.wait_for('interaction', timeout=30.0, check=check_interaction)
         #check=check_interaction
        
        t_id = int(interaction.data["values"][0])

        #We have the id of the tournament we wish to join and now we have to actually join it.

        data = {
            'tournament_id' : t_id,
            'username': str(ctx.author),
            'discord_id': int(ctx.author.id)
        }

        headers = {'Content-Type': 'application/json'}
        r = requests.post(f'http://127.0.0.1:5556/JoinTournament/{t_id}', json=data)

        if r.ok:
            response = f'{ctx.author} sucessfully registerd for tournament name'
        else:
            if r.status_code == 403:
                response = f'Tournament is underway, unable to join'
            elif r.status_code == 409:
                response = f'{ctx.author} is already registered'
            else:
                response = f'Error, please try again. If error persists contact ___'
        
        await ctx.send(response)

    except asyncio.TimeoutError:
        await ctx.send('Timed out. Try again')

    