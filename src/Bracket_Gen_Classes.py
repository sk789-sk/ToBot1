#Bracket Gen Classes
from models import Match
from collections import deque
from config import app , db

class TreeNode:
    #Represent each node as a match.
    def __init__(self,player_1,player_2, left=None,right=None,winner=None,parent=None):
        self.value = (player_1,player_2)
        
        self.left = left
        self.right = right
        
        self.winner = winner
        self.player_1 = player_1
        self.player_2 = player_2
        
        self.db_id = None
        
    pass

def next_power_of_2(n):
    # If n is already a power of 2, return n
    if n & (n - 1) == 0:
        return n

    # Find the position of the most significant bit in n
    msb_position = 0
    while n > 0:
        n >>= 1
        msb_position += 1

    # Return 2 raised to the power of the next highest bit position
    return 1 << msb_position

def build_single_elimination_bracket(player_list,t_id):
    matches = []

    #create initial matches
    for x,y in zip(*[iter(player_list)]*2): #this works from documentation as a trick 
        match_leaf = TreeNode(player_1=x,player_2=y)
        matches.append(match_leaf)
    
    #create subsequent matches
    while len(matches) >1:
        print(len(matches))
        prev_1 = matches.pop(0)
        prev_2 = matches.pop(0)
        new_match = TreeNode(player_1=None,player_2=None,left=prev_1, right= prev_2)
        matches.append(new_match)
    return matches[0] #returns the root node

def display_bracket_DFS(root_node, depth = 0):
    if root_node:
        print(depth , (root_node.value))
        display_bracket_DFS(root_node.left, depth+1)
        display_bracket_DFS(root_node.right, depth+1)

def display_bracket_BFS(root):
    if not root:
        return
    
    queue = deque([root])

    while queue:
        node = queue.popleft()
        print(f"depth: , Value: {node.value}")

        if node.left:
            queue.append((node.left)) #depth +1
        if node.right:
            queue.append((node.right)) #depth +1 

def tree2db(root,t_id,parent_id=None):

    #i guess we could do this where we start with the root, we add the values 
    #We then access the children of the node which now has an id that we can use for the parent column. 
    #I think we should do DFS traversal then. so we have the parent into child for easier referencing. 

    if root:

        new_Match = Match(
            tournament = t_id,
            result = None,
            round = None,
            player_1_id = root.player_1.id if root.player_1 else None,
            player_2_id = root.player_2.id if root.player_2 else None,
            winner_next_match_id = parent_id,
            # loser_next_match_id = None
        )

        with app.app_context():
            db.session.add(new_Match)
            db.session.flush()
            db.session.commit()
            root.db_id = new_Match.id
            print(root.db_id)

        tree2db(root.left, t_id=t_id,parent_id=root.db_id)
        tree2db(root.right, t_id=t_id,parent_id=root.db_id)
    


    return 

if __name__ == "__main__":
    print(next_power_of_2(6))
    print(next_power_of_2(64))
    print(next_power_of_2(33)) 

    pass




# class TreeNode:
#     def __init__(self, value):
#         self.value = value
#         self.left = None
#         self.right = None

# def build_single_elimination_bracket(players):
#     matches = []
#     for i in range(0, len(players), 2):
#         match = TreeNode((players[i], players[i+1]))
#         matches.append(match)

#     while len(matches) > 1:
#         new_matches = []
#         for i in range(0, len(matches), 2):
#             match = TreeNode((None, None))
#             match.left = matches[i]
#             match.right = matches[i+1]
#             new_matches.append(match)
#         matches = new_matches

#     return matches[0]

# def print_bracket(root, depth=0):
#     if root:
#         print("  " * depth + str(root.value))
#         print_bracket(root.left, depth + 1)
#         print_bracket(root.right, depth + 1)

# players = ["Player1", "Player2", "Player3", "Player4", "Player5", "Player6", "Player7", "Player8"]
# root = build_single_elimination_bracket(players)
# print_bracket(root)
