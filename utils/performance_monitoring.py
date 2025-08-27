# File: utils/performance_monitor.py
"""
Performance monitoring utilities.
"""

import time
import psutil
import streamlit as st
from contextlib import contextmanager
from typing import Dict, Any

class PerformanceMonitor:
    """Monitor performance metrics for the application."""
    
    def __init__(self):
        self.metrics = {}
    
    @contextmanager
    def measure_time(self, operation_name: str):
        """Context manager to measure execution time."""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            self.metrics[operation_name] = {
                'execution_time': end_time - start_time,
                'memory_used': end_memory - start_memory,
                'timestamp': time.time()
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        return self.metrics
    
    def display_metrics(self):
        """Display metrics in Streamlit UI."""
        if self.metrics:
            st.subheader("⚡ Performance Metrics")
            
            for operation, metrics in self.metrics.items():
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(f"{operation} - Time", f"{metrics['execution_time']:.3f}s")
                with col2:
                    st.metric(f"{operation} - Memory", f"{metrics['memory_used']:.1f}MB")

# Usage example
monitor = PerformanceMonitor()

with monitor.measure_time("FFT Analysis"):
    # Perform FFT analysis
    pass

monitor.display_metrics()