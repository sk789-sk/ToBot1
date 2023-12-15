import networkx as nx   
from itertools import combinations
from collections import defaultdict
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
    update_obj_list = []
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
        update_obj_list.append(new_Match)

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
        matches.append(new_Match)

        #Update the entrant w/ bye points to also have bye listed in their name.
        
        val.point_total +=3
        val.bye = True 

        update_obj_list.append(val)
        

    # for pair in pairings:
    #     new_Match = Match(
    #         tournament = tourney_id,
    #         round = 1,
    #         player_1_id = pair[0].id,
    #         player_2_id = pair[1].id,
    #     )
    #     matches.append(new_Match)
    
    #update database
    print('haha')
    print(update_obj_list)
    print('hehe')

    match_list = []

    with app.app_context():

        try:
            db.session.add_all(matches + [Tourney_info]+[val])
            # db.session.add(Tourney_info)
            db.session.commit()
            
            for match in matches:
                match_list.append(match.to_dict())
        
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f'Error {e} has occured')
            response = make_response({'error': 'Failed to create Matches'}, 500)
            raise

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

    matches = []   #List of match objects
    match_list = [] #List of json matches that will be turned into json for the bot

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
    update_list = []

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
        val.point_total +=3
        update_list.append(val)
        matches.append(new_Match)
    
    tourney_info.current_round = 1
    
    # update_list += matches 
    # update_list += tourney_info

    with app.app_context():
        print(matches)

        try:
            db.session.add_all(matches + [tourney_info] +[val])
            # db.session.add(tourney_info)
            db.session.commit()

            for match in matches:
                match_list.append(match.to_dict())


        except SQLAlchemyError as e:
            db.session.rollback()
            print(f'Error {e} has occured')
            response = make_response({'error': 'Failed to create Matches'}, 500)
            raise

        except ValueError as ve:
            print(f'Error {ve} has occured')
            raise

    return match_list

def FinalizeResults(tournament_id):
    #1. Set the tournament status to completed
    #2. Create the Tiebreaker Calculations, SOS, Bucholz, H2H,

    with app.app_context():

        entrants = Entrant.query.filter(Entrant.tournament_id==tournament_id).all()
        tournament = Tournament.query.filter(Tournament.id == tournament_id).first()
        matches = Match.query.filter(Match.tournament==tournament_id).all()
    
    tournament.status = 'Finalized'

    entrant_dict = {}

    for entrant in entrants:
        entrant_dict[entrant.id] = entrant
    
    SOS_dict = defaultdict(lambda: [0,0])   #{ id: [win, tie] }

    for match in matches: #We go over each match and add the results to my SOS_dict. Question is do byes count as wins for SOS I personally think no. 
        if match.player_2_id == None: #This would be a match where a bye was given
            continue
        else:
            if match.result !=0: #0 indicates a tie any other value is the id of the winner
                SOS_dict[match.result][0] +=1  
                # SOS_dict[match.result][2] +=1
                # SOS_dict[match.player]
            else:
                SOS_dict[match.player_1_id][1] +=1
                SOS_dict[match.player_2_id][1] +=1
        
    #At this point we have a list of wins and ties for each person. I already store the list of opponents so I can see how many games the person has played. 

    for entrant in entrants: #Calculate the SOS and other tiebreaker metrics for each person
        #Calculating SOS as follows : 
        #Summation over all opponents ( wins*1 + ties*.5) / Summation over all opponents( games played) 

        opp_w = 0
        opp_t = 0
        opp_g = 0

        for opponent in entrant.opponents: #opponent is the id of the opponent
            opp_w += SOS_dict[opponent][0]
            opp_t += SOS_dict[opponent][1]
            opp_g += len(entrant_dict[opponent].opponents)

        entrant.SOS = (opp_w + opp_t*(.5))/opp_g

    #Att the point the SOS for each entrant should be calculated in the entrants list

    with app.app_context():
        try:    
            db.session.add_all(entrants + [tournament])
            db.session.commit()
            response = make_response({},200)
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f'Error {e} has occured')
            response = make_response({'error':'Failed to Finalize'},500)

    return response

def CreateStandings(tournament_id):

    with app.app_context():

        ordered_entrants = Entrant.query.filter(Entrant.tournament_id==tournament_id).order_by(Entrant.point_total).order_by(Entrant.SOS).all()


        print(ordered_entrants)

#If I wanted to run a round-robin tournament I could do this the same way as a swiss tournament except it would just run for n-1 rounds. The way the matching algorithm works it would prioritize people that havent played each other so it would run until everybody has played each other. 

        
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