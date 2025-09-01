"""
Helper functions to set up and run ORAM experiments.

This module provides utility functions for progress display,
ORAM instance creation, performing ORAM accesses, operation statistics
computation, and running a complete experiment.
"""

import sys
import math
import random

from FutORAMa.Counter_ORAM.futorama import CounterFutORAMa
from config.constants import SIMULATION_MEGA_BLOCKS_ORAM, MEGA_BLOCKS_ORAM, PATH_ORAM, \
    COUNTER_PATH_ORAM, COUNTER_MEGA_BLOCKS_ORAM, COUNTER_FUTORAMA
from config.constants import WRITE_OPERATION, READ_OPERATION
from config.utils import generate_random_string

# Import ORAM implementations.
from MegaBlocksORAM.Counter_ORAM.counter_oram import CounterMegaBlocksORAM
from MegaBlocksORAM.Simulation_ORAM.simulation_oram import SimulationMegaBlocksORAM
from MegaBlocksORAM.Real_ORAM.oram import MegaBlocksORAM
from PathORAM.Counter_ORAM.counter_path_oram import CounterPathORAM
from PathORAM.Real_ORAM.path_oram import PathORAM

# For computing total operations in the experiments.
from RemoteRam.counter_remote_ram import CounterRemoteRam
from RemoteRam.remote_ram import RemoteRam


def print_progress_bar(current_index, total_count, label):
    """
    Displays a progress bar in the terminal.

    Parameters:
      current_index (int): The current progress index.
      total_count (int): The total number of steps.
      label (str): Additional label to display at the end of the bar.
    """
    n_bar = 50  # Progress bar width in characters.
    progress_fraction = current_index / total_count
    sys.stdout.write('\r')
    sys.stdout.write(
        f"[{'=' * int(n_bar * progress_fraction):{n_bar}s}] {int(100 * progress_fraction)}%  {label}"
    )
    sys.stdout.flush()


def get_oram_instance(choice, N, B, q, T, local_memory=2, b=None, w=None):
    """
    Returns an instance of the ORAM implementation based on the provided choice.

    Parameters:
      choice (str): Option chosen by the user. Options are:
                    SIMULATION_MEGA_BLOCKS_ORAM, MEGABLOCKS_ORAM, PATH_ORAM,
                    COUNTER_PATH_ORAM, or COUNTER_MEGA_BLOCKS_ORAM.
      N (int): Total number of logical memory blocks.
      B (int): Block size in elements.
      q (int): Parameter computed from B (typically an expansion factor).
      T (int): Total number of ORAM accesses (simulation rounds).
      local_memory (int, optional): Amount of local memory (in server blocks). Defaults to 2.
      b (int, optional): Physical block size (required for some ORAM implementations).
      w (int, optional): Client word size (in bits), required for some ORAM implementations.

    Returns:
      An instance of the selected ORAM algorithm.

    Raises:
      ValueError: If the provided choice does not match any known ORAM implementation.
    """
    if choice == SIMULATION_MEGA_BLOCKS_ORAM:
        return SimulationMegaBlocksORAM(N, B, q, local_memory_in_server_blocks=local_memory)
    elif choice == MEGA_BLOCKS_ORAM:
        return MegaBlocksORAM(N, B, q, local_memory_in_server_blocks=local_memory)
    elif choice == PATH_ORAM:
        return PathORAM(math.ceil(N / B), b, Z=4, element_size=w, local_memory_capacity=local_memory)
    elif choice == COUNTER_PATH_ORAM:
        return CounterPathORAM(math.ceil(N / B), b, Z=4, element_size=w, local_memory_capacity=local_memory)
    elif choice == COUNTER_MEGA_BLOCKS_ORAM:
        return CounterMegaBlocksORAM(N, B, q, T, local_memory_in_server_blocks=local_memory)
    elif choice == COUNTER_FUTORAMA:
        return CounterFutORAMa(N ,w, b)

    else:
        raise ValueError("Not valid input")


