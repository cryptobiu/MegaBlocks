import math
from MegaBlocksORAM.Simulation_ORAM.counter_compaction import compaction
from MegaBlocksORAM.Simulation_ORAM.counter_hash_table import HashTable
from config.constants import DUMMY
from RemoteRam.counter_remote_ram import CounterRemoteRam


class SimulationMegaBlocksORAM:
    """
    Counter version of the MegaBlocks ORAM scheme.

    This class implements the hierarchical ORAM using counter-based memory access simulation.
    N is the number of memory cells used by the client. Each server block holds B elements.
    The hierarchy is organized into levels based on expansion factor q.
    """

    def __init__(self, N, B, q, local_memory_in_server_blocks=2):
        """
        Initializes the ORAM with the given parameters.

        Parameters:
          N (int): The number of memory cells used by the client.
          B (int): Block capacity (elements per block).
          q (int): Level expansion factor.
          local_memory_in_server_blocks (int): Available local memory (in server blocks).
        """
        self.lookup_counter = 0
        self.extract_counter = 0
        self.build_counter = 0
        self.compaction_counter = 0
        self.N = N
        self.B = B
        self.q = q
        self.curr = None
        self.local_memory_in_server_blocks = local_memory_in_server_blocks
        self.amount_of_levels = math.floor(math.log(self.N, q))
        self.tables = []
        self.inner_tables = []
        for i in range(self.amount_of_levels + 1):
            if math.ceil((q ** i) * (q - 1) / B) < self.local_memory_in_server_blocks:
                self.local_memory_in_server_blocks -= math.ceil((q ** i) * (q - 1) / B)
                self.inner_tables.append(i)
        self.tables = [
            HashTable(
                CounterRemoteRam(block_capacity=self.B, memory_size=0, local=(i in self.inner_tables)),
                self.B, 0
            )
            for i in range(self.amount_of_levels + 1)
        ]
        self.load_factors = [0] * (self.amount_of_levels + 1)
        self.init_oram()

    def access(self, op, addr, data):
        """
        Simulates an oblivious access (read or write) to the ORAM.

        The method simulates I/O by performing dummy lookups and merging memory accesses.
        It finds the first level with load factor below q-1, then uses concatenation and
        compaction (if necessary) to update the hierarchy.

        Parameters:
          op: The operation type (e.g., READ_OPERATION or write indicator).
          addr: The address/key to be accessed.
          data: The data to be written (if a write operation).

        Returns:
          The retrieved data (always DUMMY in this counter version).
        """
        # Simulate lookup on each level to count I/O operations.
        for i in range(self.amount_of_levels + 1):
            if self.load_factors[i] > 0:
               self.tables[i].ht_lookup(1)
        j = self.find_ht_index()
        u = CounterRemoteRam(self.B, 1, local=True)
        if j < self.amount_of_levels:
            for i in range(j + 1):
                if self.tables[i].is_built:
                    u = CounterRemoteRam.concat_memory_accesses(
                        u, self.tables[i].ht_extract(),
                        self.calc_ht_size(i - 1), self.calc_ht_size(i), self.B
                    )
            self.load_factors[j] += 1
            self.tables[j] = HashTable(u, self.B, self.calc_ht_size(level_index=j), local=(j in self.inner_tables))
            self.tables[j].ht_build()
            self.reset_tables(0, j)
        else:
            for i in range(j + 1):
                if self.tables[i].is_built:
                    u = CounterRemoteRam.concat_memory_accesses(
                        u, self.tables[i].ht_extract(),
                        self.calc_ht_size(i - 1), self.calc_ht_size(i), self.B
                    )
            u_prime = compaction(u, u.memory_size * self.B, self.B, self.N) if self.load_factors[j] == self.q - 1 else u
            self.tables[j] = HashTable(u_prime, self.B, u_prime.memory_size * self.B)
            self.tables[j].ht_build()
            self.reset_tables(0, j)
            self.load_factors[j] = self.q - 1
        return DUMMY

    def find_ht_index(self):
        """
        Finds the first level with load factor less than q-1.

        Returns:
          int: The index of the level where new data can be merged; if all are full, returns amount_of_levels.
        """
        for index, load_factor in enumerate(self.load_factors):
            if load_factor < self.q - 1:
                return index
        return self.amount_of_levels

    def reset_tables(self, start, end):
        """
        Resets the hash tables and load factors for levels in the range [start, end).

        Parameters:
          start (int): Starting level index (inclusive).
          end (int): Ending level index (exclusive).
        """
        for i in range(start, end):
            self.tables[i].is_built = False
            self.tables[i].table = []
            self.load_factors[i] = 0

    def calc_ht_size(self, level_index):
        """
        Calculates the effective size for a given level.

        For level 0, the size equals its load factor; for the highest level, the size is N.
        Intermediate levels use the expansion factor q.

        Parameters:
          level_index (int): The level index.

        Returns:
          int: The calculated size for that level.
        """
        if level_index == 0:
            return self.load_factors[0]
        elif level_index == self.amount_of_levels:
            return self.N
        else:
            return math.ceil(int(math.pow(self.q, level_index) * self.load_factors[level_index]))

    def init_oram(self):
        X = CounterRemoteRam(block_capacity=self.B, memory_size=math.ceil(self.N / self.B))
        self.tables[self.amount_of_levels] = HashTable(X=X, B=self.B, n=self.N)
        self.tables[self.amount_of_levels].ht_build()
        self.load_factors[self.amount_of_levels] = self.q - 1
        CounterRemoteRam.read_operations = 0
        CounterRemoteRam.write_operations = 0