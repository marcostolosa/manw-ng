"""
Machine Learning module for Win32 API function classification and URL prediction
"""

# Import enhanced classifier (always available)
try:
    from .enhanced_classifier import enhanced_ml_classifier, EnhancedFunctionClassifier

    HAS_ENHANCED = True
except ImportError:
    enhanced_ml_classifier = None
    EnhancedFunctionClassifier = None
    HAS_ENHANCED = False

# Import original classifier (requires sklearn)
try:
    from .function_classifier import ml_classifier, Win32FunctionClassifier

    HAS_ML = True
except ImportError:
    ml_classifier = None
    Win32FunctionClassifier = None
    HAS_ML = False

# Use enhanced classifier as primary
primary_classifier = enhanced_ml_classifier if HAS_ENHANCED else ml_classifier
fallback_classifier = ml_classifier

__all__ = [
    "ml_classifier",
    "Win32FunctionClassifier",
    "enhanced_ml_classifier",
    "EnhancedFunctionClassifier",
    "primary_classifier",
    "fallback_classifier",
    "HAS_ML",
    "HAS_ENHANCED",
]