def perform_oram_accesses(oram, N, w_in_bytes, T, addr_range):
    """
    Performs T random ORAM accesses using the provided ORAM instance.
    For each access, a random memory address is chosen and the operation
    (read or write) is selected randomly. For write operations, random data
    is generated to match the client word size.

    Parameters:
      oram: The ORAM instance to be accessed.
      N (int): Total number of memory blocks.
      w_in_bytes (int): Client word size in bytes.
      T (int): Total number of accesses to perform.
      addr_range (int): Range for randomly generating addresses.
    """
    progress_interval = T // 100 if T >= 100 else 1
    for i in range(T):
        if i % progress_interval == 0:
            print_progress_bar(i // progress_interval, 100, "progress")
        data = "d" + str(i)
        addr = random.randint(0, addr_range - 1)
        op = random.choice([READ_OPERATION, WRITE_OPERATION])
        data += generate_random_string(w_in_bytes - len(data))
        oram.access(op, addr, data)


def print_operation_stats(total_ops, N, B, T, w, q, b, choice):
    """
    Computes derived statistics from the ORAM simulation and prints them.
    These statistics include I/O cost, bandwidth overhead, and several theoretical ratios.

    Parameters:
      total_ops (int): Total number of memory operations (I/O cost).
      N (int): Total number of logical memory blocks.
      B (int): Number of client elements per block.
      T (int): Total number of ORAM accesses.
      w (int): Client word size in bits.
      q (int): Expansion factor or similar algorithm-specific parameter.
      b (int): Physical block size.
      choice (str): The ORAM mode used.
    """
    print("\n")
    print("N =", N)
    print("B =", B)
    print("w =", w)
    print("q =", q)
    print("b =", b)
    print("b in KB =", b / (1024 * 8))

    log_n_loglog_n = math.log(N) / math.log(math.log(N))
    log_q_n = math.log(N, q)
    amortized_theory = 4 * log_q_n + 2 + 2 / q + 20 / (q - 1) + 16 / B
    log_noB_logB = math.log(N) / math.log(B)
    total_accesses_log_q_n = T * log_q_n
    total_accesses_log_n_loglog_n = T * log_n_loglog_n
    total_accesses_theory = T * amortized_theory
    total_accesses_log_n_log_B = total_ops / (log_noB_logB * T)
    io_overhead = total_ops / T
    bandwidth_overhead = (b * io_overhead) / 2 ** 13

    print("Total read and write operations:", total_ops)
    print("Bandwidth Overhead in KB: {} KB".format(bandwidth_overhead))
    print("Bandwidth Overhead in MB: {} MB".format(bandwidth_overhead / 1024))
    print("I/O overhead per access:", io_overhead)
    if choice in [MEGA_BLOCKS_ORAM, SIMULATION_MEGA_BLOCKS_ORAM, COUNTER_MEGA_BLOCKS_ORAM]:
        print("I/O Overhead Theoretical Amortized Cost (4L + 2 + o(1)) =", amortized_theory)
        print("T * Theoretical Amortized Cost =", T * amortized_theory)
        print("Ratio: Total ops / (T * Theoretical Amortized Cost) =", total_ops / total_accesses_theory)
        print("Ratio: Total ops / (T * log_q(N)) =", total_ops / total_accesses_log_q_n)
        print("Ratio: Total ops / (T * log(N)/loglog(N)) =", total_ops / total_accesses_log_n_loglog_n)
        print("Ratio: Total ops / (T * log(N)/log(B)) =", total_accesses_log_n_log_B)
        error_prob = T * log_n_loglog_n * math.exp(-(B / 6))
        print("Error probability:", error_prob)
        if error_prob > 0:
            print("Log2(Error probability):", math.log(error_prob, 2))
        else:
            print("Log2(Error probability) > 1000")


def run_experiment(oram, choice, N, B, w_in_bytes, T, w, q, b):
    """
    Runs a full ORAM experiment using the provided ORAM instance. The experiment
    performs T random accesses, calculates the overall I/O cost, and then prints detailed
    performance statistics.

    Parameters:
      oram: The ORAM instance used for the experiment.
      choice (str): The ORAM implementation chosen (one of the defined constants).
      N (int): Total number of logical memory blocks.
      B (int): Block size in terms of client elements.
      w_in_bytes (int): Client word size in bytes.
      T (int): Total number of ORAM accesses to simulate.
      w (int): Client word size in bits.
      q (int): Expansion factor or related parameter.
      b (int): Physical block size.
    """
    total_ops = 0
    address_range = N
    # In Path ORAM, we reduce the address space to N/B.
    if choice == PATH_ORAM:
        address_range = math.ceil(N / B)

    if choice in [SIMULATION_MEGA_BLOCKS_ORAM, MEGA_BLOCKS_ORAM, PATH_ORAM]:
        perform_oram_accesses(oram=oram, N=N, w_in_bytes=w_in_bytes, T=T, addr_range=address_range)

    if choice == SIMULATION_MEGA_BLOCKS_ORAM:
        total_ops = CounterRemoteRam.write_operations + CounterRemoteRam.read_operations
    elif choice in [MEGA_BLOCKS_ORAM, PATH_ORAM]:
        total_ops = RemoteRam.write_operations + RemoteRam.read_operations
    elif choice == COUNTER_PATH_ORAM:
        total_ops = oram.count_accesses() * T
    elif choice == COUNTER_MEGA_BLOCKS_ORAM:
        total_ops = oram.calc_total_cost()
    elif choice == COUNTER_FUTORAMA:
        total_ops = oram.counter_only_test() * T

    print_operation_stats(total_ops, N, B, T, w, q, b, choice)

    if choice in [MEGA_BLOCKS_ORAM, SIMULATION_MEGA_BLOCKS_ORAM]:
        print("Load factors:", oram.load_factors)
    if choice in [MEGA_BLOCKS_ORAM, SIMULATION_MEGA_BLOCKS_ORAM, COUNTER_MEGA_BLOCKS_ORAM]:
        print("Local levels:", oram.inner_tables)
