import math
from config.constants import SIMULATION_MEGA_BLOCKS_ORAM, COUNTER_MEGA_BLOCKS_ORAM, \
    COUNTER_PATH_ORAM, MEGA_BLOCKS_ORAM, COUNTER_FUTORAMA
from config.utils import reset_memory_counters
from oram_runner import get_oram_instance, run_experiment

def run_table_1():
    """
    Table 1 Experiment – Large-Scale Comparison: MegaBlocksORAM vs. Path ORAM (Block Size Range).

    In this experiment (with 64-bit client words and 1 TB of logical memory),
    we compare our construction (simulated via CounterMegaBlocksORAM, choice '5') against Path ORAM (simulated via
    CounterPathORAM, choice '4') over a narrower range of physical block sizes (from 4 KB to 64 KB).
    This setup focuses on the detailed performance (I/O cost, bandwidth overhead, and local memory usage)
    of our scheme versus Path ORAM in a regime that is typical for modern storage devices.
    """
    w = 64
    TB = 2 ** 43
    N = TB // w
    KB = 2 ** 13
    b_sizes = [4 * KB, 8 * KB, 16 * KB, 32 * KB, 64 * KB]
    for b in b_sizes:
        B = b // w
        q = math.ceil(math.sqrt(B))
        print("Mega Blocks ORAM\n")
        local_memory = 400
        T = 2 * N
        choice = COUNTER_MEGA_BLOCKS_ORAM
        oram = get_oram_instance(choice, N, B, q, T, local_memory=local_memory - 4)
        run_experiment(oram, choice, N, B, w // 8, T, w, q, b)
        print("Path ORAM\n")
        choice = COUNTER_PATH_ORAM
        path_oram = get_oram_instance(choice, N, B, q, T, local_memory=local_memory - math.log(N, 2), b=b, w=w)
        run_experiment(path_oram, choice, N, B, w // 8, T, w, q, b)
        print("b size: " + str(b // KB) + " KB")
        print("Local memory in server blocks: " + str(local_memory))
        print("Local memory in MB: " + str(local_memory * b / (2 ** 23)))
        print("Local memory in GB: " + str(local_memory * b / (2 ** 33)))


def run_table_2():
    """
    Table 2 Experiment – Large-Scale Comparison: MegaBlocksORAM vs. Path ORAM vs. FutORAMa with Large Local Memory.

    In this experiment (with 64-bit client words and 1 TB of logical memory),
    we compare our construction (simulated via FormulaORAM, choice '5') against Path ORAM (simulated via
    CounterPathORAM, choice '4') in a high–resource setting with large local memory (131,220 server blocks).
    Physical block sizes are varied over a wide range to assess the I/O overhead
    and bandwidth impact. We used the simulation mode of FutORAMa (See the code of FutORAMa for more details).
    """
    w = 64
    TB = 2 ** 43
    N = TB // w
    KB = 2 ** 13
    Byte = 2 ** 3
    b_sizes = [32 * Byte, 256 * Byte, 512 * Byte, 1 * KB, 4 * KB, 8 * KB, 16 * KB, 32 * KB, 64 * KB, 128 * KB]
    for b in b_sizes:
        B = b // w
        q = math.ceil(math.sqrt(B))
        print("Mega Blocks ORAM\n")
        local_memory = 131_220
        T = 2 * N
        if b >= KB:
            choice = COUNTER_MEGA_BLOCKS_ORAM
            oram = get_oram_instance(choice, N, B, q, T, local_memory=local_memory - 4)
            run_experiment(oram, choice, N, B, w // 8, T, w, q, b)
        print("Path ORAM\n")
        choice = COUNTER_PATH_ORAM
        path_oram = get_oram_instance(choice, N, B, q, T, local_memory=local_memory - math.log(N, 2), b=b, w=w)
        run_experiment(path_oram, choice, N, B, w // 8, T, w, q, b)
        print("FutORAMa\n")
        choice = COUNTER_FUTORAMA
        futorama = get_oram_instance(choice, TB, B, q, T, local_memory=local_memory - math.log(N, 2), w=1, b=b)
        reset_memory_counters()
        run_experiment(futorama, choice, N, B, w // 8, T, w, q, b)
        print("b size in B: " + str(b // Byte) + " B")
        print("b size in KB: " + str(b // KB) + " KB")
        print("Local memory in server blocks: " + str(local_memory))
        print("Local memory in MB: " + str(local_memory * b / (2 ** 23)))
        print("Local memory in GB: " + str(local_memory * b / (2 ** 33)))


def run_table_3():
    """
    Table 3 Experiment – Comparison of the Three Models of Our ORAM.

    In this experiment (with N = 2^16, 32‐bit client words, and local memory = 4),
    we compare all three models of our ORAM implementation by varying the physical block
    size (b) over a range [w^3, 2·w^3, 4·w^3, 8·w^3, 16·w^3, 32·w^3]. The three models,
    corresponding to choices '1', '2', and '5', are evaluated under identical conditions,
    allowing a direct comparison of their I/O overhead and bandwidth performance.
    """
    N = int(math.pow(2, 16))
    w = 32
    local_memory = 4
    choices = [SIMULATION_MEGA_BLOCKS_ORAM, MEGA_BLOCKS_ORAM, COUNTER_MEGA_BLOCKS_ORAM]
    poss_b = [w ** 3, 2 * w ** 3, 4 * w ** 3, 8 * w ** 3, 16 * w ** 3, 32 * w ** 3]
    for pos in poss_b:
        for choice in choices:
            print("Mode " + choice)
            B = pos // w
            q = math.ceil(math.sqrt(B))
            T = 2 * N
            oram = get_oram_instance(choice, N, B, q, T, local_memory)
            run_experiment(oram, choice, N, B, w // 8, T, w, q, pos)
        print("#####################################\n\n\n\n\n")


def run_table_4():
    """
    Table 4 Experiment – Effect of Varying Local Memory on Performance.

    This experiment evaluates our construction (FormulaORAM, choice '5') in a larger-scale
    setting (N = 2^30, 32‐bit client words) while varying the available local memory.
    Local memory is varied over a range (2^1, 2^2, …), and experiments are stopped once
    the local memory exceeds 2048 KB. The experiment quantifies the impact of local memory
    size on the overall I/O cost and bandwidth, helping to identify favorable resource trade-offs.
    """
    N = int(math.pow(2, 30))
    w = 32
    b = w ** 3
    B = b // w
    q = math.ceil(math.sqrt(B))
    T = 2 * N
    choice = COUNTER_MEGA_BLOCKS_ORAM
    local_memories = [2 ** i for i in range(1, 30)]
    for local_memory in local_memories:
        if ((local_memory * b) / ((2 ** 20) * 8)) > 2048:
            break
        oram = get_oram_instance(choice, N, B, q, T, local_memory=local_memory)
        run_experiment(oram, choice, N, B, w // 8, T, w, q, b)
        print("Local Memory: " + str(local_memory))
        print("Local memory in KB: " + str(local_memory * b / (1024 * 8)))
        print("Local memory in MB: " + str(local_memory * b / ((2 ** 20) * 8)))


def run_table_5():
    """
    Table 5 Experiment – Scalability Evaluation of Our Construction.

    This experiment tests the scalability of our construction (FormulaORAM, choice '5')
    by varying the logical memory size N (from 2^16 up to 2^32) while keeping the client word
    size fixed at 32 bits and local memory at 0. The performance (I/O overhead and bandwidth)
    is measured for each value of N, providing insight into how our construction scales with
    increasing memory size.
    """
    poss_power_N = [16, 20, 24, 28, 32]
    w = 32
    b = w ** 3
    w_in_bytes = math.ceil(w / 8)
    local_memory = 1
    for p in poss_power_N:
        N = int(math.pow(2, p))
        B = b // w
        q = math.ceil(math.sqrt(B))
        T = 2 * N
        choice = COUNTER_MEGA_BLOCKS_ORAM
        oram = get_oram_instance(choice, N, B, q, T, local_memory=local_memory)
        run_experiment(oram, choice, N, B, w_in_bytes, T, w, q, b)


def run_table_6():
    """
    Table 6 Experiment – Impact of the Expansion Parameter q on Performance.

    In this experiment (with N = 2^16, 32‐bit client words, and local memory = 6),
    we vary the expansion factor q (from ⌊√B⌋ to ⌊B/log₂N⌋) for our ORAM model using
    choice '1' (CounterMegaBlocksORAM). This study investigates how the theoretical and
    experimental I/O overhead changes with q, thereby illustrating the sensitivity of
    performance to the expansion parameter.
    """
    N = int(math.pow(2, 16))
    w = 32
    b = w ** 3
    B = b // w
    w_in_bytes = math.ceil(w / 8)
    local_memory = 6
    possible_q = [i for i in range(math.floor(math.sqrt(B)), math.floor(B / math.log(N, 2)) + 1)]
    for q in possible_q:
        T = 2 * N
        choice = SIMULATION_MEGA_BLOCKS_ORAM
        oram = get_oram_instance(choice, N, B, q, T, local_memory=local_memory)
        run_experiment(oram, choice, N, B, w_in_bytes, T, w, q, b)
