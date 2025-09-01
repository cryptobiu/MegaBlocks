"""
Interactive entry point for running ORAM experiments.

This module prompts the user to input experiment parameters,
selects an ORAM implementation, and then runs a complete experiment
using the helper functions defined in oram_runner.py.
"""

import math
from oram_runner import get_oram_instance, run_experiment


def main():
    """
    Main interactive function that prompts for experiment parameters,
    creates an ORAM instance based on the user’s selection, and runs the experiment.
    """
    # Prompt the user for the power-of-2 which determines N.
    power = int(input("Choose power of 2 for N (N is the number of memory blocks used by the client program): "))
    N = int(math.pow(2, power))

    w = 32  # Logical word size in bits
    w_in_bytes = math.ceil(w / 8)

    b = 65536  # Physical block size in bits
    B = b // w  # Number of client words per physical block

    q = math.ceil(math.sqrt(B))  # Expansion factor.
    T = 2 * N  # Total number of ORAM accesses

    # Display ORAM implementation options.
    print("Choose the ORAM implementation:")
    print("1) Simulation of MegaBlocksORAM (Without real memory allocation)")
    print("2) Real execution of MegaBlocksORAM")
    print("3) Real execution of PathORAM")
    print("4) Counter mode of PathORAM")
    print("5) Counter mode of MegaBlocksORAM")
    print("6) Counter mode of FutORAMa")
    choice = input("Enter your choice: ")

    try:
        oram = get_oram_instance(choice=choice, N=N, B=B, q=q, T=T, b=b, w=w)
    except ValueError as e:
        print(e)
        exit(1)

    run_experiment(oram=oram, choice=choice, N=N, B=B, w_in_bytes=w_in_bytes, T=T, w=w, q=q, b=b)


if __name__ == '__main__':
    main()
