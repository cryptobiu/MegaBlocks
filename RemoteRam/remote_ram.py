import random
import string
from config.constants import DUMMY, DUMMY_ADDR

class RemoteRam:
    """
    Simulates a remote memory module, which can be used to emulate remote RAM accesses
    in oblivious RAM (ORAM) constructions.

    Attributes:
      read_operations (int): A class-level counter tracking the total number of read operations.
      write_operations (int): A class-level counter tracking the total number of write operations.
      memory (list): A list of memory cells (blocks), each containing a list of elements.
      memory_size (int): The number of memory cells (blocks) in the module.
      block_capacity (int): The number of elements that can be stored in each memory cell.
      local (bool): A flag indicating whether this memory instance is considered local.
                   (Local memory accesses do not increment the operation counters.)
    """
    read_operations = 0
    write_operations = 0

    def __init__(self, block_capacity, memory_size, memory=None, local=False):
        """
        Initializes a RemoteRam instance.

        Parameters:
          block_capacity (int): The number of elements per memory block.
          memory_size (int): The total number of memory blocks.
          memory (list, optional): A pre-existing memory structure. If None, the memory is
                                   initialized to contain memory_size blocks, each filled with dummy entries.
          local (bool): If True, operations on this memory instance are considered local and do not count
                        towards global read/write operation counters.
        """
        self.memory_size = memory_size
        if memory is None:
            # Initialize memory with dummy values.
            memory = [[DUMMY] * block_capacity for _ in range(memory_size)]
        self.memory = memory
        self.block_capacity = block_capacity
        self.local = local

    def read_memory_cell(self, location):
        """
        Reads the memory cell (block) at the specified location.

        Parameters:
          location (int): The index of the memory cell to read.

        Returns:
          list: The content of the memory cell at the specified location.

        Raises:
          Exception: If the location is out of bounds.
        """
        if location > len(self.memory) - 1 or location < 0:
            raise Exception(f"Invalid attempt to read memory cell. Index value is {location}, memory size is {self.memory_size}")
        if not self.local:
            RemoteRam.read_operations += 1
        return self.memory[location]

    def write_memory_cell(self, location, element):
        """
        Writes the given element to the memory cell at the specified location.

        Parameters:
          location (int): The index of the memory cell to write to.
          element (list): The element (typically a block of data) to write.

        Raises:
          Exception: If the location is out of bounds.
        """
        if location > len(self.memory) - 1 or location < 0:
            raise Exception(f"Invalid attempt to write memory cell. Index value is {location}, memory size is {self.memory_size}")
        if not self.local:
            RemoteRam.write_operations += 1
        self.memory[location] = element

    def init_memory(self):
        """
        Initializes the memory with a mix of real and dummy elements.

        For the first 'real_elements' positions, a random string is generated and paired with an increasing index.
        The remaining positions in each block are filled with dummy entries.

        Parameters:
          real_elements (int): The total number of real elements to initialize in memory.
        """
        for i in range(self.memory_size):
            block_i = []
            for j in range(self.block_capacity):
                data = "d" + str(i * self.block_capacity + j)
                block_i.append((i * self.block_capacity + j, data))
            self.memory[i] = block_i

    def __add__(self, other):
        """
        Overloads the '+' operator to concatenate two RemoteRam instances.

        The resulting RemoteRam has the same block capacity and a memory size equal to the sum
        of the two instances' memory sizes. The memory contents are concatenated.

        Parameters:
          other (RemoteRam): Another RemoteRam instance.

        Returns:
          RemoteRam: A new RemoteRam instance representing the concatenation.
        """
        return RemoteRam(self.block_capacity, self.memory_size + other.memory_size, self.memory + other.memory)

    @staticmethod
    def concat_memory_accesses(mem1, mem2, capacity1, capacity2, block_size):
        """
        Concatenates the memory accesses of two RemoteRam instances.

        If the sum of capacities (capacity1 + capacity2) is less than or equal to the block_size,
        then the blocks are merged into one using merge_blocks. Otherwise, the memory arrays are simply concatenated.

        Parameters:
          mem1 (RemoteRam): The first memory instance.
          mem2 (RemoteRam): The second memory instance.
          capacity1 (int): The effective capacity used in mem1.
          capacity2 (int): The effective capacity used in mem2.
          block_size (int): The size of a block.

        Returns:
          RemoteRam: A new RemoteRam instance representing the concatenated result.
        """
        if (capacity1 + capacity2) <= block_size:
            return RemoteRam(
                block_capacity=block_size,
                memory_size=1,
                memory=[RemoteRam.merge_blocks(mem1.memory[0], mem2.memory[0], block_size, capacity1, capacity2)],
                local=True
            )
        else:
            return RemoteRam(
                block_capacity=block_size,
                memory_size=mem1.memory_size + mem2.memory_size,
                memory=mem1.memory + mem2.memory,
                local=mem1.local and mem2.local
            )

    @staticmethod
    def merge_blocks(block1, block2, block_capacity, capacity1, capacity2):
        """
        Merges two blocks of data into a single block, preserving non-dummy elements.

        For each index in the range of block_capacity, if the element in block1 or block2 is not dummy,
        it is appended to the new block. The new block is then padded with dummy entries to reach the block_capacity.

        Parameters:
          block1 (list): The first block (list of elements).
          block2 (list): The second block.
          block_capacity (int): The target capacity of the merged block.
          capacity1 (int): The effective number of valid elements in block1 (not used directly here).
          capacity2 (int): The effective number of valid elements in block2 (not used directly here).

        Returns:
          list: The merged block of data, padded with dummy entries.
        """
        new_block = []
        for i in range(block_capacity):
            if block1[i][0] != DUMMY_ADDR:
                new_block.append(block1[i])
            if block2[i][0] != DUMMY_ADDR:
                new_block.append(block2[i])
        # Pad the block with dummy entries if necessary.
        return new_block + [DUMMY] * (block_capacity - len(new_block))
