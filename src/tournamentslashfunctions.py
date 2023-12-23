import requests
import asyncio


import discord 
from discord.ext import commands

from cache import tournament_cache, set_cache, get_cache_data , start_cache_timer
from bot_ui_models import dropdownView


async def join_slash_t(interaction:discord.Interaction,client:commands.Bot): 
    if tournament_cache.get(interaction.guild_id) is None:
        r = requests.get(f'http://127.0.0.1:5556//returntournaments/{interaction.guild_id}')
        data = []
        if r.ok:
            #Create a list of discord.Select_Options
            for tournament in r.json():
                data.append(discord.SelectOption(label=f'{tournament["name"]}   Game: {tournament["game"]}    Format:{tournament["format"]}', value=tournament["id"],description=tournament['name']))

            options_list = await set_cache(tournament_cache,interaction.guild_id,data)
            await start_cache_timer(tournament_cache,interaction.guild.id)

        else:
            message = 'Cannot fetch tournaments'
    else:
        options_list = await get_cache_data(tournament_cache,interaction.guild_id)
    
    #Now create the dropdown items for the person to select from. 
 
    await interaction.response.send_message("",view=dropdownView(options=options_list), ephemeral=True)
    
    #Now check for interaction with the dropdown and then 

    try:
        interaction = await client.wait_for('interaction', timeout=30.0)
         #check=check_interaction
        print(interaction)

        t_id = int(interaction.data["values"][0])
        print(interaction.data)

        #We have the id of the tournament we wish to join and now we have to actually join it.

        data = {
            'tournament_id' : t_id,
            'username': interaction.user.name,
            'discord_id': interaction.user.id
        }

        headers = {'Content-Type': 'application/json'}
        r = requests.post(f'http://127.0.0.1:5556/JoinTournament/{t_id}', json=data)

        if r.ok:
            response = f'{interaction.user.name} sucessfully registerd for tournament name'
        else:
            if r.status_code == 403:
                response = f'Tournament is underway, unable to join'
            elif r.status_code == 409:
                response = f'{interaction.user.name} is already registered'
            else:
                response = f'Error, please try again. If error persists contact ___'
        
        await interaction.response.send_message(response, ephemeral=True)

    except asyncio.TimeoutError:
        await interaction.response.send_message('Timed out. Try again', ephemeral=True)


