class CounterRemoteRam:
    """
    Simulates remote memory accesses by counting read and write operations.
    This counter-only version does not store actual memory content.

    Attributes:
      read_operations (int): Total number of read operations performed.
      write_operations (int): Total number of write operations performed.
    """
    read_operations = 0
    write_operations = 0

    def __init__(self, block_capacity, memory_size, local=False):
        """
        Initializes the counter remote memory instance.

        Parameters:
          block_capacity (int): Number of elements per memory cell.
          memory_size (int): Total number of memory cells.
          local (bool): If True, operations are considered local (not counted).
        """
        self.memory_size = memory_size
        self.block_capacity = block_capacity
        self.local = local

    def read_memory_cell(self, location):
        """
        Simulates a read operation on a memory cell at the given location.
        Increments the read counter if the instance is not local.

        Parameters:
          location (int): The index in the simulated memory.

        Raises:
          Exception: If the location is invalid.
        """
        if location > self.memory_size * self.block_capacity - 1 or location < 0:
            raise Exception(
                f"Invalid attempt to read memory cell. Index value is {location}, memory size is {self.memory_size}")
        if not self.local:
            CounterRemoteRam.read_operations += 1

    def write_memory_cell(self, location):
        """
        Simulates a write operation on a memory cell at the given location.
        Increments the write counter if the instance is not local.

        Parameters:
          location (int): The index in the simulated memory.

        Raises:
          Exception: If the location is invalid.
        """
        if location > self.memory_size * self.block_capacity - 1 or location < 0:
            raise Exception(
                f"Invalid attempt to write memory cell. Index value is {location}, memory size is {self.memory_size}")
        if not self.local:
            CounterRemoteRam.write_operations += 1

    def __add__(self, other):
        """
        Concatenates two CounterRemoteRam instances by summing their memory sizes.

        Returns:
          CounterRemoteRam: A new instance with the combined memory size.
        """
        return CounterRemoteRam(self.block_capacity, self.memory_size + other.memory_size)

    def add_write_operations(self, num_operations):
        """
        Adds a specified number of write operations to the counter.

        Parameters:
          num_operations (int): The number of operations to add.
        """
        if not self.local:
            CounterRemoteRam.write_operations += num_operations

    def add_read_operations(self, num_operations):
        """
        Adds a specified number of read operations to the counter.

        Parameters:
          num_operations (int): The number of operations to add.
        """
        if not self.local:
            CounterRemoteRam.read_operations += num_operations

    @staticmethod
    def concat_memory_accesses(mem1, mem2, capacity1, capacity2, block_size):
        """
        Concatenates two CounterRemoteRam instances.

        If the sum of capacities is at most the block size, returns a new instance with memory size 1.
        Otherwise, returns the sum of the two instances.

        Parameters:
          mem1 (CounterRemoteRam): The first memory instance.
          mem2 (CounterRemoteRam): The second memory instance.
          capacity1 (int): Effective capacity of mem1.
          capacity2 (int): Effective capacity of mem2.
          block_size (int): The block size.

        Returns:
          CounterRemoteRam: The concatenated memory instance.
        """
        if (capacity1 + capacity2) <= block_size:
            return CounterRemoteRam(block_capacity=block_size, memory_size=1)
        else:
            return mem1 + mem2
