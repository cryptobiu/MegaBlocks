import math
from RemoteRam.counter_remote_ram import CounterRemoteRam
from config.utils import choose_C

def bin_packing(X, n, B, key_index, local=False):
    """
    Implements oblivious bin packing for the counter ORAM.

    This counter version simulates the operation counts of the oblivious bin packing procedure
    without performing the actual merge-split operations. Given an input array X with 2n elements
    packed in 2n/B blocks, it computes the number of bins (C) and the number of levels (m), then
    directly increments the read and write counters by the same number of operations that would be
    executed in the real version.

    Parameters:
      X (CounterRemoteRam): The input memory array.
      n (int): The total number of logical elements.
      B (int): The block capacity (number of elements per block).
      key_index (int): The index indicating the destination bin in each element.
      local (bool): If True, the memory is local and operations are not counted.

    Returns:
      CounterRemoteRam: The final memory array after simulated bin packing.
    """
    C = choose_C(n, B)
    m = math.floor(math.log2(C)) + 1
    a_arrays = [CounterRemoteRam(B, C, local=local) for _ in range(m)]
    a_arrays[0] = X
    if not local:
        # Simulate the read and write operations of the merge-split loop:
        # Each of the (m-1) levels and for each j in range(C // 2) performs 2 reads and 2 writes.
        CounterRemoteRam.write_operations += 2 * (m - 1) * (C // 2)
        CounterRemoteRam.read_operations += 2 * (m - 1) * (C // 2)
    return  a_arrays[m - 1], 4 * (m-1) * (C // 2)
