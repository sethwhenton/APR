"""
Phase 4: The Genetic Loop (evolution.py)

Generic Automated Program Repair using Genetic Programming.

Usage:
    python evolution.py benchmark1
    python evolution.py benchmark2
    python evolution.py benchmarks/benchmark3
    
The tool will look for:
    - benchmarks/<name>/patient.py  (the buggy program)
    - benchmarks/<name>/tests.json  (test cases)
    
Outputs:
    - benchmarks/<name>/repaired_solution.py  (if fix found)
    - benchmarks/<name>/report_summary.txt    (summary report)
"""

import os
import sys
import argparse
import random
import shutil
from datetime import datetime

# Import our modules
from mutation import load_program, save_program_to_string, apply_random_mutation
from test_harness import TestHarness


# === CONFIGURATION ===
POPULATION_SIZE = 40
NUM_GENERATIONS = 50
SURVIVOR_RATIO = 0.5  # Keep top 50%
TEMP_DIR = "temp_variants"


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Automated Program Repair using Genetic Programming",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python evolution.py benchmark1
    python evolution.py benchmark2 --generations 100
    python evolution.py benchmarks/benchmark3 --population 60
        """
    )
    
    parser.add_argument(
        "benchmark",
        help="Name of the benchmark (e.g., 'benchmark1' or 'benchmarks/benchmark1')"
    )
    
    parser.add_argument(
        "--generations", "-g",
        type=int,
        default=NUM_GENERATIONS,
        help=f"Number of generations to run (default: {NUM_GENERATIONS})"
    )
    
    parser.add_argument(
        "--population", "-p",
        type=int,
        default=POPULATION_SIZE,
        help=f"Population size (default: {POPULATION_SIZE})"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser.parse_args()


def resolve_benchmark_path(benchmark_arg):
    """
    Resolve the benchmark directory path from the argument.
    
    Accepts:
        - "benchmark1" -> "benchmarks/benchmark1"
        - "benchmarks/benchmark1" -> "benchmarks/benchmark1"
        - Full path -> as-is
    """
    # If it's already a path with benchmarks/
    if os.path.isdir(benchmark_arg):
        return benchmark_arg
        
    # Try prefixing with benchmarks/
    prefixed = os.path.join("benchmarks", benchmark_arg)
    if os.path.isdir(prefixed):
        return prefixed
        
    # Not found
    raise FileNotFoundError(
        f"Benchmark not found: '{benchmark_arg}'\n"
        f"Tried: '{benchmark_arg}' and '{prefixed}'\n"
        f"Available benchmarks: {list_available_benchmarks()}"
    )


def list_available_benchmarks():
    """List all available benchmark directories."""
    benchmarks_dir = "benchmarks"
    if not os.path.isdir(benchmarks_dir):
        return []
    return [d for d in os.listdir(benchmarks_dir) 
            if os.path.isdir(os.path.join(benchmarks_dir, d))]


def setup_temp_directory():
    """Creates the temporary directory for variant files."""
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    os.makedirs(TEMP_DIR)


def cleanup_temp_directory():
    """Removes the temporary directory and all its contents."""
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)


def get_temp_filepath(index):
    """Returns a UNIQUE temporary file path for a given variant index."""
    return os.path.join(TEMP_DIR, f"variant_{index}.py")


def save_variant_to_file(lines, filepath):
    """Saves a code variant (list of lines) to a file."""
    code_str = save_program_to_string(lines)
    with open(filepath, 'w') as f:
        f.write(code_str)


def find_changed_lines(original_lines, repaired_lines):
    """
    Compares original and repaired code to find what changed.
    
    Returns:
        list of tuples: [(line_number, original_code, repaired_code), ...]
    """
    changes = []
    
    # Compare line by line
    max_lines = max(len(original_lines), len(repaired_lines))
    
    for i in range(max_lines):
        if i >= len(original_lines):
            # New line added
            changes.append((i + 1, "<no line>", repaired_lines[i].strip()))
        elif i >= len(repaired_lines):
            # Line removed
            changes.append((i + 1, original_lines[i].strip(), "<deleted>"))
        elif original_lines[i] != repaired_lines[i]:
            # Line modified
            changes.append((i + 1, original_lines[i].strip(), repaired_lines[i].strip()))
    
    return changes


def write_summary_report(
    benchmark_dir,
    benchmark_name,
    function_name,
    success,
    generations_run,
    final_generation,
    max_fitness,
    achieved_fitness,
    original_lines,
    repaired_lines,
    weighted_lines
):
    """
    Writes a comprehensive summary report to the benchmark directory.
    
    This report fulfills the 'Project Report' requirement by documenting:
    - Test results and success/failure status
    - Which lines were changed
    - The genetic algorithm parameters used
    """
    report_path = os.path.join(benchmark_dir, "report_summary.txt")
    
    with open(report_path, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write("         AUTOMATED PROGRAM REPAIR - SUMMARY REPORT\n")
        f.write("=" * 70 + "\n\n")
        
        # Basic Info
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Benchmark: {benchmark_name}\n")
        f.write(f"Function Tested: {function_name}()\n\n")
        
        # Result
        f.write("-" * 70 + "\n")
        f.write("RESULT\n")
        f.write("-" * 70 + "\n")
        if success:
            f.write("Status: SUCCESS - Perfect repair found!\n")
        else:
            f.write("Status: FAILURE - No perfect repair found.\n")
        f.write(f"Final Fitness: {achieved_fitness}/{max_fitness}\n")
        f.write(f"Generations Run: {generations_run}\n")
        if success:
            f.write(f"Solution Found At: Generation {final_generation}\n")
        f.write("\n")
        
        # Fault Localization
        f.write("-" * 70 + "\n")
        f.write("FAULT LOCALIZATION\n")
        f.write("-" * 70 + "\n")
        f.write("Suspicious lines identified (higher weight = more suspicious):\n")
        for line_num, weight in weighted_lines:
            if weight > 0:
                f.write(f"  Line {line_num}: weight = {weight}\n")
        f.write("\n")
        
        # Code Changes
        f.write("-" * 70 + "\n")
        f.write("CODE CHANGES\n")
        f.write("-" * 70 + "\n")
        
        if repaired_lines:
            changes = find_changed_lines(original_lines, repaired_lines)
            
            if changes:
                f.write(f"Total lines changed: {len(changes)}\n\n")
                for line_num, before, after in changes:
                    f.write(f"Line {line_num}:\n")
                    f.write(f"  BEFORE: {before}\n")
                    f.write(f"  AFTER:  {after}\n\n")
            else:
                f.write("No code changes detected (unexpected).\n")
        else:
            f.write("No successful repair to compare.\n")
        
        # Original Code
        f.write("-" * 70 + "\n")
        f.write("ORIGINAL CODE (patient.py)\n")
        f.write("-" * 70 + "\n")
        for i, line in enumerate(original_lines, 1):
            f.write(f"{i:3}: {line.rstrip()}\n")
        f.write("\n")
        
        # Repaired Code (if available)
        if repaired_lines:
            f.write("-" * 70 + "\n")
            f.write("REPAIRED CODE (repaired_solution.py)\n")
            f.write("-" * 70 + "\n")
            for i, line in enumerate(repaired_lines, 1):
                f.write(f"{i:3}: {line.rstrip()}\n")
        
        f.write("\n" + "=" * 70 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 70 + "\n")
    
    return report_path


def initialize_population(original_lines, weighted_lines, population_size):
    """
    Creates the initial population of variants.
    
    Strategy:
    - Variant 0: The original (buggy) program (baseline).
    - Variants 1+: Mutated versions of the original.
    """
    population = []
    
    # First variant is the original
    population.append(original_lines[:])
    
    # Generate more mutants
    for i in range(1, population_size):
        mutant = None
        attempts = 0
        
        while mutant is None and attempts < 10:
            mutant = apply_random_mutation(original_lines[:], weighted_lines)
            attempts += 1
        
        if mutant is None:
            mutant = original_lines[:]
            
        population.append(mutant)
    
    return population


def evaluate_population(population, harness, verbose=False):
    """
    Evaluates fitness for ALL variants in the population.
    
    Returns:
        list of tuples: [(variant_lines, fitness_score), ...]
    """
    scored_population = []
    
    for i, variant in enumerate(population):
        # Save to unique temp file
        filepath = get_temp_filepath(i)
        save_variant_to_file(variant, filepath)
        
        # Evaluate fitness using the harness
        debug = verbose and i < 3  # Debug mode for first 3 variants if verbose
        fitness = harness.evaluate_file(filepath, debug=debug)
        scored_population.append((variant, fitness))
        
        # Show non-zero fitness
        if fitness > 0:
            print(f"  Variant {i}: fitness = {fitness}")
        
        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"  Evaluated {i + 1}/{len(population)} variants...")
    
    return scored_population


def select_survivors(scored_population):
    """
    Selects the top 50% of variants based on fitness.
    
    Returns:
        tuple: (survivors list, best fitness this generation)
    """
    sorted_pop = sorted(scored_population, key=lambda x: x[1], reverse=True)
    
    num_survivors = int(len(sorted_pop) * SURVIVOR_RATIO)
    survivors = [variant for variant, fitness in sorted_pop[:num_survivors]]
    
    return survivors, sorted_pop[0][1]


def repopulate(survivors, weighted_lines, population_size):
    """
    Fills the population back to population_size by mutating survivors.
    """
    new_population = survivors[:]
    
    while len(new_population) < population_size:
        parent = random.choice(survivors)[:]
        
        child = None
        attempts = 0
        while child is None and attempts < 10:
            child = apply_random_mutation(parent, weighted_lines)
            attempts += 1
        
        if child is None:
            child = parent[:]
        
        new_population.append(child)
    
    return new_population


def run_evolution(benchmark_dir, num_generations, population_size, verbose=False):
    """
    Main entry point: Runs the complete genetic algorithm loop.
    
    Args:
        benchmark_dir: Path to the benchmark directory
        num_generations: Number of generations to run
        population_size: Size of the population
        verbose: Enable verbose output
        
    Returns:
        The repaired variant if found, None otherwise
    """
    print("=" * 60)
    print("       AUTOMATED PROGRAM REPAIR - GENETIC EVOLUTION")
    print("=" * 60)
    
    benchmark_name = os.path.basename(benchmark_dir)
    print(f"\nBenchmark: {benchmark_name}")
    
    # Step 1: Initialize the test harness
    print("\n[Phase 1] Loading benchmark...")
    harness = TestHarness(benchmark_dir)
    print(f"  Function: {harness.function_name}()")
    print(f"  Max fitness: {harness.max_fitness}")
    print(f"  Positive tests: {len(harness.positive_tests)} (weight: {harness.positive_weight})")
    print(f"  Negative tests: {len(harness.negative_tests)} (weight: {harness.negative_weight})")
    
    # Step 2: Load the patient program
    print("\n[Phase 2] Loading patient program...")
    original_lines = load_program(harness.get_patient_path())
    print(f"  Loaded {len(original_lines)} lines from patient.py")
    
    # Step 3: Run fault localization
    print("\n[Phase 3] Running fault localization...")
    weighted_lines = harness.run_fault_localization()
    print(f"  Identified {len(weighted_lines)} executable lines with suspicion weights:")
    for line, weight in weighted_lines:
        if weight > 0:
            print(f"    Line {line}: weight = {weight}")
    
    # Step 4: Setup temp directory
    print("\n[Phase 4] Setting up workspace...")
    setup_temp_directory()
    print(f"  Created: {TEMP_DIR}/")
    
    # Step 5: Initialize population
    print("\n[Phase 5] Initializing population...")
    population = initialize_population(original_lines, weighted_lines, population_size)
    print(f"  Created {len(population)} variants")
    
    # Step 6: The Evolution Loop
    print(f"\n[Phase 6] Starting Evolution ({num_generations} generations)...")
    print("-" * 60)
    
    best_variant = None
    best_fitness = 0.0
    success = False
    final_generation = 0
    repaired_lines = None
    
    for generation in range(1, num_generations + 1):
        print(f"\n>>> GENERATION {generation}/{num_generations}")
        
        # Evaluate all variants
        print("  Evaluating fitness...")
        scored_population = evaluate_population(
            population, harness, verbose=(verbose and generation == 1)
        )
        
        # Check for perfect solution
        for variant, fitness in scored_population:
            if fitness >= harness.max_fitness:
                print("\n" + "=" * 60)
                print("  SUCCESS! PERFECT REPAIR FOUND!")
                print("=" * 60)
                
                # Save the winning variant to benchmark folder
                solution_path = os.path.join(benchmark_dir, "repaired_solution.py")
                save_variant_to_file(variant, solution_path)
                print(f"\n  Solution saved to: {solution_path}")
                print(f"  Fitness: {fitness}/{harness.max_fitness}")
                print(f"  Generation: {generation}")
                
                # Find and display the changes
                changes = find_changed_lines(original_lines, variant)
                if changes:
                    print(f"\n  Code changes ({len(changes)} lines modified):")
                    for line_num, before, after in changes:
                        print(f"    Line {line_num}:")
                        print(f"      BEFORE: {before}")
                        print(f"      AFTER:  {after}")
                
                # Write summary report
                report_path = write_summary_report(
                    benchmark_dir=benchmark_dir,
                    benchmark_name=benchmark_name,
                    function_name=harness.function_name,
                    success=True,
                    generations_run=num_generations,
                    final_generation=generation,
                    max_fitness=harness.max_fitness,
                    achieved_fitness=fitness,
                    original_lines=original_lines,
                    repaired_lines=variant,
                    weighted_lines=weighted_lines
                )
                print(f"\n  Report saved to: {report_path}")
                
                cleanup_temp_directory()
                return variant
            
            if fitness > best_fitness:
                best_fitness = fitness
                best_variant = variant[:]
        
        final_generation = generation
        
        # Selection
        survivors, gen_best = select_survivors(scored_population)
        print(f"  Best fitness: {gen_best}/{harness.max_fitness}")
        print(f"  Survivors: {len(survivors)}")
        
        # Repopulate
        population = repopulate(survivors, weighted_lines, population_size)
    
    # Evolution complete without perfect solution
    print("\n" + "=" * 60)
    print("  Evolution complete. No perfect repair found.")
    print("=" * 60)
    print(f"\n  Best fitness achieved: {best_fitness}/{harness.max_fitness}")
    
    if best_variant:
        best_path = os.path.join(benchmark_dir, "best_attempt.py")
        save_variant_to_file(best_variant, best_path)
        print(f"  Best attempt saved to: {best_path}")
    
    # Write summary report even for failures
    report_path = write_summary_report(
        benchmark_dir=benchmark_dir,
        benchmark_name=benchmark_name,
        function_name=harness.function_name,
        success=False,
        generations_run=num_generations,
        final_generation=final_generation,
        max_fitness=harness.max_fitness,
        achieved_fitness=best_fitness,
        original_lines=original_lines,
        repaired_lines=best_variant,
        weighted_lines=weighted_lines
    )
    print(f"  Report saved to: {report_path}")
    
    cleanup_temp_directory()
    return None


def main():
    """Main entry point."""
    args = parse_args()
    
    try:
        benchmark_dir = resolve_benchmark_path(args.benchmark)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    run_evolution(
        benchmark_dir=benchmark_dir,
        num_generations=args.generations,
        population_size=args.population,
        verbose=args.verbose
    )


if __name__ == "__main__":
    main()
