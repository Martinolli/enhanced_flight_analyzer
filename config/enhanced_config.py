# File: config/enhanced_config.py
"""
Configuration settings for enhanced features.
"""

class EnhancedConfig:
    """Configuration for enhanced flight data analyzer features."""
    
    # FFT Unit Conversion Settings
    FFT_UNIT_CONVERSION = {
        'enabled': True,
        'show_conversion_info': True,
        'conversion_precision': 6
    }
    
    # Statistical Analysis Settings
    STATISTICS = {
        'default_outlier_method': 'iqr',
        'default_outlier_threshold': 1.5,
        'correlation_methods': ['pearson', 'spearman', 'kendall'],
        'max_parameters_for_pca': 20
    }
    
    # Large Dataset Handling Settings
    LARGE_DATASET = {
        'memory_limit_mb': 500,
        'default_chunk_size': 10000,
        'default_sample_rate': 0.1,
        'enable_memory_optimization': True,
        'show_progress_bars': True
    }
    
    # Performance Settings
    PERFORMANCE = {
        'enable_caching': True,
        'cache_ttl_seconds': 3600,
        'parallel_processing': True,
        'max_workers': 4
    }