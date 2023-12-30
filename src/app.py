from models import *
from flask import Flask, make_response, jsonify, request, session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased
from sqlalchemy import or_
import os

# Local imports

from config import app, db
from models import Match , Entrant , Tournament
from BracketGen import startTournament_Swiss, BiPartiteMatchMaking , FinalizeResults , CreateStandings , startSingleElim



@app.route('/')
def home():
    return 'testing base'


@app.route('/Create', methods = ['POST'])
def create():
    
    data = request.get_json()
    print(data)
    
    try:
        #reqbin test was good
        new_tournament = Tournament(
            name = data['name'],
            game = data['game'],
            format = data['format'],
            creator = data['creator'],
            status = 'Initialized',
            guild_id = data['guild_id']
        )
        
        db.session.add(new_tournament)
        db.session.commit()

        response = make_response(new_tournament.to_dict(),200)
    
    except ValueError:
        response = make_response({"Errors":["Failed to create"]},400)

    return response

@app.route('/JoinTournament/<int:t_id>', methods = ['POST'])
def Join_Tournament(t_id):

    data = request.get_json()
    tournament_status = Tournament.query.filter(Tournament.id==t_id).first().status
    entered_status = Entrant.query.filter(Entrant.tournament_id==t_id,Entrant.discord_id==data['discord_id']).first()

    if request.method == 'POST':
        
        if tournament_status == 'Underway':
            response = make_response({},403)
            print('Tournament underway, can no longer enter')

        elif entered_status:
            response = make_response({}, 409)
            print('User already entered')

        else:
             
            try:
                new_Entrant = Entrant(
                    tournament_id = t_id,
                    point_total = 0,
                    opponents = [],
                    pair_up_down = None,
                    bye = 0,
                    SOS = None,
                    dropped = None,
                    username = data['username'],
                    discord_id = data['discord_id']
                )

                db.session.add(new_Entrant)
                db.session.commit()

                response = make_response(jsonify(new_Entrant.to_dict()),200)

            except SQLAlchemyError as e:
                    db.session.rollback()
                    print(f'Error {e} occured')
                    response = make_response({'error': 'Failed to create entrant'}, 500)
                    
            except ValueError as ve:
                    response = make_response({},400)
                    print(f'Error: {ve}')
    
    else:
            #DELETE
            print('delete')

    return response

@app.route('/Drop/<int:t_id>', methods = ['POST'])
def drop_entrant(t_id):
     #1. If the tournament is underway change status to dropped
     #2. If the tournament has not yet begun delete them
     #3. If tournament is in other status, finalized etc do not allow edits
     #3. Info given is the users discord_id
     

    data = request.get_json()
    tournament_status = Tournament.query.filter(Tournament.id==t_id).first().status
    entrant = Entrant.query.filter(Entrant.tournament_id==t_id,Entrant.discord_id==data['discord_id']).first_or_404()
    
    if tournament_status == 'Underway':
        entrant.dropped = True
        try:            
            db.session.add(entrant)
            db.session.commit()
            response = make_response({},202)
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f'Error {e} occured')
            response = make_response({'error': 'Failed to drop'}, 500)

    elif tournament_status == 'Initialized':
        try:
            db.session.delete(entrant)
            db.session.commit()
            response = make_response({},204)
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f'Error {e} occured')
            response = make_response({'error': 'Failed to delete'}, 500)
    else:
        response = make_response({'Error':'Cannot Modify'},403) #cannot modify resource anymore
 

    return response


@app.route('/start/<int:t_id>')
def start_tournament(t_id):

    t = Tournament.query.filter(Tournament.id==t_id).first()

    if t.status == 'Initialized':
        print(t.format)
        if t.format in ['Swiss','Round Robin']:
            try:
                matches = startTournament_Swiss(t_id)   
                response = make_response(jsonify(matches),200)
            except SQLAlchemyError as e:
                db.session.rollback()
                print(f'Error {e} has occured')
                response = make_response({'error': 'Failed to start'}, 500)

        elif t.format == 'Single Elimination':
            try:
                matches = startSingleElim(t_id)

                response = make_response(jsonify(matches),200)
            except SQLAlchemyError as e:
                db.session.rollback()
                print(f'Error {e} has occured')
                response = make_response({'error':'failed to start'},500)
        else:
            response = make_response({'Error':'Chosen format not supported'},501)
    else:
        response = make_response({},403) #tournament is underway or completed
    
    return response

