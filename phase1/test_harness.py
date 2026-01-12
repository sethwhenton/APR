import patient

# === DEFINITION OF TESTS ===

# Positive Tests: These represent scenarios that ALREADY PASS despite the bug.
# Since our bug finds the MIN instead of MAX, lists with identical elements or single elements will pass.
# GenProg Weight: 1.0 (Standard regression testing)
POSITIVE_TESTS = [
    ([5, 5, 5], 5),
    ([42], 42),
    ([0, 0, 0], 0)
]

# Negative Tests: These represent scenarios that FAIL and reveal the bug.
# We want the 'max', but the bug gives us 'min'.
# GenProg Weight: 10.0 (High priority to fix)
NEGATIVE_TESTS = [
    ([-1, 0, 5], 5),      # Buggy code returns -1
    ([1, 2, 3, 4], 4),    # Buggy code returns 1
    ([10, 30, 20], 30)    # Buggy code returns 10
]

WEIGHT_POS = 1.0
WEIGHT_NEG = 10.0

def run_test(input_val, expected):
    """
    Executes a single test case against the patient.py module.
    Returns True if strict equality holds, False otherwise.
    """
    try:
        # We assume the input is safe to pass directly
        result = patient.find_max(input_val)
        return result == expected
    except Exception:
        return False

def calculate_fitness():
    """
    Calculates the weighted fitness score.
    
    Logic:
    1. Iterate through Positive Tests. If pass -> +1.0
    2. Iterate through Negative Tests. If pass -> +10.0
    
    Why this structure?
    In GenProg, the goal is to repair the specific defect (Negative Test) 
    without breaking valid existing behavior (Positive Tests). 
    Weighting negative tests higher guides the genetic algorithm to prioritize 
    mutations that fix the bug, even if they temporarily break some positive tests 
    (though the ideal solution satisfies both).
    """
    fitness = 0.0
    
    # Run Positive Tests
    for inp, expected in POSITIVE_TESTS:
        if run_test(inp, expected):
            fitness += WEIGHT_POS
            
    # Run Negative Tests
    for inp, expected in NEGATIVE_TESTS:
        if run_test(inp, expected):
            fitness += WEIGHT_NEG
            
    return fitness

if __name__ == "__main__":
    score = calculate_fitness()
    
    # Calculate max possible fitness for normalization/display
    max_fitness = (len(POSITIVE_TESTS) * WEIGHT_POS) + (len(NEGATIVE_TESTS) * WEIGHT_NEG)
    
    print(f"--- Fitness Evaluation ---")
    print(f"Current Fitness: {score} / {max_fitness}")
    
    print("\n--- Detailed Breakdown ---")
    print("Positive Tests (Weight 1.0):")
    for i, (inp, exp) in enumerate(POSITIVE_TESTS):
        passed = run_test(inp, exp)
        status = "PASS" if passed else "FAIL"
        print(f"  Test {i+1} [Input: {inp}]: {status}")

    print("\nNegative Tests (Weight 10.0):")
    for i, (inp, exp) in enumerate(NEGATIVE_TESTS):
        passed = run_test(inp, exp)
        status = "PASS" if passed else "FAIL"
        print(f"  Test {i+1} [Input: {inp}]: {status}")
