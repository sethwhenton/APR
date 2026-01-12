import random
import ast
import re

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


# === EXPRESSION MUTATION (The Bug Fixer!) ===

# All possible comparison operator mutations
# Each operator can mutate to multiple alternatives
COMPARISON_MUTATIONS = {
    '<': ['>', '<=', '!='],      # < can become >, <=, or !=
    '>': ['<', '>=', '!='],      # > can become <, >=, or !=
    '<=': ['>=', '<', '=='],     # <= can become >=, <, or ==
    '>=': ['<=', '>', '=='],     # >= can become <=, >, or ==
    '==': ['!=', '<=', '>='],    # == can become !=, <=, or >=
    '!=': ['==', '<', '>'],      # != can become ==, <, or >
}

# Regex pattern to find comparison operators
# Order matters: check longer operators first (<=, >=) before shorter ones (<, >)
COMPARISON_PATTERN = re.compile(r'(<=|>=|==|!=|<|>)')


def mutate_expression(lines, target_idx):
    """
    Operator: EXPRESSION MUTATION
    
    Finds comparison operators in the target line and swaps them with opposites.
    
    This is fundamentally different from GenProg's standard operators:
    - DELETE, INSERT, SWAP work at the LINE level (copy/move entire statements)
    - EXPRESSION works at the TOKEN level (modify individual operators)
    
    Why is this powerful?
    - Many bugs are "off-by-one" logic errors: < instead of >, == instead of !=
    - These can't be fixed by moving lines around
    - We need to surgically change the operator itself
    
    Example:
        Input:  "if n < current:"
        Output: "if n > current:"
    """
    new_lines = lines[:]
    target_line = new_lines[target_idx]
    
    # Find all comparison operators in this line
    matches = list(COMPARISON_PATTERN.finditer(target_line))
    
    if not matches:
        # No comparison operators found, can't mutate
        return None
    
    # Pick a random operator to swap
    match = random.choice(matches)
    original_op = match.group()
    # Pick a random replacement from the possible mutations for this operator
    replacement_op = random.choice(COMPARISON_MUTATIONS[original_op])
    
    # Build the new line with the swapped operator
    # We replace only the first occurrence at the matched position
    new_line = (
        target_line[:match.start()] + 
        replacement_op + 
        target_line[match.end():]
    )
    
    new_lines[target_idx] = new_line
    
    return new_lines


# === BOOLEAN MUTATION ===

# Mapping of boolean operators to their opposites
BOOLEAN_SWAPS = {
    ' and ': ' or ',
    ' or ': ' and ',
}

# Pattern to find boolean operators (with spaces to avoid matching 'android' etc.)
BOOLEAN_PATTERN = re.compile(r'( and | or )')


def mutate_boolean(lines, target_idx):
    """
    Operator: BOOLEAN MUTATION
    
    Finds boolean operators (and/or) in the target line and swaps them.
    
    This fixes common logic bugs where:
    - 'and' should be 'or' (too restrictive condition)
    - 'or' should be 'and' (too permissive condition)
    
    Example:
        Input:  "if has_length or has_digit:"
        Output: "if has_length and has_digit:"
    """
    new_lines = lines[:]
    target_line = new_lines[target_idx]
    
    # Find all boolean operators in this line
    matches = list(BOOLEAN_PATTERN.finditer(target_line))
    
    if not matches:
        return None
    
    # Pick a random operator to swap
    match = random.choice(matches)
    original_op = match.group()
    replacement_op = BOOLEAN_SWAPS[original_op]
    
    # Build the new line
    new_line = (
        target_line[:match.start()] + 
        replacement_op + 
        target_line[match.end():]
    )
    
    new_lines[target_idx] = new_line
    
    return new_lines


# === CROSSOVER OPERATOR ===

