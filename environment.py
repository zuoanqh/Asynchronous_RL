import tensorflow as tf
from skimage.transform import resize
from skimage.color import rgb2gray
import numpy as np
from collections import deque
import gym_pull
import random


class Env(object):
    def __init__(self, gym_env, resized_width, resized_height, agent_history_length, game_type):
        self.env = gym_env
        self.resized_width = resized_width
        self.resized_height = resized_height
        self.agent_history_length = agent_history_length
        self.game_type = game_type

        if self.game_type == 'Doom':
            if gym_env.spec.id == "ppaquette/DoomBasic-v0":
                print("Doing workaround for DoomBasic-v0")
                self.gym_actions = [0, 10, 11]
            if gym_env.spec.id == "ppaquette/DoomDefendCenter-v0":
                print("Doing workaround for DoomDefendCenter-v0")
                self.gym_actions = [0, 14, 15]
            if gym_env.spec.id == "ppaquette/DoomDefendLine-v0":
                print("Doing workaround for DoomDefendLine-v0")
                self.gym_actions = [0, 14, 15]
            if gym_env.spec.id == "ppaquette/DoomDeathmatch-v0":
                print("Doing workaround for DoomDeathmatch-v0")
                self.gym_actions = [0, 10, 11, 12, 13, 14, 15]

            if gym_env.spec.id == "ppaquette/DoomHealthGathering-v0":
                print("Doing workaround for DoomHealthGathering-v0")
                self.gym_actions = [13, 14, 15]
        elif self.game_type == 'Atari':
            if gym_env.spec.id == "Breakout-v0" or gym_env.spec.id == "Pong-v0":
                self.gym_actions = [1, 2, 3]
            else:
                self.gym_actions = len(self.env.action_space)
        else:
            print("Error: game_type MUST be Doom or Atari")
            exit()
        self.gym_actions = [1, 2, 3]
        # Screen buffer of size AGENT_HISTORY_LENGTH to be able
        # to build state arrays of size [1, AGENT_HISTORY_LENGTH, width, height]
        self.state_buffer = deque()

    def get_initial_state(self):
        """
        Resets the atari game, clears the state buffer
        """
        # Clear the state buffer
        self.state_buffer = deque()

        x_t = self.env.reset()
        x_t = self.get_preprocessed_frame(x_t)
        s_t = np.stack((x_t, x_t, x_t, x_t), axis=0)

        for i in range(self.agent_history_length - 1):
            self.state_buffer.append(x_t)
        # ~ s_t = np.array([s_t])
        return s_t

    def get_preprocessed_frame(self, observation):
        """
        See Methods->Preprocessing in Mnih et al.
        1) Get image grayscale
        2) Rescale image
        """
        return resize(rgb2gray(observation), (self.resized_width, self.resized_height))

    def step(self, action_index):
        """
        Excecutes an action in the gym environment.
        Builds current state (concatenation of agent_history_length-1 previous frames and current one).
        Pops oldest frame, adds current frame to the state buffer.
        Returns current state.
        """
        if self.game_type == 'Doom':
            actions = [0] * 43
            actions[self.gym_actions[action_index]] = 1
            x_t1, r_t, terminal, info = self.env.step(actions)
        else:
            x_t1, r_t, terminal, info = self.env.step(self.gym_actions[action_index])

        x_t1 = self.get_preprocessed_frame(x_t1)

        previous_frames = np.array(self.state_buffer)
        s_t1 = np.empty((self.agent_history_length, self.resized_height, self.resized_width))
        s_t1[:self.agent_history_length - 1, ...] = previous_frames
        s_t1[self.agent_history_length - 1] = x_t1

        # Pop the oldest frame, add the current frame to the queue
        self.state_buffer.popleft()
        self.state_buffer.append(x_t1)

        return s_t1, r_t, terminal
