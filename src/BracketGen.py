import networkx as nx   
from itertools import combinations
from collections import defaultdict
import matplotlib.pyplot as plt
import random
from math import log2, ceil

from flask import Flask, make_response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import aliased
from sqlalchemy import or_, desc

#local imports

from config import app, db
from models import Match , Entrant , Tournament
from Bracket_Gen_Classes import next_power_of_2, build_single_elimination_bracket, display_bracket_DFS, display_bracket_BFS ,tree2db

def CreateMatches(tourney_id):
    #given a graph of the tournament

    #For Now we will recreate the graph from the tournament records.

    #1. Get all the entrants

    with app.app_context():
        entrants = Entrant.query.filter(Entrant.tournament_id==tourney_id,Entrant.dropped is not True).all() 
    #2.Create the graph for creating matches.
    random.shuffle(entrants)

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
    random.shuffle(entrants)

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
        val.bye += 1

        update_obj_list.append(val)

############################################################################3
        # if val.bye == True:
        #     BiPartiteMatchMaking(tourney_id)  #Add a safeguard in to prevent to many recurse calls. 
        # else:

        #     new_Match = Match(
        #         tournament = tourney_id,
        #         round = current_r+1,
        #         player_1_id = val.id,
        #         player_2_id = None,
        #         result = val.id
        #     )
        #     matches.append(new_Match)

        #     #Update the entrant w/ bye points to also have bye listed in their name.
            
        #     val.point_total +=3
        #     val.bye = True 

        #     update_obj_list.append(val)
###########################################################################################333        

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

def startTournament_Swiss(tourney_id):
    #This is the same method for creating RR
    #Start the tournament which would then create the initial matches.
    #We pass in a list of entrants and create the initial graph
    #would it be better to just have this only make the matches and leave all database related things to be passed into it. Instead of giving it an ID instead we would pass it a graph 

    tourney_graph = nx.Graph() 
    
    #1. First get the entrants in the tournament
    with app.app_context():
        entrants = Entrant.query.filter(Entrant.tournament_id==tourney_id).all()
        tourney_info = Tournament.query.filter(Tournament.id == tourney_id).first()

    #Calculate the number of rounds in the tournament

    print(tourney_info)

    if tourney_info.status == 'Swiss':
        round_total = ceil(log2(len(entrants)))
    elif tourney_info.status == 'Round Robin':
        round_total = len(entrants) - 1



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
        val.bye += 1
        update_list.append(val)
        matches.append(new_Match)
    
    tourney_info.current_round = 1
    tourney_info.status = 'Underway'
    tourney_info.total_round = round_total

    with app.app_context():

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
    #3. Modified Median Bucholz Summation numer of points divided by number of games won 
    with app.app_context():

        entrants = Entrant.query.filter(Entrant.tournament_id==tournament_id).all()
        tournament = Tournament.query.filter(Tournament.id == tournament_id).first()
        matches = Match.query.filter(Match.tournament==tournament_id).all()
    
    tournament.status = 'Finalized'

    entrant_dict = {}

    for entrant in entrants:
        entrant_dict[entrant.id] = entrant
    
    SOS_dict = defaultdict(lambda: [0,0])   #{ id: [win, tie] }

    for match in matches: #We go over each match and add the results to my SOS_dict. Question is do byes count as wins for SOS I personally think no. Looking at tourney recrods, a win you get when you play against a bye counts as a win 
        # if match.player_2_id == None: #This would be a match where a bye was given
        #     continue
        # else:
            
        if match.result !=0: #0 indicates a tie any other value is the id of the winner
            SOS_dict[match.result][0] +=1  
        else:
            SOS_dict[match.player_1_id][1] +=1
            SOS_dict[match.player_2_id][1] +=1
        
    #At this point we have a list of wins and ties for each person. I already store the list of opponents so I can see how many games the person has played. 

    for entrant in entrants: #Calculate the SOS and other tiebreaker metrics for each person
        #Calculating SOS as follows : 
        #Summation over all opponents ( wins*1 + ties*.5) / Summation over all opponents( games played)  
        #Calculat median Bucholz
        #Calculate Bucholz
        ##Bucholz Cut 1 would essentially remove an 0-2 drop 
        ##SOS.SOS second tiebreaker that konami uses

        #FIDE has a system where where dropped opponent score is given as points_when_drop + ties for rest of games.
        #Newer system is Your score -  

        # https://chessischess.blogspot.com/2011/01/idiosyncrasies-of-swiss-manager-program.html 
        #https://chess.stackexchange.com/questions/24915/how-is-buchholz-score-calculated-in-a-swiss-tournament
        #https://www.fide.com/FIDE/handbook/Standards_of_Chess_Equipment_and_tournament_venue.pdf 
        #https://www.delanceyukschoolschesschallenge.com/wp-content/uploads/2018/06/Tie-Breaks-Explained-V2.pdf 

        
        

        #SOS vars
        opp_w = 0
        opp_t = 0
        opp_g = 0
        
        #SOSOS vars
        opp_opp_w = 0
        opp_opp_t = 0
        opp_opp_g = 0


        opp_points = []
        
        for opponent in entrant.opponents: #opponent is the id of the opponent
            opp_w += SOS_dict[opponent][0]
            opp_t += SOS_dict[opponent][1]
            opp_g += len(entrant_dict[opponent].opponents) + entrant_dict[opponent].bye
            opp_points.append(entrant_dict[opponent].point_total)

            #This is for Konami SOSOS
            for opp_2 in entrant_dict[opponent].opponents:
                opp_opp_w += SOS_dict[opp_2][0]
                opp_opp_t += SOS_dict[opp_2][1]
                opp_opp_g += len(entrant_dict[opp_2].opponents) + entrant_dict[opp_2].bye 


        #probably better to sort points and then do 0 and last index. Assuming each min max has to sort anyway
            
        entrant.SOS = round((opp_w + opp_t*(.5))/opp_g,3)
        entrant.SOSOS = round((opp_opp_w + opp_opp_t*(.5))/opp_opp_g,3)

        entrant.Bucholz = sum(opp_points)
        entrant.medianBucholz = sum(opp_points) - min(opp_points) - max(opp_points)
        entrant.BucholzCut1 = sum(opp_points) - min(opp_points)

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

