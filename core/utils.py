# SpacedCode/core/utils.py

import math

class FSRS:
    def __init__(self, w=None):
        self.w = w if w else (2.5, 2.6, 2.3, 2.8, 3.0, 0.8, 0.7, 0.5, 0.1, 0.1, 0.1, 1.0, 0.5, 0.5, 1.0, .6, 1.2, 0.5, 0.7, 1.3)
        self.request_retention = 0.8
        self.maximum_interval = 365
        self.DECAY = -0.4
        self.FACTOR = 0.9 ** (1 / self.DECAY) - 1

    def forgetting_curve(self, elapsed_days, stability):
        return (1 + self.FACTOR * elapsed_days / stability) ** self.DECAY

    def next_interval(self, stability, retention_factor):
        new_interval = stability / self.FACTOR * (retention_factor ** (1 / self.DECAY) - 1)
        return min(max(round(new_interval), 1), self.maximum_interval)

    def next_difficulty(self, difficulty, rating):
        next_d = difficulty - self.w[6] * (rating - 3)
        return min(max(self.mean_reversion(5.0, next_d), 1), 10)

    def next_recall_stability(self, difficulty, stability, retrievability, rating):
        return stability * (
            1
            + math.exp(self.w[8])
            * (11 - difficulty)
            * math.pow(stability, -self.w[9])
            * (math.exp((1 - retrievability) * self.w[10]) - 1)
        ) * (self.w[15] if rating == 2 else 1)

    def mean_reversion(self, init, current):
        return self.w[7] * init + (1 - self.w[7]) * current
    

def calculate_average_time(question, solving_time):
    if question.average_time:
        return (question.average_time + solving_time) / 2
    return solving_time