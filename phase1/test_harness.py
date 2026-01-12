"""
Generic Test Harness for Automated Program Repair

This module provides dynamic test loading and execution for any benchmark.
Tests are loaded from JSON files, allowing the tool to work with arbitrary programs.
"""

import json
import os
import sys
import importlib.util
import concurrent.futures
import threading

# Timeout for individual test execution (seconds)
# Prevents infinite loops from hanging the tool
TEST_TIMEOUT = 2.0


class TestHarness:
    """
    A generic test harness that loads tests from JSON and evaluates variants.
    
    Usage:
        harness = TestHarness("benchmarks/benchmark1")
        fitness = harness.evaluate_file("temp_variant.py")
    """
    
    def __init__(self, benchmark_dir):
        """
        Initialize the test harness for a specific benchmark.
        
        Args:
            benchmark_dir: Path to the benchmark directory containing patient.py and tests.json
        """
        self.benchmark_dir = os.path.abspath(benchmark_dir)
        self.patient_path = os.path.join(self.benchmark_dir, "patient.py")
        self.tests_path = os.path.join(self.benchmark_dir, "tests.json")
        
        # Load test configuration
        self._load_tests()
        
    def _load_tests(self):
        """Load test cases from the JSON file."""
        if not os.path.exists(self.tests_path):
            raise FileNotFoundError(f"Tests file not found: {self.tests_path}")
            
        with open(self.tests_path, 'r') as f:
            config = json.load(f)
            
        self.function_name = config["function_name"]
        self.max_fitness = config["max_fitness"]
        
        self.positive_tests = config["positive_tests"]["cases"]
        self.positive_weight = config["positive_tests"]["weight"]
        
        self.negative_tests = config["negative_tests"]["cases"]
        self.negative_weight = config["negative_tests"]["weight"]
        
    def get_patient_path(self):
        """Returns the path to the buggy program."""
        return self.patient_path
        
    def get_all_tests(self):
        """Returns all test cases with their weights."""
        return {
            "positive": (self.positive_tests, self.positive_weight),
            "negative": (self.negative_tests, self.negative_weight)
        }
        
    def evaluate_file(self, filepath, debug=False):
        """
        Evaluate a variant file against all test cases.
        
        Args:
            filepath: Path to the Python file to test
            debug: If True, print detailed test results
            
        Returns:
            float: The fitness score
        """
        fitness = 0.0
        abs_filepath = os.path.abspath(filepath)
        
        try:
            # Load the module dynamically with unique name
            module_name = f"variant_{os.path.basename(filepath).replace('.py', '')}_{id(self)}"
            
            if module_name in sys.modules:
                del sys.modules[module_name]
                
            spec = importlib.util.spec_from_file_location(module_name, abs_filepath)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Get the function to test
            if not hasattr(module, self.function_name):
                if debug:
                    print(f"    [ERROR] Function '{self.function_name}' not found in module")
                return 0.0
                
            func = getattr(module, self.function_name)
            
            # Run positive tests
            for test in self.positive_tests:
                try:
                    # Deep copy inputs to avoid mutation
                    inputs = self._deep_copy_inputs(test["input"])
                    
                    # Run with timeout to catch infinite loops
                    success, result = self._run_with_timeout(func, inputs)
                    expected = test["expected"]
                    
                    if not success:
                        if debug:
                            print(f"    [POS TIMEOUT] Input: {test['input']}, Error: {result}")
                        continue
                    
                    if result == expected:
                        fitness += self.positive_weight
                        if debug:
                            print(f"    [POS PASS] Input: {test['input']}, Expected: {expected}, Got: {result}")
                    elif debug:
                        print(f"    [POS FAIL] Input: {test['input']}, Expected: {expected}, Got: {result}")
                except Exception as e:
                    if debug:
                        print(f"    [POS ERROR] Input: {test['input']}, Error: {e}")
                        
            # Run negative tests
            for test in self.negative_tests:
                try:
                    inputs = self._deep_copy_inputs(test["input"])
                    
                    # Run with timeout to catch infinite loops
                    success, result = self._run_with_timeout(func, inputs)
                    expected = test["expected"]
                    
                    if not success:
                        if debug:
                            print(f"    [NEG TIMEOUT] Input: {test['input']}, Error: {result}")
                        continue
                    
                    if result == expected:
                        fitness += self.negative_weight
                        if debug:
                            print(f"    [NEG PASS] Input: {test['input']}, Expected: {expected}, Got: {result}")
                    elif debug:
                        print(f"    [NEG FAIL] Input: {test['input']}, Expected: {expected}, Got: {result}")
                except Exception as e:
                    if debug:
                        print(f"    [NEG ERROR] Input: {test['input']}, Error: {e}")
                        
        except SyntaxError as e:
            if debug:
                print(f"    [SYNTAX ERROR] {e}")
        except Exception as e:
            if debug:
                print(f"    [LOAD ERROR] {e}")
                
        return fitness
        
    def _deep_copy_inputs(self, inputs):
        """Create deep copies of input arguments to avoid mutation."""
        import copy
        return [copy.deepcopy(arg) for arg in inputs]
    
    def _run_with_timeout(self, func, args, timeout=TEST_TIMEOUT):
        """
        Run a function with a timeout to prevent infinite loops.
        
        Args:
            func: The function to call
            args: Arguments to pass (as a list)
            timeout: Maximum seconds to wait
            
        Returns:
            tuple: (success, result_or_error)
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args)
            try:
                result = future.result(timeout=timeout)
                return (True, result)
            except concurrent.futures.TimeoutError:
                return (False, "Timeout")
            except Exception as e:
                return (False, str(e))
        
    def get_coverage(self, func, args):
        """
        Run function with tracing to get line coverage.
        
        Args:
            func: The function to call
            args: Arguments to pass to the function
            
        Returns:
            set: Set of line numbers executed
        """
        covered_lines = set()
        
        def trace_func(frame, event, arg):
            if event == 'line':
                code_path = os.path.abspath(frame.f_code.co_filename)
                if code_path == self.patient_path:
                    covered_lines.add(frame.f_lineno)
            return trace_func
            
        sys.settrace(trace_func)
        try:
            func(*args)
        except Exception:
            pass
        finally:
            sys.settrace(None)
            
        return covered_lines
        
    def run_fault_localization(self):
        """
        Run fault localization on the original patient to get weighted lines.
        
        Returns:
            list: List of (line_number, weight) tuples
        """
        # Load the original patient module
        module_name = f"patient_original_{id(self)}"
        if module_name in sys.modules:
            del sys.modules[module_name]
            
        spec = importlib.util.spec_from_file_location(module_name, self.patient_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        func = getattr(module, self.function_name)
        
        lines_p = set()  # Lines executed by positive tests
        lines_f = set()  # Lines executed by negative tests
        
        # Collect coverage from positive tests
        for test in self.positive_tests:
            inputs = self._deep_copy_inputs(test["input"])
            lines = self.get_coverage(func, inputs)
            lines_p.update(lines)
            
        # Collect coverage from negative tests
        for test in self.negative_tests:
            inputs = self._deep_copy_inputs(test["input"])
            lines = self.get_coverage(func, inputs)
            lines_f.update(lines)
            
        # Calculate weights based on GenProg formula
        all_lines = lines_p.union(lines_f)
        weighted_lines = []
        
        for line in sorted(all_lines):
            if line in lines_f:
                if line in lines_p:
                    weight = 0.1  # In both - less suspicious
                else:
                    weight = 1.0  # Only in failing - highly suspicious
            else:
                weight = 0.0  # Only in passing - not suspicious
            weighted_lines.append((line, weight))
            
        return weighted_lines


# === Legacy compatibility (for old code that imports directly) ===

# Default values (will be overwritten when TestHarness is used)
POSITIVE_TESTS = []
NEGATIVE_TESTS = []
WEIGHT_POS = 1.0
WEIGHT_NEG = 10.0


def load_legacy_tests():
    """Load tests from the old patient.py location for backwards compatibility."""
    global POSITIVE_TESTS, NEGATIVE_TESTS, WEIGHT_POS, WEIGHT_NEG
    
    POSITIVE_TESTS = [
        ([5, 5, 5], 5),
        ([42], 42),
        ([0, 0, 0], 0)
    ]
    NEGATIVE_TESTS = [
        ([-1, 0, 5], 5),
        ([1, 2, 3, 4], 4),
        ([10, 30, 20], 30)
    ]
    WEIGHT_POS = 1.0
    WEIGHT_NEG = 10.0


# Load legacy tests on import
load_legacy_tests()


if __name__ == "__main__":
    # Test the harness with benchmark1
    print("Testing TestHarness with benchmark1...")
    harness = TestHarness("benchmarks/benchmark1")
    
    print(f"Function: {harness.function_name}")
    print(f"Max fitness: {harness.max_fitness}")
    print(f"Patient path: {harness.patient_path}")
    
    print("\nEvaluating original patient...")
    fitness = harness.evaluate_file(harness.patient_path, debug=True)
    print(f"\nFitness: {fitness}/{harness.max_fitness}")
