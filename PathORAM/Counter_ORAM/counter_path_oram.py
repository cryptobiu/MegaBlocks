import math
from PathORAM.Counter_ORAM.counter_local_pos_path_oram import CounterLocalPosPathORAM
from RemoteRam.counter_remote_ram import CounterRemoteRam
from MegaBlocksCode.MegaBlocks.config.utils import next_power_of_two_greater_or_equal


class CounterPathORAM:
    """
    A counter-based Path ORAM implementation.

    This class implements the Path ORAM protocol using a counter-based scheme. The ORAM tree
    is stored in a remote memory abstraction (CounterRemoteRam) and organized as a complete
    binary tree with a fixed bucket capacity (Z). The position map—used to map block addresses
    to random leaves—is implemented either locally (using CounterLocalPosPathORAM) or recursively,
    depending on the available local memory.

    Store the elements locally if there is enough space in the local memory (saved as tree and
    position map for convenience); otherwise, a recursive position map is employed. The number
    of levels in the ORAM tree is computed based on the rounded-up number of blocks (N),
    ensuring that the tree is complete.

    Parameters:
      N (int): The number of blocks allocated for the client. This value is rounded up to a power of two.
      b (int): The size (in bits) of each server block.
      Z (int): The capacity of each bucket in the ORAM tree (number of blocks per bucket).
      element_size (int): The size (in bits) of each element stored in a block.
      local_memory_capacity (int): The threshold (in server blocks) that determines whether elements are stored
                                   locally. If there is enough space, they will be stored locally (as the tree
                                   and position map for convenience). Otherwise, a recursive position map is used.
                                   Default is 2.

    Attributes:
      N (int): The adjusted (rounded-up) number of blocks.
      number_of_levels (int): The number of levels in the ORAM tree.
      local (bool): Indicates whether the elements are stored locally.
      pos_map: The position map instance (either a local or recursive instance).
      tree: The remote memory instance (CounterRemoteRam) that simulates the ORAM tree.
      stash (list): A temporary buffer used during data accesses.
    """

    def __init__(self, N, b, Z, element_size, local_memory_capacity=2):
        self.N = N
        self.b = b  # Size of each server block (in bits).
        self.number_of_levels = int(math.log(self.N, 2)) + 1
        self.Z = Z  # Bucket capacity.
        self.local_memory_capacity = local_memory_capacity
        self.local = False

        # Store the elements locally if there is enough space in the local memory
        # (saved as tree and position map for convenience); otherwise, use a recursive position map.
        if self.N < self.local_memory_capacity:
            self.N = next_power_of_two_greater_or_equal(N)
            self.number_of_levels = int(math.log(self.N, 2)) + 1
            self.pos_map = CounterLocalPosPathORAM(N=self.N, b=self.b, Z=self.Z)
            self.tree = CounterRemoteRam(
                memory_size=((2 * self.N) - 1) * self.Z,
                block_capacity=self.b // element_size,
                local=True
            )
            self.local = True
        else:
            self.N = next_power_of_two_greater_or_equal(N)
            self.number_of_levels = int(math.log(self.N, 2)) + 1
            self.pos_map = CounterPathORAM(
                N=math.ceil(self.N / (b // math.ceil(math.log(self.N, 2)))),
                b=self.b,
                Z=self.Z,
                local_memory_capacity=self.local_memory_capacity,
                element_size=math.ceil(math.log(self.N, 2))
            )
            self.tree = CounterRemoteRam(
                memory_size=((2 * self.N) - 1) * self.Z,
                block_capacity=self.b // element_size,
                local=False
            )

        self.stash = []  # Initialize an empty stash.

    def count_accesses(self):
        """
        Returns the total number of memory accesses incurred by the ORAM operations.

        When using a local position map, no recursive accesses are incurred (returns 0);
        otherwise, it counts twice the number of accesses for each level in the ORAM tree,
        plus the accesses made by the recursive position map.
        """
        if self.local:
            return 0
        return 2 * self.number_of_levels * self.Z + self.pos_map.count_accesses()
