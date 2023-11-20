import networkx as nx   
from itertools import combinations
import matplotlib.pyplot as plt


#local imports

from config import app, db
from models import Match , Entrant , Tournament

def CreateMatches(tourney_id):
    #given a graph of the tournament

    #For Now we will recreate the graph from the tournament records.

    #1. Get all the entrants 

    with app.app_context():
        entrants = Entrant.query.filter(Entrant.tournament_id==tourney_id).all() #Entrant.dropped != True

    #2.Create the graph for creating matches. 

    print(entrants)

    G = nx.Graph()
    G.add_nodes_from(entrants)

    for pair in combinations(entrants,2):
        
        #If matching has already occured set the weight to -inf. 
        #This would also be another reason to store the graph itself in the database. 
        #We would recreate the graph when a user drops, aka remove the vertex and all edges involved with it(only for matchmaking).
        # 
        #  

        print(pair)

        p1_opponents = list(pair[0].opponents)

        if pair[1].id in p1_opponents:
            G.add_edge(pair[0],pair[1],weight=-10000) 
            print('match seen')

        else:
            G.add_edge(pair[0],pair[1],weight=pair[0].point_total+pair[1].point_total)


    nx.draw(G, with_labels=True, font_weight='bold', node_color='skyblue', font_color='black', node_size=1000)
    plt.show()

    pairings = (nx.max_weight_matching(G,maxcardinality=True))

    print(pairings)

    #Add new matches to the database

    matches = []
    
    for pair in pairings:
        new_Match = Match(
            tournament = tourney_id,
            round = 1,
            player_1 = pair[0].id,
            player_2 = pair[1].id,
        )
        matches.append(new_Match)

    with app.app_context():
        db.session.add_all(matches)
        db.session.commit()

    return pairings

def BiPartiteMatchMaking():
    #matchmaking by bipartite matching, break sets of players into 2 groups for player 1 and player 2

    pass

def CreateTournament():
    #Initialize a new tournament in the database. (This is done in app.py now instead)
    pass



def startTournament(tourney_id):
    #Start the tournament which would then create the initial matches.
    #We pass in a list of entrants and create the initial graph
    tourney_graph = nx.Graph() 
    
    #1. First get the entrants in the tournament
    with app.app_context():
        entrants = Entrant.query.filter(Entrant.tournament_id==tourney_id).all()
    
    #2. Add the entrants to the tournament
    
    tourney_graph = nx.Graph() 
    tourney_graph.add_nodes_from(entrants)

    #shuffle entrants as well

    all_pairings = []

    for pair in combinations(entrants,2):
        tourney_graph.add_edge(pair[0],pair[1],weight=pair[0].point_total+pair[1].point_total)
        
        all_pairings.append(pair)

    pairings = (nx.maximal_matching(tourney_graph))    

    # nx.draw(tourney_graph, with_labels=True, font_weight='bold', node_color='skyblue', font_color='black', node_size=1000)
    # plt.show()

    print(pairings)

    #4. We have the pairings and now we need to turn them into match objects to store in the database. Extract the information from the Entrant

    matches = []
    for pair in pairings:
        new_Match = Match(
            tournament = tourney_id,
            round = 1,
            player_1 = pair[0].id,
            player_2 = pair[1].id,
        )
        matches.append(new_Match)

    with app.app_context():
        db.session.add_all(matches)
        db.session.commit()


    #5. Create a graph of tournament state. This will be the graph used for subsequent matchmaking once results matter. 
        #pairings that have already been set should now be set to weights of - inf so they cannot occur again since we are using max weight matching. 



    return matches

def add_Match_Result(match_id, loser_id):
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

# startTournament(1)

##Added Round 1 Sim Results

# add_Match_Result(1,5)
# add_Match_Result(2,4)
# add_Match_Result(3,7)
# add_Match_Result(4,1)

##Create Round 2 Pairings

# CreateMatches(1)

##Add Round 3 Sim Results

# add_Match_Result(5,7)
# add_Match_Result(6,4)
# add_Match_Result(7,8)
# add_Match_Result(8,3)

#Create Round 3 Pairings
# CreateMatches(1)

add_Match_Result(9,5)
add_Match_Result(10,6)
add_Match_Result(11,8)
add_Match_Result(12,7)