import discord 
from discord.ext import commands
import random as rd
import requests 
import os
from dotenv import load_dotenv

# import BracketGen

#Create Tournament 
#Send Pairings to entrants
#send results to API

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True 

# client = discord.Client(intents=intents)


#So far this is just our connection to discord and we have set the message contents to true which allows us to use the events with messages. 

#Theres 2 ways to connect to discord here. client =  discord.Client is the websocket and has more flexibility.
# bot= commands.Bot(prefix,intents) then using @bot.command/event is an extension of the Client class, seems like it just has some common use cases built in and is just easier to use then. 

client = commands.Bot(command_prefix='$',intents=intents ,case_insensitive=True)



@client.event
async def on_ready():
    print(f'Logged in with {client.user}')
    #on_ready() is an event thats is within the client library and is called when the bot has logged in. 

@client.event
async def on_message(message):
    # print(message)
    # print(type(message.author))

    if message.author == client.user:
        return #do nothing on bot message to avoid recursion 
    
    if message.content.startswith('$h'):
        await message.channel.send('Hello!')

    #having the event for message and the command seems to conflict. seems like it prioritizes the message and then never gets to the command.
    # https://discordpy.readthedocs.io/en/latest/faq.html#why-does-on-message-make-my-commands-stop-working

    await client.process_commands(message)


    #my guess is that we send a message that has $h we will return hello work probable with $hhh?

    #Ok so this where the onmessage bit would occur. We define the messages and then what the
    #/enter, /createTournament, /createPairings, /Finalize etc., /endTourney  

 #TEST commands

@client.command()
async def ping(ctx):
    await ctx.send("pong")

@client.command()
async def RPS(ctx):
    #return an rock-paper-scissors value for 

    val = rd.choice(['rock', 'paper', 'scissors'])    
    await ctx.send(val)


@client.command()
async def copy(ctx, arg):
    await ctx.send(arg)




#Tournament Commands

@client.command()
async def create(ctx, name): #create tournament information
    #Create a Tournament, add in additional parameters, figure out how to make it as a dropdown step by step.

    data = {
        'name': name,
        'game': 'YGO',
        'format': 'Swiss',
        'creator': int(ctx.author.id)
    }

    headers = {'Content-Type': 'application/json'}
    r = requests.post('http://127.0.0.1:5556/Create', json=data)
    
    print(r.status_code)

    if r.ok:
        response = f'Tournament Created Successfully'
    else:
        response = f'Failed to create'
    
    await ctx.send(response)


@client.command()
async def join(ctx, t_id: int): #enter a tournament
    #1. enter a tournament given a tournament id.
    #2. If user already entered return feedback
    #3. If tournament has started do not enter and feedback
    #4. if failure inform

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
            print(match)

            print('line break')


            print(match['player_1'])

            P1 = match['player_1']['discord_id']
            P2 = match['player_2']['discord_id']


            user_1 = await client.fetch_user(P1)
            user_2 = await client.fetch_user(P2) #returns a class discord.User
            
            m1 = f'Your opponent is {user_2.name}'
            m2 = f'Your opponent is {user_1.name}'

            
            await user_1.send(m1)
            await user_2.send(m2)

            message += f'\n {user_1.mention} vs. {user_2.mention}'

            print(message)

        await ctx.send('Tournament Started, Pairings Generated')
    
        await ctx.send(message)
    else:

        await ctx.send('ERROR')
        "Tournament is already underway or some error creating matches provide feedback"

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

        message = "Pairings for the next round: \n"

        for match in data:

            
            P1 = match['player_1']['discord_id']
            P2 = match['player_2']['discord_id']

            user_1 = await client.fetch_user(P1)
            user_2 = await client.fetch_user(P2)

            m1 = f'Your opponent is {user_2.name}'
            m2 = f'Your opponent is {user_1.name}'

            await user_1.send(m1)
            await user_2.send(m2)

            message += f'\n {user_1.mention} vs {user_2.mention}'

        await ctx.send(message)
    else:
        await ctx.send('Error')

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






    


client.run(os.getenv('Disc_Token'))