def CreateStandings(tournament_id, *args):

    if not args:
        args = ('SOS', 'SOSOS')

    with app.app_context():
        query = Entrant.query.filter(Entrant.tournament_id==tournament_id).order_by(desc(Entrant.point_total))
        
        for arg in args:
            if not hasattr(Entrant, arg):
                print(f'Invalid attribute {arg}. Continuing with next attribute' )
                continue
            
            query = query.order_by(desc(getattr(Entrant,arg)))

        ordered_entrants = query.all()

    return(ordered_entrants)

def startSingleElim(tournament_id):
    #Create a single Elimination bracket from entrants
    #Steps: 
    # 1. Return the list of entrants in the tournament. 
    # 2. Check that the value of entrants is a power of 2. If not add dummy entrants(aka None) to the entrant list. Matches against dummies are byes. Inser the dummies in between actual entrants to ensure we dont have dummy vs dummy and byes that will occur in the later rounds
    # 3. Take the entrants list and turn them into matches/leaf nodes. These matches are leaf nodes for a binary tree.
    # 4. Construct the tree from the list of matches. This can be done recursively until the length of the matches is equal to 1 and that is the root and championshipnode. 2 leaf nodes are used to create a parent node and this parent is a new match. We can actually do this in 1 pass by adding the created parent nodes to the end of the list
    # 5. Add these matches to the database
    # 5. Matches where the entrant wins due to a bye is automatically updated, before we send out the pairings. 

    with app.app_context():
        entrants = Entrant.query.filter(Entrant.tournament_id == tournament_id).all()
        Tourney = Tournament.query.filter(Tournament.id == tournament_id).first()
    
    #### RANDOM SEEDING LIST###
    random.shuffle(entrants)
    print(entrants)
    byes_needed = next_power_of_2(len(entrants)) - len(entrants)
    print(byes_needed)
    new_entrants = []
    
    while byes_needed >0:
        new_entrants.append(entrants.pop(0))
        new_entrants.append(None)
        byes_needed -=1
    new_entrants.extend(entrants)
    
    print(new_entrants)
    ### Random Seeding List### 

    ###IF ENTRANTS ARE SEEDED###
    ###follow method created in notebook###
    ###IF ENTRANTS ARE SEEDED###
    
    #Create the bracket
    root = build_single_elimination_bracket(new_entrants,tournament_id)
    
    #Transfer bracket to db
    tree2db(root,tournament_id)
    display_bracket_DFS(root)   
    


    Tourney.status = 'Underway'

    #Get the Matches

    with app.app_context():
        init_matches = Match.query.filter(Match.tournament==tournament_id,Match.result == None,Match.player_1_id != None,Match.player_2_id != None).all()

        db.session.add(Tourney)
        db.session.commit()
        
        print(init_matches)

        match_list = [match.to_dict() for match in init_matches]

    return match_list
    


def startDoubleElim(tournament_id):
    #The winners side is a single elim bracket.
    #the losers side is a single elim bracket, but in between each level there is an additional set of matches where the winners side losers go down. Basically instead of cutting the amoutn of entrants in half with each round it takes 2 rounds to do it. 
    #We then create a match where the lft child is the winner of the winners bracket and the right hcild is the winner of the losers bracket to combine the 2 trees into 1. 
    pass


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


if __name__ == "__main__":
    startSingleElim(2)
    pass