import math
import random
import string

from FutORAMa.Counter_ORAM.local_RAM import local_RAM
from RemoteRam.counter_remote_ram import CounterRemoteRam
from RemoteRam.remote_ram import RemoteRam
from config.constants import DUMMY_ADDR


def get_msb_at_index(x, i, bit_length):
    """
    Returns the i-th most significant bit of x (0 or 1), where i=1 corresponds 
    to the leftmost bit. If i is greater than the bit_length, returns 0.

    Parameters:
      x (int): The integer whose bits are examined.
      i (int): The 1-indexed bit position from the left (MSB).
      bit_length (int): The total number of bits to consider.

    Returns:
      int: 0 or 1, the value of the specified bit.
    """
    bit_pos_from_right = bit_length - i  # Compute zero-indexed position from right.
    return (x >> bit_pos_from_right) & 1


def is_dummy(x):
    """
    Determines if an element x is a dummy based on its key.

    Parameters:
      x (tuple): An element (typically a (key, value) pair or similar).

    Returns:
      bool: True if the first component equals DUMMY_ADDR, False otherwise.
    """
    return x[0] == DUMMY_ADDR


def closest_even_number(number):
    """
    Returns the smallest even number that is greater than or equal to the input.

    Parameters:
      number (int): The input number.

    Returns:
      int: The closest even number.
    """
    return math.ceil(number / 2) * 2


def next_power_of_two_greater_or_equal(x: int) -> int:
    """
    Returns the smallest power of 2 that is greater than or equal to x.

    Parameters:
      x (int): The input number.

    Returns:
      int: The next power of 2 >= x.
    """
    p = 1
    while p < x:
        p <<= 1  # Multiply by 2.
    return p


def choose_C(n, B):
    """
    Chooses the parameter C for bin packing in the MegaBlocks ORAM project.

    C is determined as the next power of two greater than or equal to max(ceil(2n/B), 2).

    Parameters:
      n (int): Total number of logical elements.
      B (int): Block capacity (number of elements per block).

    Returns:
      int: The chosen C value.
    """
    val = math.ceil((2 * n) / B)
    return next_power_of_two_greater_or_equal(val)


def generate_random_string(k):
    """
    Generates a random alphanumeric string of length k.

    Parameters:
      k (int): The length of the random string.

    Returns:
      str: A random string consisting of letters and digits.
    """
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=k))


def count_reals(mem1):
    """
    Counts the number of non-dummy elements in a memory array.

    Parameters:
      mem1 (iterable): A memory array (list of blocks), where each block is a list of elements.

    Returns:
      int: The total count of real (non-dummy) elements.
    """
    counter = 0
    for block in mem1:
        for item in block:
            if item[0] != DUMMY_ADDR:
                counter += 1
    return counter

def reset_memory_counters():
    CounterRemoteRam.read_operations = 0
    CounterRemoteRam.write_operations = 0
    RemoteRam.read_operations = 0
    RemoteRam.write_operations = 0
    local_RAM.BALL_READ = 0
    local_RAM.BALL_WRITE = 0
    local_RAM.RT_WRITE = 0
    local_RAM.RT_READ = 0