def crossover(parent_a, parent_b):
    """
    Operator: ONE-POINT CROSSOVER
    
    Combines genetic material from two parent programs to create two offspring.
    This fulfills Line 10 of Figure 1 in the GenProg paper.
    
    Algorithm:
    1. Pick a random pivot point (line index)
    2. Create offspring_1: parent_a[:pivot] + parent_b[pivot:]
    3. Create offspring_2: parent_b[:pivot] + parent_a[pivot:]
    
    Args:
        parent_a: First parent (list of lines)
        parent_b: Second parent (list of lines)
        
    Returns:
        tuple: (offspring_1, offspring_2) - both as list of lines
               Returns (None, None) if crossover produces invalid syntax
    
    Note: Crossover can easily break Python's indentation structure,
    so we validate syntax and return None for invalid offspring.
    """
    # Ensure we have valid parents
    if not parent_a or not parent_b:
        return None, None
    
    # Find the shorter parent length to avoid index errors
    min_len = min(len(parent_a), len(parent_b))
    
    if min_len <= 1:
        # Too short for meaningful crossover
        return None, None
    
    # Try multiple pivot points to find valid offspring
    max_attempts = 5
    
    for attempt in range(max_attempts):
        # Pick random pivot point (excluding first and last lines)
        # This gives us meaningful genetic exchange
        pivot = random.randint(1, min_len - 1)
        
        # Create two offspring using one-point crossover
        offspring_1 = parent_a[:pivot] + parent_b[pivot:]
        offspring_2 = parent_b[:pivot] + parent_a[pivot:]
        
        # Validate both offspring have valid Python syntax
        valid_1 = is_valid_syntax(offspring_1)
        valid_2 = is_valid_syntax(offspring_2)
        
        if valid_1 and valid_2:
            # Both offspring are valid
            return offspring_1, offspring_2
        elif valid_1:
            # Only first is valid, return it with a copy
            return offspring_1, offspring_1[:]
        elif valid_2:
            # Only second is valid, return it with a copy
            return offspring_2, offspring_2[:]
        # else: try another pivot point
    
    # All attempts failed - return None
    return None, None


def crossover_single(parent_a, parent_b):
    """
    Simplified crossover that returns a single valid offspring.
    
    This is easier to use in the repopulation loop.
    
    Returns:
        list: A single offspring, or None if crossover fails
    """
    offspring_1, offspring_2 = crossover(parent_a, parent_b)
    
    if offspring_1 is not None:
        # Randomly return one of the two offspring
        return random.choice([offspring_1, offspring_2])
    
    return None


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
    
    # Mutation operators with weights:
    # - expression (2x): comparison bugs are very common
    # - boolean (2x): and/or bugs are common
    # - delete, insert, swap: standard GenProg operators
    op = random.choice(['delete', 'insert', 'swap', 'expression', 'expression', 'boolean', 'boolean'])
    
    mutated_lines = None
    
    if op == 'delete':
        print(f"Applying DELETE at line {target_idx+1}")
        mutated_lines = mutate_delete(lines, target_idx)
    elif op == 'insert':
        print(f"Applying INSERT: Copying line {source_idx+1} to after {target_idx+1}")
        mutated_lines = mutate_insert(lines, target_idx, source_idx)
    elif op == 'swap':
        print(f"Applying SWAP: Swapping line {target_idx+1} with line {source_idx+1}")
        mutated_lines = mutate_swap(lines, target_idx, source_idx)
    elif op == 'expression':
        result = mutate_expression(lines, target_idx)
        if result:
            # Get the original and new line for display
            orig_line = lines[target_idx].strip()
            new_line = result[target_idx].strip()
            print(f"Applying EXPRESSION at line {target_idx+1}: '{orig_line}' -> '{new_line}'")
            mutated_lines = result
        else:
            print(f"EXPRESSION at line {target_idx+1}: No comparison operators found, skipping.")
            return None
    elif op == 'boolean':
        result = mutate_boolean(lines, target_idx)
        if result:
            orig_line = lines[target_idx].strip()
            new_line = result[target_idx].strip()
            print(f"Applying BOOLEAN at line {target_idx+1}: '{orig_line}' -> '{new_line}'")
            mutated_lines = result
        else:
            print(f"BOOLEAN at line {target_idx+1}: No boolean operators found, skipping.")
            return None
        
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
