import random as rd
import requests 
import os
import asyncio 

import discord 
from discord.ext import commands
from dotenv import load_dotenv

from botHelperfunctions import create_table
from cache import tournament_cache, set_cache

from wip_bot_commands import join_t
from tournamentslashfunctions import * 


load_dotenv()


intents = discord.Intents.default()
intents.message_content = True 

#defaults 
default_timeout = 15.0



# client = discord.Client(intents=intents)


#So far this is just our connection to discord and we have set the message contents to true which allows us to use the events with messages. 

#Theres 2 ways to connect to discord here. client =  discord.Client is the websocket and has more flexibility.
# bot= commands.Bot(prefix,intents) then using @bot.command/event is an extension of the Client class, seems like it just has some common use cases built in and is just easier to use then. 

#Slash commands use interactions, prefix commands use context

client = commands.Bot(command_prefix='$',intents=intents ,case_insensitive=True)



@client.event
async def on_ready():
    print(f'Logged in with {client.user}')

    try:
        synched = await client.tree.sync()
        print(f"synched with {len(synched)} commands")
    except Exception as e:
        print(e)

    #Test slash commands
    test_guild = 1178775700573012038

@client.tree.command(name='hello')
async def hello(interaction:discord.Interaction):
    await interaction.response.send_message("hello!", ephemeral=True)

@client.tree.command(name='rps')
async def rps(interaction:discord.Interaction):
    val = rd.choice(['rock', 'paper', 'scissors'])    
    await interaction.response.send_message(val, ephemeral=True)


@client.tree.command(name='join_slash',description='Join a tournament')
async def joinslasht(interaction:discord.Interaction):
    await join_slash_t(interaction,client)

@client.tree.command(name='create', description='Create a tournament')
async def createslasht(interaction:discord.Interaction, name: str, game: str, format: str='Swiss'):
    await create_slash(interaction,client, name, game , format )
    
@client.tree.command(name='drop', description='Drop from a tournament')
async def dropslash(interaction:discord.Interaction):
    await drop_slash(interaction,client)

@client.tree.command(name='start', description='Start a tournament')
async def startslash(interaction:discord.Interaction):
    await start_slash(interaction,client)

@client.tree.command(name='loss', description='Report a loss')
async def lossslash(interaction:discord.Interaction):
    await loss_slash(interaction,client)

@client.tree.command(name='next_round', description='Start the next round')
async def nextroundslash(interaction:discord.Interaction):
    await next_round_slash(interaction,client)

@client.tree.command(name='end', description='End a tournament')
async def endslash(interaction:discord.Interaction):
    await end_slash(interaction,client)

@client.tree.command(name='standings', description='Get the Standings')
async def standingslash(interaction:discord.Interaction):
    await standings_slash(interaction,client)






@client.event
async def on_message(message):

    if message.author == client.user:
        return #do nothing on bot message to avoid recursion 
    
    if message.content.startswith('$h'):
        await message.channel.send('Hello!')
    await client.process_commands(message)
    

####################### PREFIX COMMANDS #####################################
    
###TEST COMMANDS ###
@client.command()
async def ping(ctx):
    await ctx.send("pong")

@client.command()
async def RPS_t(ctx):
    val = rd.choice(['rock', 'paper', 'scissors'])    
    await ctx.send(val, ephemeral=True)

@client.command()
async def copy(ctx, arg):
    await ctx.send(arg)

###Tournament Commands ###

@client.command()
async def create(ctx, name): 
    #create tournament information
    #Create a Tournament, add in additional parameters, figure out how to make it as a dropdown step by step.
    #Delete tournament cache

    data = {
        'name': name,
        'game': 'YGO',
        'format': 'Swiss',
        'creator': int(ctx.author.id),
        'guild_id': int(ctx.guild.id)
    }

    headers = {'Content-Type': 'application/json'}
    r = requests.post('http://127.0.0.1:5556/Create', json=data)
    
    if r.ok:
        response = f'Tournament Created Successfully'
        tournament_cache[ctx.guild.id] = None

    else:
        response = f'Failed to create'
    
    await ctx.send(response)


@client.command()
async def join_by_id(ctx, t_id: int):     
    #join w/ database id, shouldnt be used i think
    data = {
        'tournament_id' : t_id,
        'username': str(ctx.author),
        'discord_id': int(ctx.author.id)
    }

    headers = {'Content-Type': 'application/json'}
    r = requests.post(f'http://127.0.0.1:5556/JoinTournament/{t_id}', json=data)

    if r.ok:
        response = f'{ctx.author} registered successfully'
    else:
        if r.status_code == 403: 
            response = f'Tournament is underway, unable to join'
        elif r.status_code == 409:
            response = f'{ctx.author} is already registered'
        else:
            response =f'Error, please try again'
    
    await ctx.send(response)

