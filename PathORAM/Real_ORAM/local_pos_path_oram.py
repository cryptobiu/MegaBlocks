import math
import random

from config.utils import next_power_of_two_greater_or_equal


class LocalPosPathORAM:
    def __init__(self, N, b, Z):
        self.N = N
        self.B = b
        self.Z = Z
        self.position_map = {}

    def pos_map_access(self, addr):
        old_leaf = self.position_map[addr] if addr in self.position_map else random.randint(0, self.N - 1)
        self.position_map[addr] = random.randint(0, self.N - 1)
        return old_leaf, self.position_map[addr]