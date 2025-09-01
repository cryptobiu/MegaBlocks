import math
from MegaBlocksORAM.Simulation_ORAM.counter_hash_table import HashTable
from RemoteRam.counter_remote_ram import CounterRemoteRam
from config.utils import choose_C


class CounterMegaBlocksORAM:
    def __init__(self, N, B, q, T, local_memory_in_server_blocks=2):
        """
        Initializes the FormulaORAM cost model.

        Parameters:
          N: Upper bound on the number of real elements.
          B: Block capacity (number of elements per block).
          q: Expansion factor.
          T: Total number of accesses.
          local_memory_in_server_blocks: Available local memory (in server blocks).
        """
        self.N = N
        self.B = B
        self.q = q
        self.T = T
        self.number_of_levels = math.floor(math.log(self.N, q)) + 1
        self.rebuild_costs = [0 for _ in range(self.number_of_levels)]
        # Create a 2D list to store build/extract costs for each level (dimensions: number_of_levels x (q-1)).
        self.table_build_extract_costs = [[(0, 0)] * (q - 1) for _ in range(self.number_of_levels)]
        self.build_total_costs = [(0, 0)] * self.number_of_levels
        self.local_memory_in_server_blocks = local_memory_in_server_blocks
        self.inner_tables = []
        # Determine which levels use local memory.
        for i in range(self.number_of_levels):
            if math.ceil((q ** i) * (q - 1) / B) < self.local_memory_in_server_blocks:
                self.local_memory_in_server_blocks -= math.ceil((q ** i) * (q - 1) / B)
                self.inner_tables.append(i)

    def calc_build_extract_costs(self):
        """
        Calculates and stores the per-level cost of table building and extraction.

        For each level (except those in inner_tables), iterates through load factors 1 to q-1.
        The cost is computed as: 2 * C * log₂(C) + C + (C // 2), where C = choose_C(calc_ht_size(i, load_factor), B).
        The total cost for each level is stored in build_total_costs.
        """
        for i in range(self.number_of_levels):
            if i in self.inner_tables:
                continue
            for j in range(self.q - 1):
                n = self.calc_ht_size(i, j + 1)
                self.table_build_extract_costs[i][j] = self.calc_build_extract_with_ht(n)

    def calc_ht_size(self, level_index, load_factor):
        """
        Calculates the effective size (number of elements) for a given level.

        For level 0, the size equals the load factor.
        For the highest level, the size is N.
        Otherwise, the size is determined by q^(level_index) * load_factor.

        Parameters:
          level_index (int): The level index.
          load_factor (int): The load factor at that level.

        Returns:
          int: The effective size for the level.
        """
        if level_index == 0:
            return load_factor
        elif level_index == self.number_of_levels - 1:
            return self.N
        else:
            return math.ceil(int(math.pow(self.q, level_index) * load_factor))

    def total_lookup_cost(self, T, q):
        """
        Computes the total I/O cost for lookups over T accesses across all levels.

        For each level, a full cycle is of q^(level)*(q - 1) + 1, where the first q^(level)
        accesses are inactive and the next are active. Each active
        lookup is counted as 2 operations.

        Parameters:
          T (int): Total number of memory accesses.
          q (int): Expansion factor.

        Returns:
          int: The total I/O cost for lookups.
        """
        total_cost = 0
        for level in range(self.number_of_levels):
            if level in self.inner_tables:
                continue
            if level == self.number_of_levels - 1:
                total_cost += 2 * T
                continue
            cycle_length = (q ** (level + 1))
            inactive = q ** level
            active = cycle_length - inactive
            full_cycles = T // cycle_length
            remainder = T % cycle_length

            if remainder <= inactive:
                extra = 0
            else:
                extra = min(remainder - inactive, active)
            total_cost += 2 * (full_cycles * active + extra)
        return total_cost

    def total_compaction_cost(self, T):
        """
        Estimates the total compaction cost over T accesses.

        The method computes:
          - tables_capacity_sum: Sum of effective sizes at each level (using max load factor = q-1).
          - compaction_input_size: Total input size for compaction (in terms of elements).
          - compaction_output_size: Number of blocks in the output after compaction.
          - C: Parameter computed via choose_C based on compaction_input_size.

        Returns:
          float: The estimated total compaction cost.
        """
        tables_capacity_sum = self.q ** (self.number_of_levels - 1)
        compaction_times = T // tables_capacity_sum
        # rest of compactions
        compaction_input_size = 0
        for i in range(self.number_of_levels):
            compaction_input_size += self.calc_ht_size(i, self.q - 1)
        compaction_input_size = math.ceil(compaction_input_size / self.B)
        C = choose_C(compaction_input_size * self.B, self.B)
        compaction_output_size = math.ceil(self.N / self.B)

        return compaction_times * (compaction_output_size + 2 * C * math.log(C, 2) + C + 3 * compaction_input_size + C - 2 * compaction_input_size)

    def total_rebuild_cost(self, T, q):
        """
        Computes the total rebuild cost over T accesses across all levels.

        For each level i, the rebuild cost is simulated as follows:
          - Every rebuild costs load_factor * q^(i-1), where load_factor cycles as 1,2,...,q-1.
          - The number of rebuilds R at level i is T // q^i.
          - The cost is the sum of full cycles (each of q-1 rebuilds) plus any remaining rebuilds,
            plus an extraction cost from lower levels.

        Parameters:
          T (int): Total number of accesses.
          q (int): Expansion factor.

        Returns:
          float: The total rebuild cost.
        """
        total_cost = 0
        for i in range(self.number_of_levels):
            if i in self.inner_tables:
                continue
            if i == self.number_of_levels - 1:
                counter = T // (q ** (self.number_of_levels - 1))
                extract_cost_lower_levels = 0
                # Extraction cost of lower levels.
                for j in range(i):
                    extract_cost_lower_levels += self.table_build_extract_costs[j][q - 2][1]
                build_extract_current_level = self.table_build_extract_costs[i][q - 2][0] + \
                                              self.table_build_extract_costs[i][q - 2][1]
                cost = counter * (build_extract_current_level + extract_cost_lower_levels)
                self.rebuild_costs[i] = cost
                total_cost += cost
            else:
                Q = T // (q ** (i + 1))  # full cycle.
                r = (T % (q ** (i + 1))) // q ** i  # the reminder of cycles.
                full_cycle_cost = 0
                remainder_cost = 0
                extract_cost_current_level = 0
                extract_cost_lower_levels = 0
                build_current_level = 0

                # Extraction cost of lower levels.
                for j in range(i):
                    extract_cost_lower_levels += self.table_build_extract_costs[j][q - 2][1]

                if Q > 0:
                    # Building cost of current level after extraction.
                    for j in range(self.q - 1):
                        build_current_level += self.table_build_extract_costs[i][j][0]

                    # Extraction cost of the current level.
                    for j in range(self.q - 2):
                        extract_cost_current_level += self.table_build_extract_costs[i][j][1]

                    full_cycle_cost = Q * (extract_cost_current_level + (
                            self.q - 1) * extract_cost_lower_levels + build_current_level)
                if r > 0:
                    remainder_cost = r * extract_cost_lower_levels

                    # The cost of the extraction
                    for j in range(r - 1):
                        remainder_cost += self.table_build_extract_costs[i][j][1]

                    # The cost of build
                    for j in range(r):
                        remainder_cost += self.table_build_extract_costs[i][j][0]
                cost = full_cycle_cost + remainder_cost
                self.rebuild_costs[i] = cost
                total_cost += cost
        return total_cost

    def calc_build_extract_with_ht(self, n):
        CounterRemoteRam.write_operations = 0
        CounterRemoteRam.read_operations = 0
        ht = HashTable(CounterRemoteRam(block_capacity=self.B, memory_size=math.ceil(n / self.B), local=False),
                       self.B, n, False)
        ht.ht_build()
        build_cost = CounterRemoteRam.read_operations + CounterRemoteRam.write_operations
        CounterRemoteRam.write_operations = 0
        CounterRemoteRam.read_operations = 0
        ht.ht_extract()
        extract_cost = CounterRemoteRam.read_operations + CounterRemoteRam.write_operations
        return build_cost, extract_cost

    def calc_total_cost(self):
        """
        Calculates the total cost of the ORAM operations by summing:
          - Build/Extract cost,
          - Lookup cost,
          - Rebuild cost.

        Returns:
          float: The total cost.
        """
        self.calc_build_extract_costs()
        total_cost = self.total_compaction_cost(self.T)
        total_cost += self.total_lookup_cost(self.T, self.q)
        total_cost += self.total_rebuild_cost(self.T, self.q)
        return int(total_cost)