@client.command()
async def drop(ctx, t_id:int): #drop from a tournament information
    #if tournament is underway change player status to dropped
    #if tournament has not started remove them from the entrants 
    #delete an entrant from a tournament
    #return a confirmation that the delete occured

    data = {
        'tournament_id' : t_id,
        'discord_id' : int(ctx.author.id)
    }

    headers = {'Content-Type': 'application/json'}
    r = requests.post(f'http://127.0.0.1:5556/Drop/{t_id}', json=data)

    if r.ok:
        response = f'{ctx.author} dropped sucessfully'
    else:
        if r.status_code == 403:
            response = f'Entrants can no longer be modified'
        else:
            response = f'Error, please try again or check if registered'
    
    await ctx.send(response)


@client.command()
async def start(ctx, t_id:int):
    #start a tournament
    #Send a reqeust to the server to start the tournament
    #Server will then send back a list of matches
    #Bot will then message the people in the matches that Tournament is underway and that your opponent is username. 

    r = requests.get(f'http://127.0.0.1:5556/start/{t_id}')

    #Ok we get back a list of tournaments
    if r.ok:

        data = r.json()

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
                await ctx.send('Error displaying matches')

        await ctx.send('Tournament Started, Pairings Generated')
    
        await ctx.send(message)
    else:
        await ctx.send('Tournament has already begun')
  

@client.command()
async def loss(ctx, t_id): #report a loss,
    #I have a user id
#     We have a user use the /command

# /command tourney id, in the case of multiple tournaments

# From that we have the context which gives me the users_id. 
# From the users_id we need to extract which match they are playing.

# SQL to search for the Match where Entrant(join)discord_id matches the the id we get back from the bot and the tournament id.

# From that we have the match id and the entrant id.
 
# From there we can use the match_id one that we have from before. 

    data = {
        'tournament_id' : t_id,
        'discord_id' : int(ctx.author.id)
    }

    headers = {'Content-Type': 'application/json'}
    r = requests.patch(f'http://127.0.0.1:5556/UpdateMatch', json=data)

    if r.ok:
        response = f'{ctx.author} loss reported sucessfully'
    else:
        if r.status_code == 400:
            response = f'{ctx.author} is not in an active match for the tournament'
        elif r.status_code == 409:
            response = f'Match Result has already been reported'
        else:
            response = f'Error, please try again'
    
    await ctx.send(response)

@client.command()
async def draw(ctx, t_id): 
    #In the case of a draw, it would want both players to accept a draw.
    pass

@client.command()
async def next_round(ctx, t_id):
    #Create the pairings for the next round. 

    #Send a request to the server to get the next round.
    #Server will
        # Verify that all matches are complete for the previous round.
        #If all matches are done we 
        # - create the pairings for the next round
        # - Update tournament status to the new round
        # - Post the pairings to the database
        # - Return pairings to the bot
    #Bot will then
    # - Message Entrants with their opponent. 
    # - Post the pairings in channel by @'s

    r = requests.get(f'http://127.0.0.1:5556/Generate_Matches/{t_id}')

    if r.ok:
        data = r.json()

        print(data)

        message = "Pairings for the next round: \n"

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

                await ctx.send('Error displaying matches')

        

    else:
        if r.status_code == 409: #still have ongoing matches
            data = r.json()

            message = "Awaiting the Results of the following Matches: \n"

            for match in data:
                P1 = match['player_1']['discord_id']
                P2 = match['player_2']['discord_id']

                user_1 = await client.fetch_user(P1)
                user_2 = await client.fetch_user(P2)

                message += f'\n {user_1.name} vs {user_2.name}'

    await ctx.send(message)

@client.command()
async def end(ctx, t_id):
    #Finish the tournament 

    #Send a request to the server to end the tournament
    #Server will
        #Verify that all the matches are completed
        #Change the tournament staus to finalized. 
        #Calculate all SOS and other tiebreaker metrics
        #Send feedback the bot that it has been calculated
    #Bot
        #Message that the tournament is now concluded.
        #Display the standings maybe*

    r = requests.get(f'http://127.0.0.1:5556/end/{t_id}')

    if r.ok:
        message = f'Results have been finalized'
    else:
        message = f'something went wrong'

    await ctx.send(message)
    pass


