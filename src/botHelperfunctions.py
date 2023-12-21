from table2ascii import table2ascii


def create_table(data,header= ['Rank', 'Player', 'Points', 'Tiebreak1','Tiebreak2'],tiebreaker_metrics=['SOS','SOSOS']):
    body = []
    for idx, entrant in enumerate(data):
        body.append([idx+1,entrant['username'],entrant['point_total'],entrant[tiebreaker_metrics[0]],entrant[tiebreaker_metrics[1]]])
    message = table2ascii(header=header, body= body)   
    return message