@app.route('/UpdateMatch' , methods = ['PATCH'])   #this is really report loss
def updateMatch():
    
    data = request.get_json() #I am given the tournament id and the discord_id here

    entrant_1_alias = aliased(Entrant)
    entrant_2_alias = aliased(Entrant)

    tournament = Tournament.query.filter(Tournament.id == data['tournament_id']).first()

    t_round = tournament.current_round

    print(tournament.format)

    if tournament.format in ['Swiss','Round Robin']:
        #Create functions for this bit i think
                
        match = db.session.query(Match).outerjoin(entrant_1_alias, Match.player_1_id==entrant_1_alias.id ).outerjoin(entrant_2_alias, Match.player_2_id==entrant_2_alias.id).filter(or_(entrant_1_alias.discord_id==data['discord_id'],entrant_2_alias.discord_id==data['discord_id']),Match.round==t_round,Match.tournament==tournament.id).first()
        
        print('???')

        if match:
        #we have a match now lets update the match results. We pass the ID of the 
            if match.result == None:

                entrant_1 = Entrant.query.filter(match.player_1_id==Entrant.id).first()
                entrant_2 = Entrant.query.filter(match.player_2_id==Entrant.id).first()
                
                entrant_2.opponents.append(entrant_1.id)
                entrant_1.opponents.append(entrant_2.id)            

                #2 cases player_1 loss or player_2
                if match.player_1.discord_id == data['discord_id']: # player 1 has lost
                    match.result = match.player_2_id #update match result
                    entrant_2.point_total +=3

                else: #player 2 has lost
                    match.result = match.player_1_id
                    entrant_1.point_total +=3

                try:
                    db.session.add_all([match,entrant_1,entrant_2])
                    db.session.commit()
                    
                    response = make_response({},204)
                except SQLAlchemyError as e:
                    db.session.rollback()
                    print(f'Error {e} has occured')
                    response = make_response({'error': 'Server Error failed to update'},304)
                except ValueError as ve:
                    db.session.rollback
                    print(f'Error {ve} has occured')
                    response = make_response({'Error':'Bad Data'},422)
            else:
                response = make_response({'Error':'Already Reported'},409)
        else:
            response = make_response({'Error': 'Player is not in an active match'},400)

    if tournament.format in ['Single Elimination','Double Elimination']:
        
        match = db.session.query(Match).outerjoin(entrant_1_alias, Match.player_1_id==entrant_1_alias.id ).outerjoin(entrant_2_alias, Match.player_2_id==entrant_2_alias.id).filter(Match.tournament == tournament.id, or_(entrant_1_alias.discord_id==data['discord_id'],entrant_2_alias.discord_id==data['discord_id']),Match.result==None,Match.player_1_id!=None,Match.player_2_id!=None).first()

        #Match where the person reporting is a participant, the result has not been reported and there are 2 players. I dont think that really matters the 2 players since it is a loser report system

        #double Elim would have a losers next match as well potentially. 

        print('hahaxd')

        print(match)

        if match:
            #we have a match now lets update the match results. We pass the ID of the 
            if match.result == None:

                entrant_1 = Entrant.query.filter(match.player_1_id==Entrant.id).first()
                entrant_2 = Entrant.query.filter(match.player_2_id==Entrant.id).first()
                
                #The finals has no winners next match also. 

                winners_next_match = Match.query.filter(Match.id==match.winner_next_match_id).first()
                
                #this whole bit with the if/else has a better solution im sure

                #2 cases player_1 loss or player_2
                if match.player_1.discord_id == data['discord_id']: # player 1 has lost
                    match.result = match.player_2_id #update match result
                    
                    if winners_next_match:

                        if winners_next_match.player_1_id == None:
                            winners_next_match.player_1_id = match.player_2_id
                        else:
                            winners_next_match.player_2_id = match.player_2_id

                else: #player 2 has lost
                    match.result = match.player_1_id

                    if winners_next_match:

                        if winners_next_match.player_1_id == None:
                            winners_next_match.player_1_id = match.player_1_id
                        else:
                            winners_next_match.player_2_id = match.player_1_id

                try:
                    # db.session.add_all([match,entrant_1,entrant_2,winners_next_match])
                    # db.session.commit()

                    if winners_next_match:
                        db.session.add_all([match,entrant_1,entrant_2,winners_next_match])
                        db.session.commit()
                        response = make_response(jsonify(winners_next_match.to_dict()),200)
                    else:
                        db.session.add_all([match,entrant_1,entrant_2])
                        db.session.commit()
                        response = make_response({},201)
                except SQLAlchemyError as e:
                    db.session.rollback()
                    print(f'Error {e} has occured')
                    response = make_response({'error': 'Server Error failed to update'},304)
                except ValueError as ve:
                    db.session.rollback
                    print(f'Error {ve} has occured')
                    response = make_response({'Error':'Bad Data'},422)
            else:
                response = make_response({'Error':'Already Reported'},409)
        else:
            response = make_response({'Error': 'Player is not in an active match'},400)

    return response

