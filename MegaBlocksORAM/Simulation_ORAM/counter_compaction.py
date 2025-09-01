import math
from MegaBlocksORAM.Simulation_ORAM.counter_bin_packing import bin_packing
from RemoteRam.counter_remote_ram import CounterRemoteRam
from config.utils import choose_C


def compaction(X, n, B, n_0):
    """
    Simulates the oblivious compaction procedure (as described in the paper) in the counter model.

    Parameters:
      X (CounterRemoteRam): Input memory array.
      n (int): Total number of logical elements in X.
      B (int): Block capacity (number of elements per block).
      n_0 (int): Upper bound on the number of real elements in X (output array has size n_0/B blocks).

    Returns:
      CounterRemoteRam: A new memory array representing the compacted output.

    The function increments the CounterRemoteRam read and write counters to simulate the I/O overhead of the
    real compaction procedure.
    """
    size_of_X = math.ceil(n / B)
    C = choose_C(n, B)
    size_of_compact_array = math.ceil(n_0 / B)

    # Create an intermediate memory instance.
    X_prime = CounterRemoteRam(memory_size=C, block_capacity=B)

    # Simulate the I/O of processing the input blocks:
    CounterRemoteRam.write_operations += 2 * size_of_X  # Two writes per processed block.
    CounterRemoteRam.read_operations += size_of_X  # One read per processed block.

    # Simulate padding: writing remaining dummy blocks.
    CounterRemoteRam.write_operations += (C - 2 * size_of_X)

    # Perform oblivious bin packing, which itself increments counters.
    Y_buckets = bin_packing(X_prime, n, B, key_index=2)

    # Create the output memory instance.
    new_array = CounterRemoteRam(memory_size=size_of_compact_array, block_capacity=B)

    # Simulate reading all blocks from the bin-packed output.
    CounterRemoteRam.read_operations += C

    # Simulate writing the compacted output blocks.
    CounterRemoteRam.write_operations += size_of_compact_array

    return new_array
