import random
import ast

def load_program(filepath):
    """Loads the program as a list of lines."""
    with open(filepath, 'r') as f:
        return f.readlines()

def save_program_to_string(lines):
    """Converts the list of lines back to a single string."""
    return "".join(lines)

# === SYNTAX VALIDATION ===

def is_valid_syntax(lines):
    """
    Checks if the proposed mutation results in valid Python syntax.
    This prevents wasting time on broken code (compile errors).
    """
    code_str = save_program_to_string(lines)
    try:
        ast.parse(code_str)
        return True
    except SyntaxError:
        return False

# === MUTATION OPERATORS ===

def mutate_delete(lines, target_idx):
    """
    Operator: DELETE
    Removes the statement at target_idx.
    To avoid empty blocks (e.g., 'if True: [nothing]'), we replace with 'pass'
    instead of deleting specific indentation lines entirely.
    """
    new_lines = lines[:]
    original = new_lines[target_idx]
    
    # Preserve indentation
    indentation = original[:len(original) - len(original.lstrip())]
    
    # Replace with 'pass' to maintain valid syntax for empty blocks
    new_lines[target_idx] = f"{indentation}pass\n"
    
    return new_lines

def mutate_insert(lines, target_idx, source_idx):
    """
    Operator: INSERT
    Inserts the code from source_idx AFTER target_idx.
    """
    new_lines = lines[:]
    source_line = new_lines[source_idx]
    target_line = new_lines[target_idx]
    
    # We must match the indentation of the TARGET line for the insertion to make sense.
    target_indent = target_line[:len(target_line) - len(target_line.lstrip())]
    clean_source = source_line.strip()
    
    inserted_line = f"{target_indent}{clean_source}\n"
    new_lines.insert(target_idx + 1, inserted_line)
    
    return new_lines

def mutate_swap(lines, idx_a, idx_b):
    """
    Operator: SWAP
    Swaps the content of line A and line B, while preserving original indentations.
    This is critical because identifying correct indentation swaps is hard.
    """
    new_lines = lines[:]
    
    line_a = new_lines[idx_a]
    line_b = new_lines[idx_b]
    
    # Extract indentations
    indent_a = line_a[:len(line_a) - len(line_a.lstrip())]
    indent_b = line_b[:len(line_b) - len(line_b.lstrip())]
    
    # Check if lines are just whitespace/comments to avoid weird swaps
    if not line_a.strip() or not line_b.strip():
        return new_lines

    # Construct swapped lines with ORIGINAL positions' indentation
    new_lines[idx_a] = f"{indent_a}{line_b.strip()}\n"
    new_lines[idx_b] = f"{indent_b}{line_a.strip()}\n"
    
    return new_lines

# === SELECTION LOGIC ===

def select_line_by_weight(weighted_lines):
    """
    Roulette Wheel Selection based on suspiciousness weights.
    Returns the INDEX of the selected line.
    """
    lines, weights = zip(*weighted_lines)
    total_weight = sum(weights)
    
    if total_weight == 0:
        return random.choice(lines)
        
    r = random.uniform(0, total_weight)
    current = 0
    for line_idx, weight in weighted_lines:
        current += weight
        if current > r:
            return line_idx
    
    return lines[0] # Fallback

def apply_random_mutation(lines, weighted_lines_info):
    """
    Main entry point for mutation.
    1. Selects a 'faulty' line based on weights (Target for Delete/Swap/Insert Dest).
    2. Selects a 'fix' line randomly from the codebase (Source for Insert/Swap).
    3. Randomly picks an operator.
    4. Applies mutation.
    5. Validates syntax. If invalid, returns None (so we can retry).
    """
    
    # Select the statement to modify (the 'Suspicious' location)
    # weighted_lines_info is list of tuples: (line_number_1_based, weight)
    # We need 0-based index for list access
    
    # Filter only non-zero weights if possible, else random
    candidates = [(L-1, W) for L, W in weighted_lines_info if W > 0]
    if not candidates:
        candidates = [(L-1, 1.0) for L, W in weighted_lines_info]
        
    target_idx = select_line_by_weight(candidates)
    
    # Select a source line (any executable line in the program is a candidate for code bank)
    # For simplicity, we assume any line in 'candidates' is a valid code bank
    source_idx = random.choice(candidates)[0]
    
    op = random.choice(['delete', 'insert', 'swap'])
    
    mutated_lines = []
    
    if op == 'delete':
        print(f"Applying DELETE at line {target_idx+1}")
        mutated_lines = mutate_delete(lines, target_idx)
    elif op == 'insert':
        print(f"Applying INSERT: Copying line {source_idx+1} to after {target_idx+1}")
        mutated_lines = mutate_insert(lines, target_idx, source_idx)
    elif op == 'swap':
        print(f"Applying SWAP: Swapping line {target_idx+1} with line {source_idx+1}")
        mutated_lines = mutate_swap(lines, target_idx, source_idx)
        
    # Syntax Check
    if is_valid_syntax(mutated_lines):
        return mutated_lines
    else:
        print("Mutation resulted in invalid syntax! Discarding.")
        return None

if __name__ == "__main__":
    # Test Run
    import localization # Import merely to run it again or we reuse known weights
    
    print("--- Loading Patient ---")
    original_lines = load_program("patient.py")
    
    # Mock weights based on previous Step output (Lines 6, 9, 11, 12, 15 have 0.1)
    mock_weights = [
        (6, 0.1), (9, 0.1), (11, 0.1), (12, 0.1), (15, 0.1)
    ]
    
    print("--- Attempting Mutation ---")
    mutated = None
    attempt = 0
    while mutated is None and attempt < 10:
        mutated = apply_random_mutation(original_lines, mock_weights)
        attempt += 1
        
    if mutated:
        print("\n--- Mutated Program Result ---")
        print(save_program_to_string(mutated))
    else:
        print("Failed to generate valid mutation.")
