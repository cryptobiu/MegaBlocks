import math
import secrets
from config.utils import choose_C
from MegaBlocksORAM.Simulation_ORAM.counter_bin_packing import bin_packing
from RemoteRam.counter_remote_ram import CounterRemoteRam


class HashTable:
    """
    Counter version of an oblivious hash table (HT) for MegaBlocks ORAM.

    The hash table is built from an input array X of n elements (packed into n/B memory words, each of capacity B).
    Each element is a pair (k, v) (some of which may be dummy). The table size is determined by choose_C(n, B).
    I/O operations are simulated by incrementing CounterRemoteRam's counters.
    """

    def __init__(self, X, B, n, local=False):
        """
        Initializes the counter hash table.

        Parameters:
          X (CounterRemoteRam): The input memory array.
          block_capacity (int): Number of elements per memory block.
          data_size (int): Total number of elements.
          local (bool): If True, operations are local (not counted).
        """
        self.is_built = False
        self.local = local
        self.X = X
        self.X.local = local
        self.n = n
        self.B = B
        self.C = choose_C(self.n, self.B)
        self.secret_key = secrets.token_bytes(32)
        self.table = CounterRemoteRam(block_capacity=self.B, memory_size=self.C, local=self.local)

    def ht_build(self):
        """
        Simulates building the hash table (HT.Build) by incrementing I/O counters.

        The procedure calculates the number of memory cells (size_of_X) in X and simulates:
          - Reading each cell once (size_of_X reads)
          - Writing two cells per block (2 * size_of_X writes)
          - Writing dummy cells for the remaining cells up to C.
        Then it performs counter bin packing (using key_index=2) to form the table.
        """
        counter = 0
        if not self.local:
            size_of_X = math.ceil(self.n / self.B)
            X_prime = CounterRemoteRam(memory_size=self.C, block_capacity=self.B, local=self.local)
            CounterRemoteRam.read_operations += size_of_X
            CounterRemoteRam.write_operations += self.C
            counter += size_of_X + self.C
            self.table, num = bin_packing(X_prime, self.n, self.B, key_index=2, local=self.local)
            counter += num
        self.is_built = True

    def ht_lookup(self, k):
        """
        Simulates a hash table lookup.

        For a lookup on key k, the function simulates a read and write on the table at index k.
        """
        counter = 0
        if not self.local:
            self.table.read_memory_cell(k)
            self.table.write_memory_cell(k)
            counter += 2
        return counter

    def ht_extract(self):
        """
        Simulates extracting the original array from the hash table (HT.Extract).

        The table is reverse-routed using counter bin packing (with key_index=3), and the I/O counters
        are incremented to reflect reading all cells and writing half as many cells.

        Returns:
          CounterRemoteRam: A new memory instance with memory_size set to ceil(n/B).
        """
        counter = 0
        if not self.is_built:
            return 0
        Y_buckets, num = bin_packing(self.table, self.n, self.B, 3, local=self.local)
        X_prime = CounterRemoteRam(memory_size=self.C // 2, block_capacity=self.B, local=self.local)
        if not self.local:
            CounterRemoteRam.read_operations += self.C
            CounterRemoteRam.write_operations += (self.C // 2)
            counter += self.C + (self.C // 2) + num
        X_prime.memory_size = math.ceil(self.n / self.B)
        return X_prime
