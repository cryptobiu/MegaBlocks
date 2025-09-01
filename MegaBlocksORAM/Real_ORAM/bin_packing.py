import math

from RemoteRam.remote_ram import RemoteRam
from config.constants import DUMMY
from config.utils import is_dummy, get_msb_at_index, choose_C


def bin_packing(X, n, B, key_index, local=False):
    """
    Implements oblivious bin packing.

    Parameters:
      X (RemoteRam): An array X with 2n elements packed in C blocks (C = round up 2n/B to the next power of 2).
      n (int): The total number of elements.
      B (int): The size of each block in the array X.
      key_index (int): The index within an element where the destination bin is stored.
      local (bool): Flag indicating whether the memory used is local (default is False).

    Returns:
      RemoteRam: A RemoteRam instance containing the elements in X placed into their destination bins.

    Raises:
      Exception: If an overflow occurs during bin packing.
    """
    # Determine the number of bins (C) and the number of levels (m)
    C = choose_C(n, B)
    m = math.floor(math.log2(C)) + 1
    # Create an array of RemoteRam instances for each level
    a_arrays = [RemoteRam(B, C, local=local) for _ in range(m)]
    a_arrays[0] = X  # The initial level is the input array X

    # Process each level to merge and split elements into bins
    for i in range(m - 1):
        for j in range(C // 2):
            # Compute the offset for current bin grouping based on level i
            j_prime = math.floor(j / (2 ** i)) * (2 ** i)
            # Read two adjacent cells from the current level
            a_0 = a_arrays[i].read_memory_cell(j + j_prime)
            a_1 = a_arrays[i].read_memory_cell(j + j_prime + 2 ** i)
            # Merge and split the two cells into two new bins based on the (i+1)th MSB
            b_0, b_1 = merge_split(a_0, a_1, i, B, (C - 1).bit_length(), key_index)
            if b_0 != "Overflow":
                a_arrays[i + 1].write_memory_cell(2 * j, b_0)
                a_arrays[i + 1].write_memory_cell(2 * j + 1, b_1)
            else:
                raise Exception("Overflow on bin packing.")
    # Return the final level containing the packed bins
    return a_arrays[m - 1]


def merge_split(a_0, a_1, i, B, bit_length, key_index):
    """
    Merges two blocks and splits the elements into two bins based on the (i+1)th most significant bit.

    Parameters:
      a_0 (list): The first block of elements.
      a_1 (list): The second block of elements.
      i (int): Current level index.
      B (int): The block capacity.
      bit_length (int): The bit length used to represent the destination bin.
      key_index (int): The index within an element where the destination bin is stored.

    Returns:
      tuple: Two lists, each representing a bin of size B (padded with dummies if necessary).
             Returns ("Overflow", "Overflow") if either bin exceeds capacity.
    """
    b_0 = []
    b_1 = []

    # Process each element in both blocks
    for j in range(B):
        if not is_dummy(a_0[j]):
            # Use the (i+1)th most significant bit to decide the bin
            if get_msb_at_index(a_0[j][key_index], i + 1, bit_length) == 0:
                b_0.append(a_0[j])
            else:
                b_1.append(a_0[j])
        if not is_dummy(a_1[j]):
            if get_msb_at_index(a_1[j][key_index], i + 1, bit_length) == 0:
                b_0.append(a_1[j])
            else:
                b_1.append(a_1[j])

    # Check if any bin exceeds the capacity B
    if len(b_0) > B or len(b_1) > B:
        return "Overflow", "Overflow"

    # Pad the bins with dummy elements if needed and return
    return b_0 + [DUMMY] * (B - len(b_0)), b_1 + [DUMMY] * (B - len(b_1))
