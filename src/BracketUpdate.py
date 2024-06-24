from models import Match, Entrant
#Functions to update the brackets games

points_per_win = 3

def updateSingleElimMatch(winner_id,match_obj):
    #Assume we are getting a valid winner_id and a valid_match. (Verification is done earlier)
    #update the match result
    match_obj.result = winner_id
    #get the next match
    next_match = Match.query.filter(Match.id == match_obj.winners_next_match_id).first()
    if next_match:
        #First one to win gets so be player 1 doesnt matter
        if next_match.player_1_id is None:
            next_match.player_1_id = winner_id
        else:
            next_match.player_2_id = winner_id
        
    else:
        print('Final match node, winner has won')
    
    #update DB here or just return the match objects to be updated. I want to do all the updates in 1 function
    return

def updateSwissMatch(winner_id,match_obj,round):

    #update match info
    match_obj.round = round
    match_obj.result = winner_id
    #There is no next match to be updated, but there is instead Entrant information that needs to be updated 
    #update Entrant info

    players = (match_obj.player_1_id, match_obj.player_2_id)
    loser_id = 'Whichever one of the values in the players tuple doesnt equal the winners'

    winner_entrant_obj = Entrant.query.filter(Entrant.id==winner_id,Entrant.tournament_id==match_obj.tournament).first()
    lose_entrant_obj = Entrant.query.filter(Entrant.id==loser_id,Entrant.tournament_id==match_obj.tournament).first()
    
    winner_entrant_obj.opponents.append(loser_id)
    lose_entrant_obj.opponents.append(winner_id)
    winner_entrant_obj.point_total+=points_per_win

    updated = [winner_entrant_obj, lose_entrant_obj, match_obj]

    return updated