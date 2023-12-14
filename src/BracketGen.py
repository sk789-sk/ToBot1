import networkx as nx   
from itertools import combinations
import matplotlib.pyplot as plt

from flask import Flask, make_response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased
from sqlalchemy import or_

#local imports

from config import app, db
from models import Match , Entrant , Tournament

def CreateMatches(tourney_id):
    #given a graph of the tournament

    #For Now we will recreate the graph from the tournament records.

    #1. Get all the entrants 

    with app.app_context():
        entrants = Entrant.query.filter(Entrant.tournament_id==tourney_id,Entrant.dropped != True).all() 
    #2.Create the graph for creating matches. 

    G = nx.Graph()
    G.add_nodes_from(entrants)

    for pair in combinations(entrants,2):
        
        #If matching has already occured set the weight to -inf. 
        #This would also be another reason to store the graph itself in the database. 
        #We would recreate the graph when a user drops, aka remove the vertex and all edges involved with it(only for matchmaking).
        # 
        #  

        p1_opponents = list(pair[0].opponents)

        if pair[1].id in p1_opponents:
            G.add_edge(pair[0],pair[1],weight=-10000) 
            print('match seen')

        else:
            G.add_edge(pair[0],pair[1],weight=pair[0].point_total+pair[1].point_total)


    nx.draw(G, with_labels=True, font_weight='bold', node_color='skyblue', font_color='black', node_size=1000)
    plt.show()

    pairings = (nx.max_weight_matching(G,maxcardinality=True))

    #Add new matches to the database

    matches = []
    
    for pair in pairings:
        new_Match = Match(
            tournament = tourney_id,
            round = 1,
            player_1_id = pair[0].id,
            player_2_id = pair[1].id,
        )
        matches.append(new_Match)

    with app.app_context():
        db.session.add_all(matches)
        db.session.commit()

    return pairings