@app.route('/Generate_Matches/<int:t_id>')
def generate_matches(t_id):
    #. Verify that all matches are completed, if not say we are awaiting matches

    tourney = Tournament.query.filter(Tournament.id == t_id).first()
    round_check = tourney.current_round 

    unfinished_matches = Match.query.filter(Match.tournament==t_id,Match.round==round_check,Match.result==None).all()

    if len(unfinished_matches) !=0:
        #return the matchs that need to be finished
        unfinished_match_list = []
        for match in unfinished_matches:
            unfinished_match_list.append(match.to_dict())

        response = make_response(jsonify(unfinished_match_list),409)

    #. There are no unfinished matches so we run the function to create the next set of matches. the function also updates the tournament state. Need to add error handling for this Bipartite Function

    else:

        #check if there ar any more rounds:

        if round_check < tourney.total_round:
            matches = BiPartiteMatchMaking(t_id) 
            response = make_response(jsonify(matches),200)
        else:
            response = make_response({},418)
    
    return response

@app.route('/end/<int:t_id>')
def end(t_id):

    unfinished_matchlist = Match.query.filter(Match.tournament == t_id,Match.result == None).all()
    
    if len(unfinished_matchlist) > 0:
        unfinished_list = []
        for match in unfinished_matchlist:
            unfinished_list.append(match.to_dict())

        response = make_response({jsonify(unfinished_list)},409)

    else:
        response = FinalizeResults(t_id)

    return response





@app.route('/Standings/<int:t_id>', methods=['GET','POST'])
def get_standings(t_id):

#     data = {
#     "tournament_id": 123,
#     "filter_parameters": []
# }
    
    if request.method == 'GET':
        
        standings_list = []

        standings = CreateStandings(t_id)
        
        for player in standings:
            standings_list.append(player.to_dict())

        response = make_response(jsonify(standings_list),200)

    elif request.method =='POST':

        data = request.get_json()
        
        standings = CreateStandings(t_id, *data['filter_parameters'])
        print(standings)
        standings_list = []

        for player in standings:
            standings_list.append(player.to_dict())

        response = make_response(jsonify(standings_list),200)

    #this only works in 3.7+ where dictionary key insertions are kept in order

    return response

@app.route('/joinedtournaments/<int:user_id>/<int:guild_id>')
def return_joined_inGuild(user_id,guild_id):

    joined_tournaments = db.session.query(Tournament).join(Entrant, Entrant.tournament_id==Tournament.id).filter(Entrant.discord_id==user_id,Tournament.status != 'Finalized',Tournament.guild_id==guild_id).all()

    tournament_list = [tournament.to_dict() for tournament in joined_tournaments]

    response = make_response(jsonify(tournament_list),200)
    return response

@app.route('/joinedunderwaytournaments/<int:user_id>/<int:guild_id>')
def return_joined_underway_inGuild(user_id,guild_id):

    joined_tournaments = db.session.query(Tournament).join(Entrant, Entrant.tournament_id==Tournament.id).filter(Entrant.discord_id==user_id,Tournament.status == 'Underway',Tournament.guild_id==guild_id).all()

    tournament_list = [tournament.to_dict() for tournament in joined_tournaments]

    response = make_response(jsonify(tournament_list),200)
    return response
 

@app.route('/returntournaments/<int:guild_id>/<string:status>')
def guilds_tournaments(guild_id,status):

    init_tournaments = Tournament.query.filter(Tournament.guild_id==guild_id,Tournament.status==status).all()

    tournament_list = [tournament.to_dict() for tournament in init_tournaments]

    response = make_response(jsonify(tournament_list),200)
    return response

@app.route('/returnMatches/<int:t_id>')
def return_all(t_id):
    matches = Match.query.filter(Match.tournament==t_id).all()
    match_list = []
    for match in matches:
        match_list.append(match.to_dict())

    response = make_response(jsonify(match_list),200)
    return response 

@app.route('/returnEntrants/<int:t_id>')
def returnEntrants(t_id):

    #We get a tournament id, from the tournament ID we look at all entrants in a tournament with that id

    entrants = Entrant.query.filter(Entrant.tournament_id==t_id).all()

    entrant_list = []

    for entrant in entrants:
        entrant_list.append(entrant.to_dict())

    response = make_response(jsonify(entrant_list),200)
    return response
if __name__ == '__main__':

    app.run(port=5556, debug=True) 
