import math
from MegaBlocksORAM.Real_ORAM.compaction import compaction
from MegaBlocksORAM.Real_ORAM.hash_table import HashTable
from config.constants import DUMMY, READ_OPERATION
from RemoteRam.remote_ram import RemoteRam
from config.utils import choose_C


class MegaBlocksORAM:
    """
    Implements the MegaBlocks ORAM scheme as described in the paper
    "MegaBlocks: Breaking the Ω(log N) I/O-Overhead Barrier for Oblivious RAM."

    Attributes:
      N (int): Number of memory blocks used by the client.
      B (int): The block capacity (number of elements per memory block in the remote RAM).
      q (int): The expansion factor for each level.
      local_memory_in_server_blocks (int): The amount of local memory available (in server blocks).
      amount_of_levels (int): The total number of levels in the ORAM hierarchy.
      tables (list): A list of HashTable instances representing each level.
      inner_tables (list): A list of level indices that are maintained in local memory.
      load_factors (list): A list tracking the number of valid entries (load) at each level.
    """

    def __init__(self, N, B, q, local_memory_in_server_blocks=2):
        self.N = N
        self.B = B
        self.q = q
        self.curr = None
        self.local_memory_in_server_blocks = local_memory_in_server_blocks
        # Calculate the number of levels using log base q.
        self.amount_of_levels = math.floor(math.log(self.N, q))
        self.tables = []
        self.inner_tables = []
        # Determine which levels can reside in local memory.
        for i in range(self.amount_of_levels + 1):
            if math.ceil((q ** i) * (q - 1) / B) < self.local_memory_in_server_blocks:
                self.local_memory_in_server_blocks -= math.ceil((q ** i) * (q - 1) / B)
                self.inner_tables.append(i)
        self.tables = [
            HashTable(
                RemoteRam(block_capacity=self.B, memory_size=0, local=(i in self.inner_tables)),
                self.B, 0
            ) for i in range(self.amount_of_levels + 1)
        ]
        # Initialize load factors for each level to zero.
        self.load_factors = [0] * (self.amount_of_levels + 1)
        self.init_oram()

    def access(self, op, addr, data):
        """
        Performs an oblivious access (read or write) to the Memory.

        The access procedure operates as follows:
          1. Scans the hierarchy of levels for the target address 'addr'. At each level with nonzero load,
             a lookup is performed via ht_lookup.
          2. Dummy lookups are performed in levels that are not the source of the accessed data to hide the access pattern.
          3. A new element containing the updated (addr, data) pair is created in a local RemoteRam instance.
          4. The level index 'j' is determined as the first level with a load factor less than q - 1.
          5. The new block is merged with data extracted from lower levels using concatenation (via RemoteRam.concat_memory_accesses).
          6. Depending on the level j:
             - For levels below the top, the hash table is rebuilt and its load factor is incremented.
             - For the highest level, if the level is full (load factor equals q - 1), compaction is performed.
          7. Finally, the accessed data is returned.

        Parameters:
          op: The operation type (e.g., read or write).
          addr: The address for the access.
          data: The data to be written (if op indicates a write).

        Returns:
          The data retrieved from the ORAM (for a read), or the old data (for a write).
        """
        found = False
        data_star = DUMMY

        # Search through each level for the element at 'addr'.
        for i in range(self.amount_of_levels + 1):
            if not found and self.load_factors[i] > 0:
                fetched = self.tables[i].ht_lookup(addr)
                if fetched != DUMMY:
                    data_star = fetched
                    found = True
            elif self.load_factors[i] > 0:
                # Perform dummy lookups in case the element was found.
                self.tables[i].ht_lookup("_")

        if not found:
            data_star = 0

        # Construct a new element with the relevant information.
        if op == READ_OPERATION:
            curr = (addr, data_star)
        else:
            curr = (addr, data)

        # Find the first level with load factor less than q-1.
        j = self.find_ht_index()

        # Create a local RemoteRam instance containing the new element, pad with dummies.
        u = RemoteRam(self.B, 1, [[curr] + [DUMMY for _ in range(self.B -1)]], local=True)

        # Merge the new block (u) with the data extracted from levels.
        if j < self.amount_of_levels:
            for i in range(j + 1):
                if self.tables[i].is_built:
                    u = RemoteRam.concat_memory_accesses(
                        u, self.tables[i].ht_extract(),
                        self.calc_ht_size(i - 1), self.calc_ht_size(i),
                        self.B
                    )
            self.load_factors[j] += 1
            # Rebuild the hash table at level j with the merged data.
            self.tables[j] = HashTable(u, self.B, self.calc_ht_size(level_index=j), local=(j in self.inner_tables))
            self.tables[j].ht_build()
            self.reset_tables(0, j)
        else:
            for i in range(j + 1):
                if self.tables[i].is_built:
                    u = RemoteRam.concat_memory_accesses(
                        u, self.tables[i].ht_extract(),
                        self.calc_ht_size(i - 1), self.calc_ht_size(i),
                        self.B
                    )
            # If the highest level is full, perform compaction.
            if self.load_factors[j] == self.q - 1:
                u_prime = compaction(u, u.memory_size * self.B, self.B, self.N)
            else:
                u_prime = u
            self.tables[j] = HashTable(u_prime, self.B, u_prime.memory_size * self.B)
            self.tables[j].ht_build()
            self.reset_tables(0, j)
            self.load_factors[j] = self.q - 1

        return data_star

    def find_ht_index(self):
        """
        Finds the first level index where the load factor is less than q-1.

        Returns:
          int: The index of the level where the new data can be inserted. If all levels are full,
               returns the index corresponding to amount_of_levels (i.e., a new level).
        """
        for index, load_factor in enumerate(self.load_factors):
            if load_factor < self.q - 1:
                return index
        return self.amount_of_levels

    def reset_tables(self, start, end):
        """
        Resets the hash tables and load factors for levels in the range [start, end).

        This method marks the specified tables as not built, clears their memory contents,
        and resets their load factors to zero.

        Parameters:
          start (int): The starting level index (inclusive).
          end (int): The ending level index (exclusive).
        """
        for i in range(start, end):
            self.tables[i].is_built = False
            self.tables[i].table = []
            self.load_factors[i] = 0

    def calc_ht_size(self, level_index):
        """
        Calculates the effective size (number of elements) of a given level in the hierarchy.

        For level 0, the size is equal to the load factor at level 0.
        For the highest level, the size is N.
        For intermediate levels, the size is determined by the expansion factor q and the current load factor.

        Parameters:
          level_index (int): The index of the level.

        Returns:
          int: The calculated size of the specified level.
        """
        if level_index == 0:
            return self.load_factors[0]
        elif level_index == self.amount_of_levels:
            return self.N
        else:
            return math.ceil(int(math.pow(self.q, level_index) * self.load_factors[level_index]))

    def init_oram(self):
        X = RemoteRam(block_capacity=self.B, memory_size=math.ceil(self.N / self.B))
        X.init_memory()
        self.tables[self.amount_of_levels] = HashTable(X=X, B=self.B, n=self.N)
        self.tables[self.amount_of_levels].ht_build()
        self.load_factors[self.amount_of_levels] = self.q - 1
        RemoteRam.read_operations = 0
        RemoteRam.write_operations = 0
