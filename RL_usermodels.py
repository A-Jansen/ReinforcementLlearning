# -*- coding: utf-8 -*-
"""
Created on Wed Sep 20 10:51:36 2023

Example code from: Kostas Tsiakas

@author: Anniek Jansen
"""

#!/usr/bin/python
import numpy as np
import random as rnd
import itertools
import matplotlib.pyplot as plt
import csv

from userModel import *

# TODO how long is an interaction and when to move on?
# TODO change prob based on pain level

# Return list of position of largest element  -- RANDOM between equals


def maxs(seq):
    max_indices = []
    # if seq:
    max_val = seq[0]
    for i, val in ((i, val) for i, val in enumerate(seq) if val >= max_val):
        if val == max_val:
            max_indices.append(i)
        else:
            max_val = val
            max_indices = [i]

    return rnd.choice(max_indices)

# return a random action based on the Q-probabilities


def cdf(seq):
    r = rnd.random()
    for i, s in enumerate(seq):
        if r <= s:
            return i

# create state space as combinatin of features


def state_action_space():
    # 0: neutral/none, 1: content, 2: happy, 3: surprised, 4: sad, 5: angry
    current_action = [0, 1, 2, 3, 4, 5]
    pain_presence = [0, 1]  # 0: no pain, 1: pain
    # 0: none, 1: any interaction
    user_interaction = [0, 1]
    # 0: neutral/none, 1: content, 2: happy, 3: surprised, 4: sad, 5: angry
    previous_action = [0, 1, 2, 3, 4, 5]
    # 0: no user_interaction, 1: any user_interaction (petting, clapping, shaking)
    previous_success = [0, 1]
    combs = (current_action, pain_presence, user_interaction,
             previous_action, previous_success)
    states = list(itertools.product(*combs))

    '''
    actions 0: neutral/none, 1: content, 2: happy, 3: surprised, 4: sad, 5: angry

    '''
    actions = [0, 1, 2, 3, 4, 5]
    return states, actions


def get_next_state(state, states, action, previous_action):
    '''
    STATE SPACE
    state[0]: current action {0: neutral/none, 1: content, 2: happy, 3: surprised, 4: sad, 5: angry}
    state[1]: pain presence {0,1}
    state[2]: user_interaction {0: none, 1: interaction}
    state[3]: previous action {0: neutral/none, 1: content, 2: happy, 3: surprised, 4: sad, 5: angry}
    state[4]: previous succes 0: no user_interaction, 1: any user_interaction (petting, clapping, shaking)
    
    STATE last 10 seconds
    
    At the end of the state, sample pain and interaction and get reward
    
    Question:: is current state needed, 
    '''
    
# =============================================================================
#     state[0] = action
#     state[1] = pain_model(action, state)
#     state[2] = user_interaction_model( action, state)
#     state[3] = previous_action
#     state[4] = previous success
# =============================================================================
    next_state = state[:]

    # if there is any user_interaction, set previous succes to 1
    if state[2] != 0:
        next_state[4] = 1
    else:
        next_state[4] = 0
    

# Should we evaluate pain for the next state or for the current state????
    next_state[0] = action
    next_state[1] = pain_model(action, state)
    next_state[2] = user_interaction_model(next_state[1], action, state)
    next_state[3] = previous_action

# REWARDS
# TODO change reward signal to discourage switching to often between behaviours, look at s, s' and a
# Reward of interaction should be higher then punishment for changing action

# using -1 for switching state resulted in a policy that never changed state

    score =0
    if next_state[2] == 1:
        score = 10
    if (action == previous_action and next_state[2] == 1):
        score += 2
    elif (action == previous_action and next_state[2] == 0): #ensures that the robot still does some switches in behaviour
        score -= 1
    else:
        score = 0

    reward = score
    return reward, next_state

# define the MDP




class MDP:
    def __init__(self, init_state, actlist, terminals=[], gamma=.9):
        self.init = init_state
        self.actlist = actlist
        self.terminals = terminals
        if not (0 <= gamma < 1):
            raise ValueError("An MDP must have 0 <= gamma < 1")
        self.gamma = gamma
        self.states = set()
        self.reward = 0

    def actions(self, state):
        """Set of actions that can be performed in this state.  By default, a
list of actions, except for terminal states. Override this
 if you need to specialize by state."""
        if state in self.terminals:
            return None
        else:
            return self.actlist

# define Policy (softmax or e-greedy)


class Policy:

    def __init__(
        self,
        name,
        param,
        Q_state=[],
        Q_next_state=[],
    ):
        self.name = name
        self.param = param
        self.Q_state = Q_state
        self.Q_next_state = Q_next_state

    def return_action(self):

        if self.name == 'egreedy':
            values = self.Q_state
            maxQ = max(values)
            e = self.param
            if rnd.random() < e:  # exploration
                return rnd.randint(0, len(values) - 1)
            else:
               # exploitation
                return maxs(values)

