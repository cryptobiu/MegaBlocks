import hashlib
import hmac
import math
import random
import secrets

from MegaBlocksORAM.Real_ORAM.bin_packing import bin_packing
from RemoteRam.remote_ram import RemoteRam
from config.constants import DUMMY, DUMMY_ADDR
from config.utils import choose_C


def compaction(X, n, B, n_0):
    """
    Implements the oblivious compaction procedure as introduced in the paper.

    This function compacts the real elements from the input memory array X into a new output array.
    Here, n_0 is an upper bound on the number of real elements in X (i.e., N), and the output array
    will have size n_0/B blocks.

    Procedure:
      1. Process each block of X (of size B) by computing a randomized destination index for each element.
         For non-dummy elements, the index is computed via HMAC (using a secret key); dummy elements (marked
         with DUMMY_ADDR) are assigned a random index.
      2. Each block is split into two halves, and each element is tagged with metadata (its current cell index
         and its position within the half).
      3. The processed blocks are stored in an intermediate array X_prime, padded with dummy blocks.
      4. The oblivious bin packing algorithm (bin_packing) routes the elements into destination bins.
      5. Finally, the output array is constructed by sequentially reading bins from Y_buckets and packing the
         non-dummy elements into blocks. Any remaining blocks in the output array are filled with dummy blocks.

    Parameters:
      X (RemoteRam): The input memory array containing the elements to be compacted.
      n (int): The total number of logical elements in X.
      B (int): The block capacity (number of elements per block).
      n_0 (int): An upper bound on the number of real elements in X. The output array will have n_0/B blocks.

    Returns:
      RemoteRam: A new memory array containing the compacted data in n_0/B blocks.
    """
    secret_key = secrets.token_bytes(32)
    dummies = [DUMMY] * (B // 2)
    size_of_compact_array = math.ceil(n_0 / B)
    size_of_X = math.ceil(n / B)
    C = choose_C(n, B)

    # Create an intermediate memory array to store processed blocks.
    X_prime = RemoteRam(memory_size=C, block_capacity=B)

    # Process each block in X.
    for i in range(size_of_X):
        curr_cell = X.read_memory_cell(i)
        for j in range(B):
            if curr_cell[j][0] == DUMMY_ADDR:
                # Assign a random bin index for dummy elements.
                item_key = random.randint(0, C - 1)
            else:
                # Compute a keyed hash to obtain the bin index for real elements.
                item_key = int.from_bytes(
                    hmac.new(secret_key, str(curr_cell[j][0]).encode('utf-8'),
                             hashlib.sha256).digest(),
                    "big") % C
            # Append the computed key to the element.
            curr_cell[j] = curr_cell[j] + (item_key,)

        # Split the block into two halves and tag each element.
        first_half = [item + (2 * i, index) for index, item in enumerate(curr_cell[:B // 2])]
        second_half = [item + (2 * i + 1, index) for index, item in enumerate(curr_cell[B // 2:])]

        # Write the processed halves to X_prime, padding with dummies.
        X_prime.write_memory_cell(2 * i, first_half + dummies)
        X_prime.write_memory_cell(2 * i + 1, second_half + dummies)

    # Pad remaining cells in X_prime with dummy blocks.
    for j in range(2 * size_of_X, C):
        X_prime.write_memory_cell(j, [DUMMY] * B)

    # Obliviously route the elements into bins.
    Y_buckets = bin_packing(X_prime, n, B, key_index=2)

    # Create the output memory array for the compacted data.
    new_array = RemoteRam(memory_size=size_of_compact_array, block_capacity=B)
    curr_index = 0
    curr_bin = 0
    current_block = []

    # Collect non-dummy elements from each bin in Y_buckets.
    for i in range(C):
        block_i = Y_buckets.read_memory_cell(i)
        for j in range(B):
            if block_i[j][0] != DUMMY_ADDR:
                current_block.append((block_i[j][0], block_i[j][1]))
                curr_index += 1
                # If the block is full, write it to new_array.
                if curr_index == B:
                    new_array.write_memory_cell(curr_bin, current_block)
                    curr_bin += 1
                    curr_index = 0
                    current_block = []

    # Write any remaining elements to new_array and adjust its size.
    if current_block and curr_index < B:
        new_array.write_memory_cell(curr_bin, current_block + ([DUMMY] * (B - len(current_block))))
        curr_bin += 1

    # Fix: Fill any remaining blocks in new_array with dummy blocks.
    for i in range(curr_bin, size_of_compact_array):
        new_array.write_memory_cell(i, [DUMMY] * B)

    return new_array
