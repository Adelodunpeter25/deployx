# DeployX Docstring Style Guide

## Format: Google Style

All functions, classes, and modules should follow Google-style docstrings.

## Module Docstrings

```python
"""
Brief one-line description.

Longer description explaining the module's purpose,
key functionality, and usage patterns.

Example:
    Basic usage example here
"""
```

## Function Docstrings

```python
def function_name(param1: str, param2: int = 0) -> bool:
    """
    Brief one-line description of what function does.
    
    More detailed explanation if needed. Explain the purpose,
    behavior, and any important side effects.
    
    Args:
        param1: Description of param1
        param2: Description of param2 (default: 0)
    
    Returns:
        Description of return value
    
    Raises:
        ExceptionType: When and why this exception is raised
    
    Example:
        >>> function_name("test", 5)
        True
    """
```

## Class Docstrings

```python
class ClassName:
    """
    Brief one-line description.
    
    Detailed explanation of class purpose and usage.
    
    Attributes:
        attr1: Description of attribute
        attr2: Description of attribute
    
    Example:
        >>> obj = ClassName()
        >>> obj.method()
    """
```

## Private Function Docstrings

```python
def _private_function(param: str) -> None:
    """Brief description (can be one-line for simple private functions)."""
```

## Apply to All Files

Priority order:
1. Public API functions (commands/*)
2. Platform implementations (platforms/*)
3. Utility functions (utils/*)
4. Internal helpers
