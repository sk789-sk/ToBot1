import requests
import asyncio


import discord 
from discord.ext import commands

from cache import *
#tournament_cache, set_cache, get_cache_data , start_cache_timer
from bot_ui_models import dropdownView


async def join_slash_t(interaction:discord.Interaction,client:commands.Bot): 
    if tournament_cache.get(interaction.guild_id) is None:
        status = 'Initialized'

        r = requests.get(f'http://127.0.0.1:5556//returntournaments/{interaction.guild_id}/{status}')
        data = []
        if r.ok:
            #Create a list of discord.Select_Options
            for tournament in r.json():
                data.append(discord.SelectOption(label=f'{tournament["name"]}   Game: {tournament["game"]}    Format:{tournament["format"]}', value=tournament["id"],description=tournament['name']))

            options_list = await set_cache(tournament_cache,interaction.guild_id,data)
            await start_cache_timer(tournament_cache,interaction.guild.id)

        else:
            await interaction.response.send_message("Cannot fetch tournaments, use prefix command with tournament id")
            return
    else:
        options_list = await get_cache_data(tournament_cache,interaction.guild_id)
    
    #Now create the dropdown items for the person to select from. 
 
    await interaction.response.send_message("",view=dropdownView(options=options_list), ephemeral=True)
    
    #Now check for interaction with the dropdown and then 

    try:
        interaction = await client.wait_for('interaction', timeout=30.0)
         #check=check_interaction
        t_id = int(interaction.data["values"][0])

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
            await interaction.response.send_message(response)
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


async def create_slash(interaction:discord.Interaction,client:commands.Bot, name, game, format): 

    data = {
        'name': name,
        'game': game,
        'format': format,
        'creator': interaction.user.id,
        'guild_id': interaction.guild_id
    }

    headers = {'Content-Type': 'application/json'}
    r = requests.post('http://127.0.0.1:5556/Create', json=data)
    
    if r.ok:
        response = f'Tournament Created Successfully'
        await reset_cache(tournament_cache,interaction.guild_id)

    else:
        response = f'Failed to create'
    
    await interaction.response.send_message(response)

async def drop_slash(interaction:discord.Interaction,client:commands.Bot):
    user_id = interaction.user.id 
    guild_id = interaction.guild_id

    r = requests.get(f'http://127.0.0.1:5556/joinedtournaments/{user_id}/{guild_id}')

    if r.ok:
        data = []
        for tournament in r.json():
            data.append(discord.SelectOption(label=f'{tournament["name"]}   Game: {tournament["game"]}    Format:{tournament["format"]}', value=tournament["id"],description=tournament['name']))

        await interaction.response.send_message("",view=dropdownView(options=data), ephemeral=True)
    
        try:
            interaction = await client.wait_for('interaction', timeout=30.0)

            t_id = int(interaction.data["values"][0])
            
            data = {
            'tournament_id' : t_id,
            'discord_id' : int(interaction.user.id)
            }

            headers = {'Content-Type': 'application/json'}
            r = requests.post(f'http://127.0.0.1:5556/Drop/{t_id}', json=data)

            if r.ok:
                response = f'{interaction.user.name} dropped sucessfully'
                await interaction.response.send_message(response)
            else:
                response = f'Error'
                await interaction.response.send_message(response,ephemeral=True)



        except asyncio.TimeoutError:
            await interaction.response.send_message('Timed out. Try again', ephemeral=True)
        
    else:
        message = 'Unable to fetch joined tournaments. Use prefix drop command with tournament id instead or try again'
        await interaction.response.send_message(message, ephemeral=True)

async def start_slash(interaction:discord.Interaction,client:commands.Bot):
    #Case where there are no tournaments needs to be added
    
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
            await interaction.response.send_message("Cannot fetch tournaments, use prefix command with tournament id")
    else:
        options_list = await get_cache_data(tournament_cache,interaction.guild_id)

    await interaction.response.send_message("",view=dropdownView(options=options_list), ephemeral=True)

    try:
        interaction = await client.wait_for('interaction', timeout=30.0)
        
        t_id = int(interaction.data["values"][0])
        
        r = requests.get(f'http://127.0.0.1:5556/start/{t_id}')

        if r.ok:
            data = r.json()

            await interaction.channel.send('Tournament Started, Pairings Generated')

            message = "Pairings for the tournament: \n"

            for match in data:

                try:

                    if match['player_2'] is not None:

                        P1 = match['player_1']['discord_id']
                        P2 = match['player_2']['discord_id'] if match['player_2'] else None


                        user_1 = await client.fetch_user(P1)
                        user_2 = await client.fetch_user(P2) #returns a class discord.User
                        
                        m1 = f'Your opponent is {user_2.name}'
                        m2 = f'Your opponent is {user_1.name}'

                        
                        await user_1.send(m1)
                        await user_2.send(m2)

                        message += f'\n{user_1.mention} vs. {user_2.mention}'
                    else:
                        P1 = match['player_1']['discord_id']
                        user_1 = await client.fetch_user(P1) 
                        m1 = f'You have a bye for the round'

                        await user_1.send(m1)
                        message += f'\n{user_1.mention} received a bye'
                
                except:                
                    await interaction.response.send_message('Error displaying matches, matches were created use DIFFERENT to show again')
        
            await interaction.response.send_message(message)
        else:
            await interaction.response.send_message('Tournament has already begun')


    except asyncio.TimeoutError:
        await interaction.response.send_message('Timed out. Try again', ephemeral=True)

