# File: utils/error_handling.py
"""
Enhanced error handling and logging for the flight data analyzer.
"""

import logging
import traceback
import streamlit as st
from typing import Any, Callable, Optional
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('flight_analyzer.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def handle_errors(operation_name: str, show_error: bool = True):
    """
    Decorator for handling errors in operations.
    
    Args:
        operation_name: Name of the operation for logging
        show_error: Whether to show error in Streamlit UI
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = f"Error in {operation_name}: {str(e)}"
                logger.error(f"{error_msg}\n{traceback.format_exc()}")
                
                if show_error:
                    st.error(f"❌ {error_msg}")
                
                return None
        return wrapper
    return decorator

@handle_errors("FFT Analysis")
def safe_fft_analysis(df, config):
    """Safely perform FFT analysis with error handling."""
    # Implementation here
    pass

@handle_errors("Statistical Analysis")
def safe_statistical_analysis(df, parameters):
    """Safely perform statistical analysis with error handling."""
    # Implementation here
    pass