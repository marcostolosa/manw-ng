"""
Machine Learning module for Win32 API function classification and URL prediction
"""

try:
    from .function_classifier import ml_classifier, Win32FunctionClassifier

    HAS_ML = True
except ImportError:
    ml_classifier = None
    Win32FunctionClassifier = None
    HAS_ML = False

__all__ = ["ml_classifier", "Win32FunctionClassifier", "HAS_ML"]
