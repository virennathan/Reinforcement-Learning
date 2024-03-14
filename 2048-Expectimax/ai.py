from __future__ import absolute_import, division, print_function
import copy, random
import sys
from game import Game

MOVES = {0: 'up', 1: 'left', 2: 'down', 3: 'right'}
MAX_PLAYER, CHANCE_PLAYER = 0, 1 

# Tree node. To be used to construct a game tree. 
class Node: 
    # Recommended: do not modify this __init__ function
    def __init__(self, state, player_type):
        self.state = (state[0], state[1])

        # to store a list of (direction, node) tuples
        self.children = []

        self.player_type = player_type

    # returns whether this is a terminal state (i.e., no children)
    def is_terminal(self):
        if not self.children:
            return True
        else:
            return False

# AI agent. Determine the next move.
class AI:
    # Recommended: do not modify this __init__ function
    def __init__(self, root_state, search_depth=3): 
        self.root = Node(root_state, MAX_PLAYER)
        self.search_depth = search_depth
        self.simulator = Game(*root_state)

    # (Hint) Useful functions: 
    # self.simulator.current_state, self.simulator.set_state, self.simulator.move

    # TODO: build a game tree from the current node up to the given depth
    def build_tree(self, node = None, depth = 0):
        if depth == 0:
            return
        if node.player_type == MAX_PLAYER:
            for dir in MOVES:
                temp = Game(*node.state)
                if temp.move(dir):
                    node.children += [(dir, Node(temp.current_state(), CHANCE_PLAYER))]
            for child in node.children:
                self.build_tree(child[1], depth-1)
        else:
            temp = Game(*node.state)
            tiles = temp.get_open_tiles()
            for tile in tiles:
                rand_board, rand_score = temp.current_state()
                rand_board[tile[0]][tile[1]] = 2
                rand_game = Game(init_tile_matrix=rand_board, init_score=rand_score)
                node.children += [(None, Node(rand_game.current_state(), MAX_PLAYER))]
            for child in node.children:
                self.build_tree(child[1], depth-1)

    # TODO: expectimax calculation.
    # Return a (best direction, expectimax value) tuple if node is a MAX_PLAYER
    # Return a (None, expectimax value) tuple if node is a CHANCE_PLAYER
    def expectimax(self, node = None):
        if node.is_terminal():
            return (None, node.state[1])
        elif node.player_type == MAX_PLAYER:
            value = -sys.maxsize-1
            dir_select = -1
            for child in node.children:
                child_max = self.expectimax(child[1])[1]
                if child_max > value:
                    value = child_max
                    dir_select = child[0]
            return (dir_select, value)
        else:
            value = 0
            for child in node.children:
                value += self.expectimax(child[1])[1] * 1/len(node.children)
            return (None, value)

    # Return decision at the root
    def compute_decision(self):
        self.build_tree(self.root, self.search_depth)
        direction, _ = self.expectimax(self.root)
        return direction

    # TODO (optional): implement method for extra credits
    def compute_decision_ec(self):
        self.build_tree(self.root, 5)
        direction, _ = self.expectimax(self.root)
        return direction