async def loss_slash(interaction:discord.Interaction,client:commands.Bot):
    user_id = interaction.user.id 
    guild_id = interaction.guild_id

    r = requests.get(f'http://127.0.0.1:5556/joinedunderwaytournaments/{user_id}/{guild_id}')

    if r.ok:
        data = r.json()

        if len(data) == 0:
            await interaction.response.send_message(f'{interaction.user.name} is not in any active tournament', ephemeral=True)
            return
        
        elif len(data) == 1:
            t_id = data[0]['id']
            data = {
                'tournament_id' : t_id,
                'discord_id' : user_id
            }
        else:
            t_list = [discord.SelectOption(label=f'{tournament["name"]}', value=tournament['id'] ) for tournament in data]

            await interaction.response.send_message("", view=dropdownView(options=t_list), ephemeral=True)

            try:
                interaction = await client.wait_for('interaction', timeout=30.0)
                t_id = interaction.data["values"][0]

                data = {
                    'tournament_id': t_id,
                    'discord_id' : user_id
                }

            except asyncio.TimeoutError:
                await interaction.response.send_message("Timed out, please try again")
    else:
        await interaction.response.send_message("Unable to retreive tournaments, use prefix command or try again", ephemeral=True)
        return
    
    #Update Match on Database and provide feedback.

    r_update = requests.patch(f'http://127.0.0.1:5556/UpdateMatch', json=data)

    if r_update.ok:
        response = f'{interaction.user.name} loss reported sucessfully'
    elif r_update.status_code == 409:
        response = f'Match Result has already been reported'
    else:
        response = f'Error, please try again'
    
    await interaction.response.send_message(response)

async def next_round_slash(interaction:discord.Interaction,client:commands.Bot  ):
    guild_id = interaction.guild_id
    status = 'Underway'

    r = requests.get(f'http://127.0.0.1:5556//returntournaments/{guild_id}/{status}')
    
    if r.ok:
        data = r.json()

        if len(data) == 0:
            await interaction.response.send_message(f'{interaction.guild.name} has no tournaments underway. Use /start command if starting a tournament', ephemeral=True)
            return

        elif len(data) ==1:
            t_id = data[0]['id']
        else:
            t_list = [discord.SelectOption(label=f'{tournament["name"]}',value=tournament['id']) for tournament in data]
            await interaction.response.send_message("", view=dropdownView(options=t_list), ephemeral=True)

            try:
                interaction = await client.wait_for('interaction', timeout=30.0)
                t_id = interaction.data["values"][0]
            except asyncio.TimeoutError:
                await interaction.response.send_message("Timed out, please try again")
    else:
        await interaction.response.send_message('Issue retreiving tournament information, use prefix command or try again', ephemeral=True)
        return
    
    r_next_round = requests.get(f'http://127.0.0.1:5556/Generate_Matches/{t_id}')

    if r_next_round.ok:
        data = r_next_round.json()
        message = "Pairings for next round: \n"

        for match in data:
            try:

                if match['player_2'] is not None:

                    P1 = match['player_1']['discord_id']
                    P2 = match['player_2']['discord_id']

                    user_1 = await client.fetch_user(P1)
                    user_2 = await client.fetch_user(P2)

                    m1 = f'Your opponent is {user_2.name}'
                    m2 = f'Your opponent is {user_1.name}'

                    await user_1.send(m1)
                    await user_2.send(m2)

                    message += f'\n{user_1.mention} vs {user_2.mention}'
                else:
                    P1 = match['player_1']['discord_id']
                    user_1 = await client.fetch_user(P1)
                    m1 = f'You have a bye for the round'
                    await user_1.send(m1)
                    message += f'\n{user_1.mention} received a bye'
            
            except:
                await interaction.response.send_message('Error displaying matches', ephemeral=True)

        await interaction.response.send_message(message)
    else:
        if r_next_round.status_code == 409:
            data = r_next_round.json()

            message = "Awaiting the Results of the following Matches: \n"

            for match in data:
                P1 = match['player_1']['discord_id']
                P2 = match['player_2']['discord_id']

                user_1 = await client.fetch_user(P1)
                user_2 = await client.fetch_user(P2)

                message += f'\n {user_1.name} vs {user_2.name}'

            await interaction.response.send_message(message)
        
        else:
            await interaction.response.send_message('Error creating next round pairings, please try again')


async def end_slash(interaction:discord.Interaction,client:commands.Bot):
    guild_id = interaction.guild_id 
    status = 'Underway'
    
    r = requests.get(f'http://127.0.0.1:5556/returntournaments/{guild_id}/{status}')

    if r.ok:
        data = r.json()

        if len(data) == 0:
            await interaction.response.send_message(f'{interaction.guild.name} has no tournaments underway')
            return
        elif len(data) == 1:
            t_id = data[0]['id']
        else:
            t_list = [discord.SelectOption(label=f'{tournament["name"]}', value=tournament['id'] ) for tournament in data]

            await interaction.response.send_message("", view=dropdownView(options=t_list), ephemeral=True)            
            
            try:
                interaction = await client.wait_for('interaction', timeout=30.0)
                t_id = interaction.data["values"][0]

            except asyncio.TimeoutError:
                await interaction.response.send_message("Timed out, please try again")        
    else:
        await interaction.response.send_message("Unable to retreive tournaments, use prefix command or try again", ephemeral=True)
        return

    #Ending Tourney
    r_end = requests.get(f'http://127.0.0.1:5556/end/{t_id}')

    if r_end.ok:
        message = f'Results have been finalized, use /standing to view results'
    else:
        message = f'something went wrong'

    await interaction.response.send_message(message)


async def standings_slash():
    pass

