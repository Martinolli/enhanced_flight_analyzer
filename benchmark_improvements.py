# File: benchmark_improvements.py
import time
import pandas as pd
import numpy as np
from memory_profiler import profile
import matplotlib.pyplot as plt

@profile
def benchmark_fft_performance():
    """Benchmark FFT performance with and without unit conversion."""
    
    # Create test data
    n_points = 100000
    fs = 1000  # 1kHz sampling
    t = np.linspace(0, n_points/fs, n_points)
    
    # Acceleration data in g-units
    accel_g = 0.01 * np.sin(2 * np.pi * 10 * t) + 0.005 * np.random.normal(size=n_points)
    
    # Benchmark original implementation (no conversion)
    start_time = time.time()
    fft_original = np.fft.fft(accel_g)
    original_time = time.time() - start_time
    
    # Benchmark enhanced implementation (with conversion)
    start_time = time.time()
    accel_si = accel_g * 9.80665  # Convert to m/s²
    fft_enhanced = np.fft.fft(accel_si)
    enhanced_time = time.time() - start_time
    
    print(f"Original FFT time: {original_time:.4f} seconds")
    print(f"Enhanced FFT time: {enhanced_time:.4f} seconds")
    print(f"Performance overhead: {((enhanced_time - original_time) / original_time) * 100:.2f}%")
    
    # Verify magnitude difference
    original_magnitude = np.max(np.abs(fft_original))
    enhanced_magnitude = np.max(np.abs(fft_enhanced))
    ratio = enhanced_magnitude / original_magnitude
    
    print(f"Magnitude ratio (enhanced/original): {ratio:.2f}")
    print(f"Expected ratio (9.80665): 9.81")

def benchmark_memory_usage():
    """Benchmark memory usage improvements."""
    
    # Create large dataset
    n_rows = 1000000
    df = pd.DataFrame({
        'time': np.linspace(0, 1000, n_rows),
        'accel_x': np.random.normal(0, 0.01, n_rows),
        'accel_y': np.random.normal(0, 0.01, n_rows),
        'accel_z': np.random.normal(0, 0.01, n_rows),
        'temp': np.random.normal(20, 2, n_rows),
        'pressure': np.random.normal(14.7, 0.5, n_rows)
    })
    
    # Original memory usage
    original_memory = df.memory_usage(deep=True).sum() / (1024 * 1024)
    
    # Optimize memory
    from components.large_dataset_handler import LargeDatasetHandler
    handler = LargeDatasetHandler()
    optimized_df = handler.optimize_dataframe_memory(df)
    
    # Optimized memory usage
    optimized_memory = optimized_df.memory_usage(deep=True).sum() / (1024 * 1024)
    
    print(f"Original memory usage: {original_memory:.2f} MB")
    print(f"Optimized memory usage: {optimized_memory:.2f} MB")
    print(f"Memory savings: {original_memory - optimized_memory:.2f} MB ({((original_memory - optimized_memory) / original_memory) * 100:.1f}%)")

if __name__ == "__main__":
    print("=== Performance Benchmarks ===")
    
    print("\n1. FFT Performance Benchmark:")
    benchmark_fft_performance()
    
    print("\n2. Memory Usage Benchmark:")
    benchmark_memory_usage()