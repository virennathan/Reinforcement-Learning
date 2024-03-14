from __future__ import absolute_import, division, print_function
from math import sqrt, log
from game import Game, WHITE, BLACK, EMPTY
import copy
import time
import random

class Node:
    # NOTE: modifying this block is not recommended
    def __init__(self, state, actions, parent=None):
        self.state = (state[0], copy.deepcopy(state[1]))
        self.num_wins = 0 #number of wins at the node
        self.num_visits = 0 #number of visits of the node
        self.parent = parent #parent node of the current node
        self.children = [] #store actions and children nodes in the tree as (action, node) tuples
        self.untried_actions = copy.deepcopy(actions) #store actions that have not been tried
        simulator = Game(*state)
        self.is_terminal = simulator.game_over

BUDGET = 1000

class AI:
    def __init__(self, state):
        self.simulator = Game()
        self.simulator.reset(*state) #using * to unpack the state tuple
        self.root = Node(state, self.simulator.get_actions())

    def mcts_search(self):
        iters = 0
        action_win_rates = {} #store the table of actions and their ucb values

        # MCTS Loop
        while(iters < BUDGET):
            if ((iters + 1) % 100 == 0):
                print("\riters/budget: {}/{}".format(iters + 1, BUDGET), end="")

            # select a node, rollout, and backpropagate
            s = self.select(self.root)
            winner = self.rollout(s)
            self.backpropagate(s, winner)
            iters += 1
        print()

        # return the best action, and the table of actions and their win values 
        _, action, action_win_rates = self.best_child(self.root, 0)
        return action, action_win_rates

    def select(self, node):
        """
        select a child node
        """
        while not node.is_terminal:
            if node.untried_actions:
                return self.expand(node)
            else:
                node, _, _ = self.best_child(node, 1/(2**0.5))
        return node

    def expand(self, node):
        """
        add a new child node from an untried action and return this new node
        """
        child_node = None #choose a child node to grow the search tree
        action = node.untried_actions.pop(0)

        self.simulator.reset(*node.state)
        self.simulator.place(*action)
        child_node = Node(self.simulator.state(), self.simulator.get_actions(), node)
        node.children.append((action, child_node))
        return child_node

    def best_child(self, node, c=1): 
        """ 
        determine the best child and action by applying the UCB formula
        """
        best_child_node = None # to store the child node with best UCB
        best_action = None # to store the action that leads to the best child
        action_ucb_table = {} # to store the UCB values of each child node (for testing)

        for child in node.children:
            action_ucb_table[child[0]] = child[1].num_wins / child[1].num_visits + \
                                         c * sqrt(2 * log(node.num_visits) / child[1].num_visits)
        
        # return the first child with the highest UCB
        max_ucb = max(action_ucb_table.values())
        for child in node.children:
            if action_ucb_table[child[0]] == max_ucb:
                best_child_node = child[1]
                best_action = child[0]
                return best_child_node, best_action, action_ucb_table

    def backpropagate(self, node, result):
        """
        backpropagate the information about winner
        """
        while node is not None:
            node.num_visits += 1
            if node.parent is not None:
                # store num wins for player of parent node
                node.num_wins += result[node.parent.state[0]]
            node = node.parent

    def rollout(self, node):
        """
        rollout randomly from the selected node and return the winner of the game
        """
        self.simulator.reset(*node.state)
        while not self.simulator.game_over:
            self.simulator.place(*self.simulator.rand_move())
        
        # Determine reward indicator from result of rollout
        reward = {}
        if self.simulator.winner == BLACK:
            reward[BLACK] = 1
            reward[WHITE] = 0
        elif self.simulator.winner == WHITE:
            reward[BLACK] = 0
            reward[WHITE] = 1
        return reward
