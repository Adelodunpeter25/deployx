"""
Centralized logging configuration for DeployX.

This module provides a unified logging system for the entire application,
supporting both console and file output with configurable verbosity levels.
It ensures consistent log formatting and proper log level management across
all components.

Features:
    - Console and file logging support
    - Configurable verbosity levels
    - Structured log formatting
    - Singleton logger pattern to avoid duplicate handlers
"""
import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logging(verbose: bool = False, log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup centralized logging configuration for DeployX.
    
    Configures the root logger with appropriate handlers and formatters.
    Prevents duplicate handler creation by checking existing handlers.
    
    Args:
        verbose: Enable DEBUG level logging if True, INFO level if False
        log_file: Optional path to log file for persistent logging
        
    Returns:
        Configured logger instance for the application
    """
    logger = logging.getLogger('deployx')
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    level = logging.DEBUG if verbose else logging.INFO
    logger.setLevel(level)
    
    # Create consistent formatter for all handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler for real-time output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Optional file handler for persistent logging
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always debug level for files
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str = 'deployx') -> logging.Logger:
    """
    Get a logger instance for the specified module.
    
    Creates a child logger under the main 'deployx' logger hierarchy.
    This allows for fine-grained logging control per module while
    maintaining consistent configuration.
    
    Args:
        name: Logger name, typically __name__ from calling module
        
    Returns:
        Logger instance configured for the specified module
    """
    return logging.getLogger(name)
