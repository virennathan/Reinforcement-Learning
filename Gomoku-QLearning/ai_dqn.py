from __future__ import absolute_import, division, print_function
from math import sqrt, log
from game import Game, WHITE, BLACK, EMPTY
import copy
import time
import random
import math
from collections import namedtuple, deque
import itertools

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

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


Transition = namedtuple('Transition', ('state', 'action', 'next_state', 'reward'))


class ReplayMemory(object):

    def __init__(self, capacity):
        self.memory = deque([], maxlen=capacity)

    def push(self, *args):
        """Save a transition"""
        self.memory.append(Transition(*args))

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)
    

class DQN(nn.Module):

    def __init__(self, n_observations, n_actions):
        super(DQN, self).__init__()
        self.layer1 = nn.Linear(n_observations, 128)
        self.layer2 = nn.Linear(128, 128)
        self.layer3 = nn.Linear(128, n_actions)

    # Called with either one element to determine next action, or a batch
    # during optimization. Returns tensor([[left0exp,right0exp]...]).
    def forward(self, x):
        x = F.relu(self.layer1(x))
        x = F.relu(self.layer2(x))
        return self.layer3(x)


BUDGET = 2000
BATCH_SIZE = 128
GAMMA = 0.99
EPS_START = 0.9
EPS_END = 0.05
EPS_DECAY = 1000
TAU = 0.005
LR = 1e-4

memory = ReplayMemory(10000)
n_actions = 11
n_observations = 121
vnet_init = False


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
            s = self.select(self.root, iters)
            winner = self.rollout(s)
            self.backpropagate(s, winner)
            iters += 1

            # if len(memory) >= BATCH_SIZE and not vnet_init:
            #     transitions = memory.sample(BATCH_SIZE)
        print()

        # return the best action, and the table of actions and their win values 
        _, action, action_win_rates = self.best_child(self.root, 0)
        return action, action_win_rates

    def select(self, node, iters):
        """
        select a child node
        """
        while not node.is_terminal:
            if node.untried_actions:
                return self.expand(node)
            else:
                node, _, _ = self.best_child(node, 1/math.sqrt(2))
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

        best_child_node, best_action = self.pick_child(node, epsilon)
        return best_child_node, best_action, None

        # for child in node.children:
        #     action_ucb_table[child[0]] = child[1].num_wins / child[1].num_visits + \
        #                                  c * sqrt(2 * log(node.num_visits) / child[1].num_visits)
        #     memory.push(child[1].state, child[0], child[1].parent.state, child[1].num_wins / child[1].num_visits)
        
        # # return the first child with the highest UCB
        # max_ucb = max(action_ucb_table.values())
        # for child in node.children:
        #     if action_ucb_table[child[0]] == max_ucb:
        #         best_child_node = child[1]
        #         best_action = child[0]
        #         return best_child_node, best_action, action_ucb_table

    def pick_action(self, node, epsilon):
        if random.randint(0, 1) < epsilon:
            return random.choice(node.children)
        else:
            action_ucb_table = {}
            for child in node.children:
                action_ucb_table[child[0]] = -1 # query dqn
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
