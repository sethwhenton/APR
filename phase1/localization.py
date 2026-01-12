import sys
import os
import patient
from test_harness import POSITIVE_TESTS, NEGATIVE_TESTS

# We need to track which lines in patient.py are executed.
# We'll stick to the strict definitions from the Task 03 PDF.

def get_coverage(func, arg):
    """
    Runs the function 'func' with argument 'arg' with tracing enabled.
    Returns a set of line numbers executed in 'patient.py'.
    """
    covered_lines = set()
    
    # We need the absolute path to filter correctly
    patient_file = os.path.abspath(patient.__file__)
    # Handle .pyc or similar extensions just in case (though usually __file__ is .py)
    if patient_file.endswith(".pyc"): 
        patient_file = patient_file[:-1]
        
    def trace_func(frame, event, arg):
        if event == 'line':
            # Check if this frame is executing code in patient.py
            # frame.f_code.co_filename usually returns absolute path
            code_path = os.path.abspath(frame.f_code.co_filename)
            if code_path == patient_file:
                covered_lines.add(frame.f_lineno)
        return trace_func

    # Start tracing
    sys.settrace(trace_func)
    try:
        func(arg)
    except Exception:
        # We expect exceptions might happen in buggy code, we still want coverage
        pass
    finally:
        # Stop tracing
        sys.settrace(None)
        
    return covered_lines

def run_localization():
    """
    Runs fault localization to assign weights to each line in patient.py.
    
    Logic per Task 03 PDF / GenProg:
    - Set P: Lines executed by at least one executing Positive Test.
    - Set F: Lines executed by at least one executing Negative Test.
    
    Weights:
    - 1.0: In F but NOT in P (Executed ONLY by failing tests).
           Reason: Highly suspicious. Changing this likely fixes the bug without breaking passing tests.
    - 0.1: In F AND in P (Executed by both).
           Reason: Less suspicious because it's used for correct behavior too. Changing it is risky.
    - 0.0: Not in F (Not executed by failing tests).
           Reason: If the buggy case doesn't run this code, changing it won't fix the bug.
    """
    
    lines_p = set()
    lines_f = set()
    
    # 1. Collect Coverage from Positive Tests
    print("Tracing Positive Tests...")
    for inp, expected in POSITIVE_TESTS:
        lines = get_coverage(patient.find_max, inp)
        lines_p.update(lines)
        
    # 2. Collect Coverage from Negative Tests
    print("Tracing Negative Tests...")
    for inp, expected in NEGATIVE_TESTS:
        lines = get_coverage(patient.find_max, inp)
        lines_f.update(lines)
        
    # 3. Calculate Weights
    # We should look at all executable lines in the file, or just the ones covered.
    # Typically we care about the union of covered lines.
    all_covered_lines = lines_p.union(lines_f)
    sorted_lines = sorted(list(all_covered_lines))
    
    results = []
    
    for line in sorted_lines:
        weight = 0.0
        if line in lines_f:
            if line in lines_p:
                weight = 0.1 # Intersection
            else:
                weight = 1.0 # Only failing
        else:
            weight = 0.0 # Only passing (should correspond to PDF 'All other statements')
            
        results.append((line, weight))
        
    # Display Results
    print("\n--- Fault Localization Results ---")
    print(f"{'Line #':<10} {'Weight':<10} {'Status'}")
    print("-" * 40)
    
    for line, weight in results:
        status_str = ""
        if weight == 1.0:
            status_str = "HIGHLY SUSPICIOUS (Fail Only)"
        elif weight == 0.1:
            status_str = "Suspicious (Fail & Pass)"
        else:
            status_str = "Safe (Pass Only)"
            
        print(f"{line:<10} {weight:<10.1f} {status_str}")

if __name__ == "__main__":
    run_localization()