def BiPartiteMatchMaking(tourney_id):
    #matchmaking by bipartite matching, break sets of players into 2 groups for player 1 and player 2
    #Same logic as above to 

    with app.app_context():
        entrants = Entrant.query.filter(Entrant.tournament_id==tourney_id,Entrant.dropped !=True).all() #Entrant.dropped != True
        Tourney_info = Tournament.query.filter(Tournament.id == tourney_id).first()
        current_r = Tourney_info.current_round
        
        Tourney_info.current_round = current_r+1

    #2.Create the graph for creating matches. 

    matching_graph = nx.Graph()

    #split entrants into 2 groups

    A_set = entrants[len(entrants)//2:]
    B_set = entrants[:len(entrants)//2]

    matching_graph.add_nodes_from(A_set, bipartite = 0)
    matching_graph.add_nodes_from(B_set, bipartate = 1)

    #Add weights between all A and B 

    for entrant_a in A_set:
        print(entrant_a.opponents)
        for entrant_b in B_set:
            #If A and B have played each other set the weight to -inf, 
            #otherwise set the weight to be sum of the point totals 
            #add the edge

            if entrant_a.id in list(entrant_b.opponents):
                print(list(entrant_b.opponents))
                e_weight = -10000
            
            else:
                e_weight = entrant_a.point_total + entrant_b.point_total


            matching_graph.add_edge(entrant_a, entrant_b, weight = e_weight)
    #find the matching

    pairings = nx.max_weight_matching(matching_graph, maxcardinality=True)
    paired_entrants = set()

    matches = []    


    #Create Matches
    for pairing in pairings:
        #each pairing is a tuple which is hashable so im guessing the set will have tuples instead of individuals, 
        paired_entrants.update(pairing) 
        new_Match = Match(
            tournament = tourney_id,
            round = current_r+1,
            player_1_id = pairing[0].id,
            player_2_id = pairing[1].id,
        )
        matches.append(new_Match)

    #Create Match for unpaired if necessary
    if len(entrants)%2 !=0: 
        unmatched = set(entrants).difference(paired_entrants) 
        val = unmatched.pop()

        new_Match = Match(
            tournament = tourney_id,
            round = current_r+1,
            player_1_id = val.id,
            player_2_id = None,
            result = val.id
        )

        #Update the entrant to also have bye listed in their name.

        matches.append(new_Match)
    
    # for pair in pairings:
    #     new_Match = Match(
    #         tournament = tourney_id,
    #         round = 1,
    #         player_1_id = pair[0].id,
    #         player_2_id = pair[1].id,
    #     )
    #     matches.append(new_Match)
    
    #update database
    match_list = []
    with app.app_context():

        try:
            db.session.add_all(matches)
            db.session.add(Tourney_info)
            db.session.commit()
            
            for match in matches:
                match_list.append(match.to_dict())
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f'Error {e} has occured')
            response = make_response({'error': 'Failed to create Matches'}, 500)


    return match_list

# BiPartiteMatchMaking(1)


def startTournament(tourney_id):
    #Start the tournament which would then create the initial matches.
    #We pass in a list of entrants and create the initial graph
    #would it be better to just have this only make the matches and leave all database related things to be passed into it. Instead of giving it an ID instead we would pass it a graph 

    tourney_graph = nx.Graph() 
    
    #1. First get the entrants in the tournament
    with app.app_context():
        entrants = Entrant.query.filter(Entrant.tournament_id==tourney_id).all()
        tourney_info = Tournament.query.filter(Tournament.id == tourney_id).first()


    
    #2. Add the entrants to the tournament
    
    tourney_graph = nx.Graph() 
    tourney_graph.add_nodes_from(entrants)

    #shuffle entrants as well

    all_pairings = []

    for pair in combinations(entrants,2):
        tourney_graph.add_edge(pair[0],pair[1],weight=pair[0].point_total+pair[1].point_total)
        
        all_pairings.append(pair)

    pairings = (nx.maximal_matching(tourney_graph))    

    #4. We have the pairings and now we need to turn them into match objects to store in the database. Extract the information from the Entrant

    matches = []
    match_list = []

    paired_entrants = set()

    for pair in pairings:
        new_Match = Match(
            tournament = tourney_id,
            round = 1,
            player_1_id = pair[0].id,
            player_2_id = pair[1].id,
        )
        matches.append(new_Match)
        paired_entrants.update(pair)

        # print(new_Match)

    if len(entrants)%2 !=0:

        print(set(entrants))
        print(paired_entrants)

        unmatched = set(entrants).difference(paired_entrants)
        
        
        print(unmatched)

        val = unmatched.pop()

        new_Match = Match(
            tournament = tourney_id,
            round = 1,
            player_1_id = val.id,
            player_2_id = None,
            result = val.id
        )
        matches.append(new_Match)
    
    tourney_info.current_round = 1

    with app.app_context():

        try:
            db.session.add_all(matches)
            db.session.add(tourney_info)
            db.session.commit()
            

            for match in matches:
                match_list.append(match.to_dict())


        except SQLAlchemyError as e:
            db.session.rollback()
            print(f'Error {e} has occured')
            response = make_response({'error': 'Failed to create Matches'}, 500)

        except ValueError as ve:
            print(f'Error {ve} has occured')
            

    return match_list

def add_Match_Result(match_id, loser_id): #NOT USED
    #update match result, update player point total, update edge weight for games already done

    with app.app_context():
        match = Match.query.filter(Match.id==match_id).first()
        entrant_1 = Entrant.query.filter(match.player_1==Entrant.id).first()
        entrant_2 = Entrant.query.filter(match.player_2==Entrant.id).first()

        entrant_2.opponents += f"{entrant_1.id},"
        entrant_1.opponents += f"{entrant_2.id},"
        
    if loser_id == match.player_1:
        match.result = match.player_2
        entrant_2.point_total +=3

    elif loser_id == match.player_2:
        match.result = match.player_1
        entrant_1.point_total +=3

    else:
        match.result = 0 
        entrant_1.point_total +=1
        entrant_2.point_total +=1
    
    with app.app_context():
        # db.session.add(match)
        db.session.add_all([match,entrant_1,entrant_2])
        db.session.commit()
    return 


def FinalizeResults(tournament_id):
    #1. Set the tournament status to completed
    #2. Create the Tiebreaker Calculations, SOS, Bucholz, H2H,

    with app.app_context():

        entrants = Entrant.query.filter(Entrant.tournament_id==tournament_id).all()


    entrant_dict = {}
    for entrant in entrants:
        entrant_dict[entrant.id] = entrant

    print(entrant_dict)
    print(entrant_dict[2].opponents)
    print(len(entrant_dict[2].opponents))

    #Determine SOS we should store calculated values in a hash to avoid recalculation since theres going to be many repeat values. 
    #Win = 1, tie = 1/3 win, loss = 0 win. This also makes it so it weights someone with wins > ties i beleive
    SOS_dict = {}

    updated_entrants = []

    for entrant in entrants:
        wins_e,games_e = 0,0

        print(list(entrant.opponents.split(',')))
        for opponent in list(entrant.opponents.split(',')):
            if opponent.isdigit():

                if opponent in SOS_dict:
                    wins_e += SOS_dict[opponent][0]
                    games_e += SOS_dict[opponent][1]
                else:

                    #this is with the idea the entrants are stored as a dictionary instead of an array to access them. We already have all the entrants we dont want to get it again from the DB for no reason. 
                    # print(type(opponent))
                    # print(entrant_dict[2])

                    games = len(entrant_dict[int(opponent)].opponents) #not accurate since this is a fkn string. 
                    wins = (entrant_dict[int(opponent)].point_total)/games
                    SOS_dict[int(opponent)] = (wins,games)
                    wins_e += wins
                    games_e += games
            else:
                continue

        entrant.SOS = wins_e/games_e

        updated_entrants.append(entrant)

    with app.app_context():
        db.session.add_all(updated_entrants)
        db.session.commit()

def CreateStandings(tournament_id):

    with app.app_context():

        ordered_entrants = Entrant.query.filter(Entrant.tournament_id==tournament_id).order_by(Entrant.point_total).order_by(Entrant.SOS).all()


        print(ordered_entrants)


        
def testouter(t_id,disc_id):



    with app.app_context():

        entrant_1_alias = aliased(Entrant)
        entrant_2_alias = aliased(Entrant)

        t_round = Tournament.query.filter(Tournament.id == t_id).first().current_round

        print(t_round)

        match = db.session.query(Match).outerjoin(entrant_1_alias, Match.player_1_id==entrant_1_alias.id ).outerjoin(entrant_2_alias, Match.player_2_id==entrant_2_alias.id).filter(or_(entrant_1_alias.discord_id==disc_id,entrant_2_alias.discord_id==disc_id),Match.round==t_round).all()

        #, entrant_1_alias, entrant_2_alias 
            
        print(match)


        # print(match[0].player_1_id.discord_id)


# FinalizeResults(1)

if __name__ == "__main__":
    BiPartiteMatchMaking(1)
    pass