@client.command()
async def standing(ctx, t_id:int): #optional top N people display top N

    #Display standings of the tournament. If the tournament is ongoing it sorts by point value, If tournament is concluded then it sorts with tiebreaker metrics as well. 

    #Send a request to the server for standings information 
    #Request may include tiebreaker criteria, default to SOS(Matched komani's tiebreaker method ) or bucholz
    #Server will:
        #Send back an order list of standing based on the criteria
    #Bot will
        #Display the standings in channel
    
    prompt = await ctx.send(
        "Select Ranking Criteria: \n"
        "1. Konami standard (Points/SOS/SOSOS) \n"
        "2. Points, BucholzCut1, Median-Bucholz \n"
        "3. Custom \n"

        "Note: On-Going tournaments will only sort by points, tiebreakers are calculated when all matches are finished"
    )


    #Check function for wait_for to make it respond only to user

    def check(message):
        return message.author == ctx.author and ctx.channel==message.channel

    #get a response to the prompt
    try:
        response = await client.wait_for('message', timeout=default_timeout, check=check)


    except asyncio.TimeoutError:
        await ctx.send('Timed out. Try again')

    #use the users response to ge the logic. 
    #discord limit of 2000 characters

    if response.content.strip() == '1':
        r = requests.get(f'http://127.0.0.1:5556/Standings/{t_id}')
       
        if r.ok:
            data = r.json()
            message = create_table(r.json(),header= ['Rank', 'Player', 'Points', 'Opp Win %','Opp Opps Win %'],tiebreaker_metrics=['SOS','SOSOS'])
            await ctx.send(f'```\n{message}\n```')
        
        else:
            message = 'Issue retreiving tournament results'
    
    elif response.content.strip() =='2':
        
        data = {
            'tournament' : t_id,
            'filter_parameters' : ['BucholzCut1','medianBucholz']
        }
        
        r = requests.post(f'http://127.0.0.1:5556/Standings/{t_id}', json=data)
        if r.ok:
            message = create_table(r.json(),header= ['Rank', 'Player', 'Points', 'BucholzCut1','medianBucholz'],tiebreaker_metrics=['BucholzCut1','medianBucholz'])
            await ctx.send(f'```\n{message}\n```')
        else:
            message = 'Issue retreiving tournament results'
    
    elif response.content.strip() =='3':
    
        filters_dict = {
            '1':'SOS',
            '2':'SOSOS',
            '3':'BucholzCut1',
            '4':'medianBucholz',
            '5':'Bucholz'
        }
    
        await ctx.send("Select minimum of 2: \n" "1. SOS \n" "2. SOSOS \n" "3. BucholzCut1 \n" "4. medianBucholz \n" "5. Bucholz \n""Ex: 1,3,4,5 " )
        try:
            response = await client.wait_for('message', timeout=default_timeout, check=check)
        except asyncio.TimeoutError:
            await ctx.send('Timed out. Try again')
        
        try:
            selected_filters = [filters_dict[id] for id in response.content.strip().split(",")]
            data = {
            'tournament' : t_id,
            'filter_parameters' : selected_filters
            }
        
            r = requests.post(f'http://127.0.0.1:5556/Standings/{t_id}', json=data)
            if r.ok:
                message = create_table(r.json(),header= ['Rank', 'Player', 'Points', selected_filters[0],selected_filters[1]],tiebreaker_metrics=selected_filters)
                await ctx.send(f'```\n{message}\nIf more than 2 metrics were selected only the first 2 values are displayed for formatting```')
            else:
                message = 'Issue retreiving tournament results'
        except:
            await ctx.send('Invalid inputs.')

    else:
        print('invalid response')

    pass 




#QOL commands 




@client.command()
async def entrants(ctx): #view tournament information
    r = requests.get('http://127.0.0.1:5556/returnEntrants/1')
    
    await ctx.send(r.text)

@client.command()
async def info(ctx, t_id:int):
    #request the tournament info from the API
    #return the Basic info, entrant count, status, etc
    pass

@client.command()
async def waiting(ctx, t_id:int):
    #request the matches that are still ongoing
    #Server will:
    #   - Return all matches in the current tournament and round that have null result, so no loss reported.
    #Bot will:
    #   -display these matches in the same format that used to initially display the matches. This will not mention. 
    pass


#Testing_ground

@client.command()
async def join(ctx,client=client):

    await join_t(ctx,client=client)


    


client.run(os.getenv('Disc_Token'))

