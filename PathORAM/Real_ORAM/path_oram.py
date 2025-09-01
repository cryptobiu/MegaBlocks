import random
import math
from PathORAM.Real_ORAM.local_pos_path_oram import LocalPosPathORAM
from RemoteRam.remote_ram import RemoteRam
from config.constants import WRITE_OPERATION, DUMMY
from config.utils import next_power_of_two_greater_or_equal


class PathORAM:
    """
    PathORAM implements the Path Oblivious RAM protocol with support for both direct data accesses
    and recursive position map accesses. The ORAM tree is stored in a remote memory abstraction,
    organized as a binary tree of buckets, while the position map is maintained either locally
    (using LocalPosPathORAM) or recursively (by instantiating another PathORAM) based on available local memory.

    The design uses a power-of-two rounded number of blocks (N) to create a complete binary tree.
    When the total number of blocks is small enough (i.e. less than the specified local_memory_capacity),
    the position map and tree are stored in local memory for efficiency. Otherwise, a recursive mechanism
    is employed.

    Parameters:
      N (int): The number of blocks in the client’s working set. This value is rounded up to a power of two.
      b (int): The size (in bits) of each server block.
      Z (int): The capacity (number of blocks) per bucket in the ORAM tree.
      element_size (int): The size (in bits) of each data element.
      local_memory_capacity (int): The threshold (in server blocks) that determines whether to store the
                                   position map and tree locally. If N is smaller than this capacity,
                                   a local position map is used.
      upper_level_N (int): The number of elements for the upper-level position map (if any). Defaults to 0.
    """

    def __init__(self, N, b, Z, element_size, local_memory_capacity=2, upper_level_N=0):

        self.N = N
        self.b = b  # Server block size in bits.
        self.B = b // element_size  # Number of elements per block.
        self.upper_level_N = upper_level_N
        self.Z = Z  # Bucket capacity.
        self.local_memory_capacity = local_memory_capacity

        # Decide whether to store the position map and tree locally or recursively.
        # If there is enough space in local memory (i.e. N is below the threshold),
        # the elements are stored locally (both the tree and the position map).
        if self.N < self.local_memory_capacity:
            self.N = next_power_of_two_greater_or_equal(self.N)
            self.number_of_levels = int(math.log(self.N, 2)) + 1
            self.pos_map = LocalPosPathORAM(N=self.N, b=self.b, Z=self.Z)
            self.tree = RemoteRam(
                memory_size=((2 * self.N) - 1) * self.Z,
                block_capacity=self.B,
                local=True
            )
        else:
            self.N = next_power_of_two_greater_or_equal(self.N)
            self.number_of_levels = int(math.log(self.N, 2)) + 1
            self.pos_map = PathORAM(
                N=math.ceil(self.N / (b // math.ceil(math.log(self.N, 2)))),
                b=self.b,
                Z=self.Z,
                element_size=math.ceil(math.log(self.N, 2)),
                local_memory_capacity=self.local_memory_capacity,
                upper_level_N=self.N
            )
            self.tree = RemoteRam(
                memory_size=((2 * self.N) - 1) * self.Z,
                block_capacity=self.B
            )
        self.stash = []  # Initialize the stash to temporarily hold blocks.

    def access(self, op, addr, data):
        """
        Performs an ORAM access (read or write) for a given block address.

        The process involves:
          1. Updating the position map entry for the given address (obtaining old and new leaf labels).
          2. Reading all buckets along the path from the root to the old leaf.
          3. Merging the blocks from the fetched path into the local stash.
          4. Searching the stash for the block with the specified address. If found, its leaf label is updated
             (and its data is updated if this is a write). If not found and writing, a new block is appended.
          5. Truncating the stash and writing back as many blocks as possible along the accessed path.

        Parameters:
          op: The operation type (e.g. WRITE_OPERATION for writes, or a read indicator for reads).
          addr: The logical address of the block.
          data: The data to be written if op is WRITE_OPERATION.

        Returns:
          The old data for a read operation, or None if the block was not found.
        """
        # Step 1: Obtain the old and new leaf labels by updating the position map.
        old_leaf, new_leaf = self.pos_map.pos_map_access(addr)
        result = None

        # Step 2: Read the entire path corresponding to the old leaf.
        path = self.read_path(old_leaf)

        # Merge all blocks along the path into the stash.
        for block in path:
            self.stash.extend(block)

        # Step 3: Look for the block with the given address in the stash.
        for i, element in enumerate(self.stash):
            if element[0] == addr:
                result = element[1]  # Retrieve the current data.
                # Update data if this is a write, or keep the read result.
                new_data = data if op == WRITE_OPERATION else result
                self.stash[i] = (element[0], new_data, new_leaf)
                break
        # If writing and the block was not found, add a new block to the stash.
        if op == WRITE_OPERATION and result is None:
            self.stash.append((addr, data, new_leaf))

        # Step 4: Truncate the stash and write back blocks along the accessed path.
        self.truncate_stash_and_write_back(old_leaf)
        return result

    def pos_map_access(self, upper_level_addr):
        """
        Performs a recursive position map access for an upper-level address.

        This method splits the upper-level address into a block index and an offset,
        retrieves the corresponding mapping from the position map (stored in blocks),
        updates the mapping, and integrates the retrieved blocks into the local stash.
        Finally, it writes back the updated mapping along the accessed path.

        Parameters:
          upper_level_addr: The address within the upper-level (position map) space.

        Returns:
          A tuple (upper_level_old_leaf, upper_level_new_leaf) representing the old and new leaf labels for
          the mapping entry.
        """
        pos_map_addr = int(upper_level_addr / self.B)
        old_leaf, new_leaf = self.pos_map.pos_map_access(pos_map_addr)
        path = self.read_path(old_leaf)
        upper_level_old_leaf = None
        upper_level_new_leaf = None

        for block in path:
            self.stash.extend(block)

        for i, element in enumerate(self.stash):
            if element[0] == pos_map_addr:
                addr_list = element[1]
                upper_level_old_leaf = addr_list[upper_level_addr % self.B]
                upper_level_new_leaf = self.generate_random_upper_leaf()
                addr_list[upper_level_addr % self.B] = upper_level_new_leaf
                self.stash[i] = (pos_map_addr, addr_list, new_leaf)

        if upper_level_old_leaf is None:
            pos_list = [self.generate_random_upper_leaf() for _ in range(self.B)]
            upper_level_new_leaf = self.generate_random_upper_leaf()
            pos_list[upper_level_addr % self.B] = upper_level_new_leaf
            upper_level_old_leaf = self.generate_random_upper_leaf()
            element = (pos_map_addr, pos_list, new_leaf)
            self.stash.append(element)

        self.truncate_stash_and_write_back(old_leaf)
        return upper_level_old_leaf, upper_level_new_leaf

    def split_and_pad_bucket(self, bucket):
        """
        Splits a bucket into fixed-size blocks and pads with dummy entries if necessary.

        Given a bucket (a list representing its contents), if the bucket contains fewer than
        (Z * B) elements, it is padded with DUMMY entries. Then the bucket is divided into exactly
        Z blocks, each with B elements.

        Parameters:
          bucket (list): The list of elements from a bucket.

        Returns:
          A list of Z blocks (each of fixed size B).
        """
        blocks = []
        if len(bucket) < self.Z * self.B:
            bucket = bucket + [DUMMY for _ in range(self.Z * self.B - len(bucket))]
        for i in range(self.Z):
            blocks.append(bucket[i * self.B: (i + 1) * self.B])
        return blocks

    def read_path(self, leaf):
        """
        Reads all buckets along the path from the root of the ORAM tree to a given leaf.

        For a complete binary tree with 'number_of_levels' levels (level 0 is the root, level L-1 are leaves),
        the path is determined by the binary representation of the leaf label.

        Returns:
          A list of all blocks read from the buckets along the path.
        """
        path = []
        L = self.number_of_levels
        for i in range(L):
            starting_index = (2 ** i - 1) * self.Z
            bucket_index = leaf >> (L - 1 - i)
            base_index = starting_index + bucket_index * self.Z
            for j in range(self.Z):
                cell_index = base_index + j
                if cell_index >= ((2 * self.N) - 1) * self.Z:
                    a= 1
                path.append(self.tree.read_memory_cell(cell_index))
        return path

    def write_path(self, buckets, leaf):
        """
        Writes a series of buckets back to the remote memory along the path from the root to a given leaf.

        For each level in the ORAM tree, this method computes the appropriate memory cell indices based on
        the leaf label and writes the corresponding bucket blocks.

        Parameters:
          buckets (list): A list of buckets (each a list of blocks) indexed by level.
          leaf (int): The leaf label that identifies the path.
        """
        L = self.number_of_levels
        for i in range(L):
            starting_index = (2 ** i - 1) * self.Z
            bucket_index = leaf >> (L - 1 - i)
            base_index = starting_index + bucket_index * self.Z
            for j in range(self.Z):
                cell_index = base_index + j
                self.tree.write_memory_cell(cell_index, buckets[i][j])

    def generate_random_upper_leaf(self):
        """
        Generates a random leaf label for the upper-level address space.

        Returns:
          An integer selected uniformly at random from the range [0, upper_level_N).
        """
        return random.randint(0, self.upper_level_N - 1)

    def truncate_stash_and_write_back(self, old_leaf):
        """
        Evicts blocks from the stash along the path corresponding to the provided leaf.

        This method scans the stash for blocks whose assigned leaf matches the prefix of old_leaf
        (determined per level), groups them into buckets, pads the buckets to a fixed size, and writes
        the resulting buckets back to remote memory along the same path.

        Parameters:
          old_leaf (int): The leaf label used to identify the path for eviction.
        """
        write_back = []
        for i in range(self.number_of_levels):
            current_bucket = []
            # Iterate over a copy of the stash to safely remove eligible blocks.
            for element in list(self.stash):
                if element == DUMMY:
                    self.stash.remove(element)
                elif element != DUMMY and (element[2] >> (self.number_of_levels - 1 - i)) == (
                        old_leaf >> (self.number_of_levels - 1 - i)):
                    current_bucket.append(element)
                    self.stash.remove(element)
                    if len(current_bucket) == self.Z * self.B:
                        break
            write_back.append(self.split_and_pad_bucket(current_bucket))
        self.write_path(write_back, old_leaf)
