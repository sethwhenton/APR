import os
import json
import sys

def create_benchmark_wizard():
    print("=" * 60)
    print("  NEW BENCHMARK CREATION WIZARD")
    print("=" * 60)
    print("This script helps you set up a new test case for the APR tool.\n")
    
    # Get benchmark name
    while True:
        name = input("Enter benchmark name (e.g., 'benchmark_final'): ").strip()
        if name:
            break
            
    # Check if directory exists
    base_dir = "benchmarks"
    target_dir = os.path.join(base_dir, name)
    
    if os.path.exists(target_dir):
        print(f"\n❌ Error: Directory '{target_dir}' already exists!")
        return
        
    # Get function details
    func_name = input("Enter the name of the function to repair (e.g., 'sort_list'): ").strip()
    
    # Create directory
    os.makedirs(target_dir)
    print(f"\n✅ Created directory: {target_dir}")
    
    # Create template patient.py
    patient_content = f'''def {func_name}(arg1):
    """
    TODO: Paste the buggy code here.
    The function name MUST match: {func_name}
    """
    # Your buggy code goes here
    pass
'''
    with open(os.path.join(target_dir, "patient.py"), 'w') as f:
        f.write(patient_content)
    print(f"✅ Created template: {os.path.join(target_dir, 'patient.py')}")
    
    # Create template tests.json
    tests_content = {
        "function_name": func_name,
        "max_fitness": 33.0,
        "positive_tests": {
            "weight": 1.0,
            "cases": [
                {
                    "input": ["EXAMPLE_INPUT_1"], 
                    "expected": "EXAMPLE_OUTPUT_1",
                    "note": "Regression test that should pass"
                }
            ]
        },
        "negative_tests": {
            "weight": 10.0,
            "cases": [
                {
                    "input": ["BUG_TRIGGER_INPUT"], 
                    "expected": "CORRECT_OUTPUT",
                    "note": "Test case that currently fails"
                }
            ]
        }
    }
    
    with open(os.path.join(target_dir, "tests.json"), 'w') as f:
        json.dump(tests_content, f, indent=4)
    print(f"✅ Created template: {os.path.join(target_dir, 'tests.json')}")
    
    print("\n" + "=" * 60)
    print("  SETUP COMPLETE!")
    print("=" * 60)
    print(f"\nNext Steps for the Lecturer:")
    print(f"1. Open '{target_dir}\\patient.py' and paste the buggy code.")
    print(f"2. Open '{target_dir}\\tests.json' and define the test cases.")
    print(f"3. Run the tool: python evolution.py {name}")

if __name__ == "__main__":
    create_benchmark_wizard()
