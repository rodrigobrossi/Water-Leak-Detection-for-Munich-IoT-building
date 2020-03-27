import numpy as np

class MarkovModel:
    def __init__(self, states_amount):
        # Transition matrix includes initial state
        self.transition_matrix = np.zeros((states_amount + 1, states_amount + 1))
        self.current_state = 0

    @property
    def transition_matrix(self):
        # Uniform probability for transition from initial state
        self._cumulative_matrix[0] = 1 / (len(self._cumulative_matrix) - 1)
        self._cumulative_matrix[0][0] = 0
        np.seterr(divide='ignore', invalid='ignore')
        transition_matrix = self._cumulative_matrix / np.sum(self._cumulative_matrix, axis=1).reshape((-1,1))
        return np.nan_to_num(transition_matrix)

    @transition_matrix.setter
    def transition_matrix(self, matrix):
        if not np.any(matrix > 1):
            # Probability matrix case 
            matrix *= 100
        self._cumulative_matrix = matrix

    def addDataPoint(self, state):
        # Max likelihood parameter estimation
        self._cumulative_matrix[self.current_state][state + 1] += 1
        self.current_state = state + 1
    
    def predictNextState(self):
        state = np.argmax(self.getTransitionProbability()) - 1
        return state, self.transition_matrix[self.current_state][state] 

    def getTransitionProbability(self, state=None):
        if state == None:
            return self.transition_matrix[self.current_state]
        return self.transition_matrix[state + 1]

    def getSequenceProbability(self, sequence):
        probability = self.transition_matrix[0][sequence[0]+1]
        for i in range(0, len(sequence) - 1):
            probability *= self.transition_matrix[sequence[i]+1][sequence[i+1]+1]
        return probability