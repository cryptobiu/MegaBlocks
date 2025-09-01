import math
import hmac
import hashlib
import random
import secrets
from MegaBlocksORAM.Real_ORAM.bin_packing import bin_packing
from config.constants import DUMMY, DUMMY_ADDR, ACCESSED_MARK
from config.utils import choose_C
from RemoteRam.remote_ram import RemoteRam


class HashTable:
    """
    Implements an oblivious non-recurrent hash table as described in the paper.

    The hash table is built from an input array X containing n elements spread over n/B memory words,
    where each memory word is of capacity B. Each element is a pair (k, v) and some elements may be dummy.
    The table size (number of buckets) is determined via the function choose_C based on n and B.

    Parameters:
      X (RemoteRam): The input memory array containing the items.
      B (int): The capacity of each memory block (B in the paper).
      n (int): The total number of elements.
      local (bool): Flag indicating if the memory used is local. Default is False.
    """
    def __init__(self, X, B, n, local=False):
        self.is_built = False
        self.X = X
        self.X.local = local
        self.n = n
        self.B = B
        self.C = choose_C(self.n, self.B)  # Number of buckets (table size)
        self.secret_key = secrets.token_bytes(32)  # 128-bit key for PRF
        self.local = local
        # Initialize the hash table memory; note: if n is not divisible by B, rounding up may be needed.
        self.table = RemoteRam(block_capacity=self.B, memory_size=self.C, local=self.local)

    def ht_build(self):
        """
        Builds the oblivious hash table (HT.Build(X)) as described in the paper.

        Procedure:
          1. Process the input array X block by block. For each element in a block:
             - If the element is a dummy (identified by DUMMY_ADDR), assign a random bin index.
             - Otherwise, compute the bin index using HMAC with a secret key.
          2. Append the computed bin index to each element.
          3. Split each block into two halves, tagging each element with its originating block index and position.
          4. Write the processed halves into an intermediate array (X_prime), padding with dummies as needed.
          5. Pad any remaining cells in X_prime.
          6. Apply the oblivious bin packing algorithm (bin_packing) to route the elements into their destination bins.
          7. Store the resulting packed bins in self.table and mark the hash table as built.
        """
        if self.C > 1:
            size_of_X = math.ceil(self.n / self.B)
            dummies = [DUMMY] * (self.B // 2)
            # Create an intermediate memory array X_prime with C blocks.
            X_prime = RemoteRam(memory_size=self.C, block_capacity=self.B, local=self.local)
            for i in range(size_of_X):
                curr_cell = self.X.read_memory_cell(i)
                # Process each element in the current block.
                for j in range(self.B):
                    if curr_cell[j][0] == DUMMY_ADDR:
                        # Assign a random bin index for dummy elements.
                        item_key = random.randint(0, self.C - 1)
                    else:
                        # For real elements, compute the bin index via HMAC.
                        item_key = int.from_bytes(
                            hmac.new(self.secret_key, str(curr_cell[j][0]).encode('utf-8'),
                                     hashlib.sha256).digest(),
                            "big") % self.C
                    # Append the computed key to the element.
                    curr_cell[j] = curr_cell[j] + (item_key,)
                # Split the block into two halves; the additional tuple entries tag the element's source block and position.
                first_half = [item + (2 * i, index) for index, item in enumerate(curr_cell[:self.B // 2])]
                second_half = [item + (2 * i + 1, index) for index, item in enumerate(curr_cell[self.B // 2:])]
                # Write the processed halves to X_prime, padding with dummies.
                X_prime.write_memory_cell(2 * i, first_half + dummies)
                X_prime.write_memory_cell(2 * i + 1, second_half + dummies)
            # Pad remaining cells in X_prime with dummy blocks.
            for j in range(2 * size_of_X, self.C):
                X_prime.write_memory_cell(j, [DUMMY for _ in range(self.B)])
            # Apply oblivious bin packing to obtain the hash table.
            self.table = bin_packing(X_prime, self.n, self.B, key_index=2, local=self.local)
        else:
            self.table = self.X
        self.is_built = True

    def ht_lookup(self, k):
        """
        Performs an oblivious lookup (HT.Lookup(k)) in the hash table.

        Procedure:
          1. If k is a dummy key (DUMMY_ADDR), assign a random bin index.
             Otherwise, compute the bin index using HMAC with the secret key.
          2. Read the corresponding memory cell (bucket) from the hash table.
          3. Search the bucket for an element with key k.
             - If found, mark the element as accessed (by appending ACCESSED_MARK) and return its (k, v) pair.
             - If not found, return a dummy element.
          4. Write the updated bucket back to the hash table.

        Parameters:
          k: The key to be looked up.

        Returns:
          The (k, v) pair if found; otherwise, a dummy element.
        """
        if k == DUMMY_ADDR:
            item_key = random.randint(0, self.C - 1)
        else:
            item_key = int.from_bytes(
                hmac.new(self.secret_key, str(k).encode('utf-8'), hashlib.sha256).digest(),
                "big") % self.C
        current_cell = self.table.read_memory_cell(item_key)
        item = None
        # Only search for real keys.
        if k != DUMMY_ADDR:
            for i in range(self.B):
                if current_cell[i][0] == k:
                    item = (current_cell[i][0], current_cell[i][1])
                    # Mark the element as accessed.
                    current_cell[i] += (ACCESSED_MARK,)
                    break
        if not item:
            item = DUMMY
        # Write the updated bucket back.
        self.table.write_memory_cell(item_key, current_cell)
        return item

    def ht_extract(self):
        """
        Extracts the original array from the hash table (HT.Extract()) as described in the paper.

        Procedure:
          1. If the hash table is not built, return the original input array X.
          2. Otherwise, perform oblivious bin packing on self.table with a different key_index (3)
             to reverse-route the elements.
          3. Create a new memory array X_prime to store the reconstructed elements.
          4. For each pair of buckets (2i and 2i+1) in the packed table:
             - Read and optionally sort the buckets based on metadata (e.g., the original block index).
             - For each element in the buckets, if it has been marked as accessed (ACCESSED_MARK), treat it as dummy.
             - Otherwise, extract the (k, v) pair.
          5. Write the reconstructed block to X_prime.
          6. Adjust the size of X_prime to match ceil(n/B) and return it.

        Returns:
          RemoteRam: The reconstructed memory array X_prime.
        """
        if not self.is_built:
            return self.X
        if self.C == 1:
            self.table.memory = [[DUMMY if len(x) == 3 and x[2] == ACCESSED_MARK else x for x in self.table.memory[0]]]
            return self.table
        # Reverse the routing of the hash table using bin packing.
        Y_buckets = bin_packing(self.table, self.n, self.B, 3, local=self.local)
        X_prime = RemoteRam(memory_size=self.C // 2, block_capacity=self.B, local=self.local)
        # Process each pair of buckets.
        for i in range(self.C // 2):
            Y_2i = Y_buckets.read_memory_cell(2 * i)
            Y_2i_plus_one = Y_buckets.read_memory_cell(2 * i + 1)
            # Sort the buckets by the extra metadata field if present (assumed to be at index 4).
            Y_2i_plus_one.sort(key=lambda x: (0, x[4]) if len(x) > 4 else (1, 0))
            Y_2i.sort(key=lambda x: (0, x[4]) if len(x) > 4 else (1, 0))
            # Reconstruct the output block by taking at most B/2 real elements from each bucket.
            X_prime_i = [DUMMY if len(x) > 5 and x[5] == ACCESSED_MARK else (x[0], x[1])
                         for x in Y_2i[:self.B // 2]] + \
                        [DUMMY if len(x) > 5 and x[5] == ACCESSED_MARK else (x[0], x[1])
                         for x in Y_2i_plus_one[:self.B // 2]]
            X_prime.write_memory_cell(i, X_prime_i)
        # Adjust the memory size of X_prime to ceil(n/B)
        X_prime.memory = X_prime.memory[:math.ceil(self.n / self.B)]
        X_prime.memory_size = math.ceil(self.n / self.B)
        return X_prime