# representation is Qtable only


class Representation:
    # qtable, neural network, policy function, function approximation
    def __init__(self, name, params):
        self.name = name
        self.params = params
        if self.name == 'qtable':
            [self.actlist, self.states] = self.params
            self.Q = [[0.0] * len(self.actlist)
                      for x in range(len(self.states))]

# learning algorithms: sarsa and q-learning


class Learning:
    # qlearning, sarsa, traces, actor critic, policy gradient
    def __init__(self, name, params):
        self.name = name
        self.params = params
        if self.name == 'qlearn' or self.name == 'sarsa':
            self.alpha = self.params[0]
            self.gamma = self.params[1]

    def update(self, state, action, next_state, next_action, reward, Q_state, Q_next_state, done):
        if done:
            Q_state[action] = Q_state[action] + \
                self.alpha*(reward - Q_state[action])
            error = reward - Q_state[action]
        else:
            if self.name == 'qlearn':
                Q_state[action] += self.alpha * \
                    (reward + self.gamma*max(Q_next_state) - Q_state[action])
                error = reward + self.gamma*max(Q_next_state) - Q_state[action]

            if self.name == 'sarsa':
                learning = self.alpha * \
                    (reward + self.gamma *
                     Q_next_state[next_action] - Q_state[action])
                Q_state[action] = Q_state[action] + learning
                error = reward + self.gamma * \
                    Q_next_state[next_action] - Q_state[action]
        return Q_state, error


# get state-action space
states, actions = state_action_space()
start_state = [0, 0, 0, 0, 0]
m = MDP(start_state, actions)
m.states = states


alabel = ["neutral", "content",  "happy", "surprised", "sad", "angry"]

# initialize Q-table
table = Representation('qtable', [m.actlist, m.states])
Q = np.asarray(table.Q)
q=False


# A Q-table can be written and loaded as a file
# you can load it like this:
if q:
    ins = open("q_table",'r')
    Q = [[float(n) for n in line.split()] for line in ins]
    ins.close()
    table.Q = Q
print(Q)
# this can change to suit the problem -- number of learning episodes - games
episodes = 50
episode = 1

# q-values --> q.Q
egreedy = Policy('egreedy', 1.0, table.Q)

# State transitions happen every # seconds, e.g. every 10 seconds. Then it will check for interactions, pain levels, previous success and update state

alpha = float(0.1) #learning rate
gamma = float(0.9)
learning = Learning('sarsa', [alpha, gamma])
interactions = 50        # this can change to suit the problem -- number of rounds
attempts = []
errors = []
returns = []

while (episode < episodes):
    previous_action = 0  # start with neutral as "last" action
    interaction = 1
    done = 0
    state = start_state
    if (episode % 10 == 0):
        print("Episode: " + str(episode))
    r = 0
    e = 0
    egreedy.param *= 0.0  # this can change to suit the problem
    if egreedy.param < 0.1:
        egreedy.param = 0.0

    while (not done):
        state_index = states.index(tuple(state))

        # human actions not available for the agent (actions 5-10)
        egreedy.Q_state = Q[state_index][:]

        action = egreedy.return_action()
        
        #wait 10 seconds and evaluate reward and get next state

        # or get next state and reward from interaction for online learning
        reward, next_state = get_next_state(
            state, states, action, previous_action)
        next_state_index = states.index(tuple(next_state))
        r += (learning.gamma**(interaction-1))*reward

        # sarsa
        # again only choose from actions that the agent can do
        egreedy.Q_next_state = Q[next_state_index][:]
        next_action = egreedy.return_action()
        if interaction == interactions:
            done = 1
            attempts.append(interaction)

        # LEARNING
        Q[state_index][:], error = learning.update(
            state_index, action, next_state_index, next_action, reward, Q[state_index][:], Q[next_state_index][:], done)
        e += error
        if (episode % 10 == 0):
            # print ("Episode: " + str(episode))
            print(interaction, state, alabel[action],
                  next_state, reward, egreedy.param)
        state = next_state
        previous_action = action
        interaction += 1

    episode += 1
    returns.append(r)
    errors.append(error)


def moving_average(a, n=20):
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n



plt.plot(moving_average(returns))
plt.title("Total return")
plt.show()

plt.plot(moving_average(errors))
plt.title("Total learning error")
plt.show()

print(Q)

# if you want to save the Q-table on a file

# =============================================================================
# with open('q_table', 'w') as f:
#     writer = csv.writer(f,delimiter=' ')
#     writer.writerows(Q)
# =============================================================================
