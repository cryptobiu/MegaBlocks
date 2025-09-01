import math
from FutORAMa.Counter_ORAM.ORAM import ORAM
from FutORAMa.Counter_ORAM.local_RAM import local_RAM


class CounterFutORAMa:
    def __init__(self, N, w, b):
        self.N = N
        self.w = w
        self.b = b
        self.number_of_blocks = math.ceil(N * w / b)

    def counter_only_test(self):
        oram = ORAM(self.number_of_blocks)
        oram.initial_build('testing_data')
        for i in range(0, self.number_of_blocks - 1, oram.conf.MU):
            btc = oram.built_tables_count()
            # Reading 2MU before building a level.
            local_RAM.BALL_READ += 4 * btc * oram.conf.MU
            local_RAM.RT_READ += 2 * btc * oram.conf.MU
            local_RAM.BALL_WRITE += 4 * btc * oram.conf.MU
            local_RAM.RT_WRITE += 2 * btc * oram.conf.MU
            oram.rebuild()
        blocks_read = (local_RAM.BALL_READ + local_RAM.BALL_WRITE) / self.number_of_blocks
        return blocks_read
