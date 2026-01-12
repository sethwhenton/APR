"""
Test All Benchmarks - Verification Script

This script runs all 5 benchmarks to verify they work correctly.
Use this before final submission to ensure everything is working.

Usage:
    python test_all_benchmarks.py
"""

import subprocess
import sys
import os

BENCHMARKS = ['benchmark1', 'benchmark2', 'benchmark3', 'benchmark4', 'benchmark5']
GENERATIONS = 15  # Quick test with fewer generations

def test_benchmark(benchmark_name):
    """Test a single benchmark and return success status."""
    print(f"\n{'='*60}")
    print(f"Testing {benchmark_name}...")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            ['python', 'evolution.py', benchmark_name, '--generations', str(GENERATIONS)],
            capture_output=True,
            text=True,
            timeout=180  # 3 minute timeout
        )
        
        # Check if solution was found
        if 'SUCCESS! PERFECT REPAIR FOUND!' in result.stdout:
            print(f"✅ {benchmark_name}: PASSED - Repair found")
            return True
        else:
            print(f"⚠️  {benchmark_name}: No perfect repair (may need more generations)")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ {benchmark_name}: FAILED - Timeout")
        return False
    except Exception as e:
        print(f"❌ {benchmark_name}: FAILED - {e}")
        return False


def verify_output_files(benchmark_name):
    """Verify that required output files exist."""
    benchmark_dir = os.path.join('benchmarks', benchmark_name)
    
    required_files = ['patient.py', 'tests.json', 'repaired_solution.py', 'report_summary.txt']
    missing = []
    
    for file in required_files:
        if not os.path.exists(os.path.join(benchmark_dir, file)):
            missing.append(file)
    
    if missing:
        print(f"   Missing files: {', '.join(missing)}")
        return False
    return True


def main():
    """Run all benchmarks and report results."""
    print("="*60)
    print("  AUTOMATED PROGRAM REPAIR - BENCHMARK VERIFICATION")
    print("="*60)
    print(f"\nTesting {len(BENCHMARKS)} benchmarks with {GENERATIONS} generations each...")
    
    results = {}
    
    for benchmark in BENCHMARKS:
        success = test_benchmark(benchmark)
        results[benchmark] = success
        
        # Verify output files
        if success:
            files_ok = verify_output_files(benchmark)
            if files_ok:
                print(f"   Output files: OK")
            else:
                results[benchmark] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("  SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for benchmark, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}  {benchmark}")
    
    print(f"\nTotal: {passed}/{total} benchmarks passed")
    
    if passed == total:
        print("\n🎉 All benchmarks working! Ready for submission.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} benchmark(s) need attention.")
        print("   Try running failed benchmarks with more generations:")
        for benchmark, success in results.items():
            if not success:
                print(f"   python evolution.py {benchmark} --generations 50")
        return 1


if __name__ == "__main__":
    sys.exit(main())
