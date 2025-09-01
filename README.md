# MegaBlocks ORAM Implementation Overview

This project implements a MegaBlocks‐style ORAM system based on the paper: 
> "MegaBlocks: Breaking the Logarithmic I/O Overhead Barrier for Oblivious RAM"

## Implementation Variants

The implementation supports several variants of MegaBlocks ORAM, including:

- **Real Mode** – Uses actual memory allocation with real elements.
- **Simulation Mode** – Executes a full run of the algorithm without allocating memory.
- **Counter Mode** – Reports estimated I/O overhead based on a formula computed from the ORAM access sequence.

In addition, a reference implementation of Path ORAM is provided (in both real and counter modes) along with a counter mode for FutORAMa (adapted from the FutORAMa source code with cosmetic changes).

## Execution Options

When running the program, you will be prompted to choose one of the following ORAM modes:

1. Simulation of MegaBlocksORAM
2. Real Execution of MegaBlocksORAM
3. Real Execution of Path ORAM
4. Counter Mode of Path ORAM
5. Counter Mode of MegaBlocksORAM
6. Counter Mode of FutORAMa

Each mode sets up an experiment with T = 2N random accesses and reports performance metrics such as I/O overhead and bandwidth.

## Project Structure

### main.py
The interactive entry point. It prompts for key parameters (e.g., a power-of‑2 for N) and uses calculated values (with w set to log₂(N) and b set to w³) to create and run an ORAM experiment based on your selection.

### oram_runner.py
Contains utility functions for:
- Creating ORAM instances
- Running random accesses
- Displaying a progress bar
- Computing performance statistics

### paper_tables.py
Provides functions (e.g., run_table_1, run_table_2, etc.) that reproduce the experimental tables presented in the paper.

**Note**: To run a paper table experiment, edit main.py to call the desired function.

### Other Directories:
The remaining directories (e.g., config/, MegaBlocksORAM/, PathORAM/, RemoteRam/) contain the implementations, configuration files, and supporting utilities.

## How to Run

1. **Set Your Working Directory**:
   Make sure your working directory is set to the project's root folder (e.g., a folder named MegaBlocksCode/MegaBlocks).
   In your IDE, mark this folder as the Sources Root so that all package imports are resolved correctly.

2. **Install Dependencies**:
   Install the required packages by running:
   ```
   pip install -r requirements.txt
   ```

3. **Execute the Main Script**:
   Run the interactive script by executing:
   ```
   python main.py
   ```
   Follow the on-screen prompts to specify the power-of-2 for N and select the desired ORAM mode.

4. **Run Paper Table Experiments (Optional)**:
   To reproduce the experiments from the paper, open paper_tables.py and modify main.py to call the desired function (e.g., run_table_1(), run_table_2(), etc.).

## Requirements

Python 3.11 is required.

## Additional Information

For further details on the implementation, refer to the inline code documentation within the source files.


## Acknowledgments

The implementation of MegaBlocks in this repository is based on the paper **"MegaBlocks: Breaking the Logarithmic I/O-Overhead Barrier for Oblivious RAM"** by Gilad Asharov, Eliran Eiluz, Ilan Komargodski, and Wei-Kai Lin.


## License

This project is licensed under the MIT License.

Copyright (c) 2025 Eliran Eiluz

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.