# Automated Program Repair - Genetic Programming Approach

**Task 03: GenProg Implementation**  
University Project - Automated Program Repair using Genetic Algorithms

---

##  Project Structure

```
phase1/
├── evolution.py          # Main genetic algorithm implementation
├── mutation.py           # Mutation operators (DELETE, INSERT, SWAP, EXPRESSION, BOOLEAN)
├── localization.py       # Fault localization using spectrum-based analysis
├── test_harness.py       # Generic test framework with timeout protection
├── README.md             # This file
│
└── benchmarks/           # 5 benchmark programs with bugs
    ├── benchmark1/       # Wrong comparison operator (< vs >)
    │   ├── patient.py           # Buggy program
    │   ├── tests.json           # Test cases
    │   ├── repaired_solution.py # Fixed program (generated)
    │   └── report_summary.txt   # Detailed report (generated)
    │
    ├── benchmark2/       # Wrong comparison in condition
    ├── benchmark3/       # Wrong guard condition  
    ├── benchmark4/       # Boolean logic error (or vs and)
    └── benchmark5/       # Wrong comparison operator
```

---

##  Quick Start

### Run on a Single Benchmark

```bash
python evolution.py benchmark1
```

### Run with Custom Parameters

```bash
python evolution.py benchmark2 --generations 50 --population 60
```

### Run in Verbose Mode

```bash
python evolution.py benchmark3 -v
```

---

## 🧬 Genetic Operators

### Mutation Operators

| Operator | Description | Example |
|----------|-------------|---------|
| **DELETE** | Replace line with `pass` | `x = 5` → `pass` |
| **INSERT** | Copy line to another location | Add line from elsewhere |
| **SWAP** | Exchange two lines | Swap line 5 and line 8 |
| **EXPRESSION** | Mutate comparison operators | `<` → `>`, `<=` → `>=` |
| **BOOLEAN** | Swap boolean operators | `and` → `or` |

### Crossover Operator

| Operator | Description |
|----------|-------------|
| **ONE-POINT CROSSOVER** | Combines two parent programs by picking a pivot point and swapping code sections |

**How Crossover Works:**
1. Select two parent programs from survivors
2. Pick a random pivot line index
3. Create offspring: `parent_a[:pivot] + parent_b[pivot:]`
4. Validate syntax (crossover can break Python indentation)
5. With 50% probability, also apply mutation to offspring

**Expression Mutation** is the key innovation beyond standard GenProg. It enables fixing character-level bugs that can't be fixed by line-level operations.

---

## 📈 Algorithm Overview

Following the GenProg paper (Figure 1), the algorithm consists of:

1. **Fault Localization**: Identify suspicious lines using spectrum-based analysis
2. **Population Initialization**: Create 40 variants through mutation
3. **Fitness Evaluation**: Test each variant against positive and negative tests
4. **Selection**: Keep top 50% based on fitness
5. **Repopulation** (Crossover + Mutation):
   - Select two parents from survivors
   - Apply **crossover** to create offspring
   - With 50% probability, apply **mutation** to offspring
   - Add valid offspring to population
6. **Repeat**: Continue for 50 generations or until perfect repair found

**Fitness Function**: `fitness = (positive_tests_passed × 1.0) + (negative_tests_passed × 10.0)`  
**Maximum Fitness**: 33.0 (3 positive + 3 negative tests)

---

##  Test Format (tests.json)

Each benchmark has a `tests.json` file defining test cases:

```json
{
    "function_name": "find_max",
    "max_fitness": 33.0,
    "positive_tests": {
        "weight": 1.0,
        "cases": [
            {"input": [[5, 5, 5]], "expected": 5}
        ]
    },
    "negative_tests": {
        "weight": 10.0,
        "cases": [
            {"input": [[-1, 0, 5]], "expected": 5}
        ]
    }
}
```

---

##  Results

All 5 benchmarks successfully repaired:

| Benchmark | Bug Type | Success | Generations |
|-----------|----------|---------|-------------|
| benchmark1 | Wrong comparison (`<` vs `>`) |  | 1 |
| benchmark2 | Wrong comparison condition |  | 1 |
| benchmark3 | Wrong guard condition |  | 1 |
| benchmark4 | Boolean logic (`or` vs `and`) |  | 1 |
| benchmark5 | Wrong comparison (`<` vs `>`) |  | 1 |

Each benchmark directory contains:
- `repaired_solution.py` - The fixed code
- `report_summary.txt` - Detailed repair report showing:
  - Which lines changed
  - Original vs repaired code
  - Fault localization results
  - Test results

---

##  Timeout Protection

The test harness includes timeout protection to prevent infinite loops in buggy variants:
- Each test has a 2-second timeout
- Uses `concurrent.futures.ThreadPoolExecutor` for safe execution
- Timeouts count as test failures (0 fitness)

---

##  Key Design Decisions

1. **Expression Mutation**: Added to handle character-level bugs (comparison operators)
2. **Boolean Mutation**: Added to handle `and`/`or` logic errors
3. **Dynamic Test Loading**: Tests defined in JSON for easy benchmark creation
4. **Unique Module Names**: Prevents Python import caching issues
5. **Temporary Variant Files**: Each variant saved to unique file for evaluation

---

## References

- GenProg: Automated Program Repair via Genetic Programming (Weimer et al., 2009)
- Spectrum-Based Fault Localization
- Genetic Algorithms for Software Engineering

---

## Usage Examples

### Example 1: View Help
```bash
python evolution.py --help
```

### Example 2: Run with Different Population
```bash
python evolution.py benchmark1 --population 100
```

### Example 3: Longer Evolution
```bash
python evolution.py benchmark2 --generations 100
```

---

##  Project Requirements (Task03.pdf)

This implementation fulfills all requirements:

- **Fault Localization**: `localization.py` implements spectrum-based analysis
- **Mutation Operators**: 5 operators including GenProg's 3 + 2 custom
- **Fitness Function**: Weighted test-based evaluation
- **Genetic Loop**: Population management, selection, repopulation
- **5 Benchmarks**: Diverse bug types with automated test suites
- **Reports**: Detailed summaries for each repair attempt

---

## Output Files

After running evolution, each benchmark will contain:

1. **repaired_solution.py** - The fixed program
2. **report_summary.txt** - Contains:
   - Success/failure status
   - Line-by-line code changes
   - Fault localization weights
   - Complete original and repaired code
   - Generation count and fitness achieved

---

## System Requirements

- Python 3.8+
- Standard library only (no external dependencies)
- Works on Windows, Linux, macOS

---

## Troubleshooting

**Issue**: "Benchmark not found"  
**Solution**: Ensure you're in the `phase1` directory when running

**Issue**: Timeout messages appearing  
**Solution**: This is normal - variants with infinite loops are detected and skipped

**Issue**: Low fitness scores  
**Solution**: Increase generations with `--generations` flag

---

**Author**: Automated Program Repair Implementation  
**Course**: University Task 03  
**Date**: January 2026
