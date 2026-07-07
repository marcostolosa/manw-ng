"""
Function classification for Win32 API header/URL prediction.

The classifier is a pure-Python heuristic model backed by a curated
function->header mapping; it has no third-party ML dependencies.
"""

from .enhanced_classifier import enhanced_ml_classifier, EnhancedFunctionClassifier

# Primary classifier used across the codebase.
primary_classifier = enhanced_ml_classifier
HAS_ENHANCED = enhanced_ml_classifier is not None

__all__ = [
    "enhanced_ml_classifier",
    "EnhancedFunctionClassifier",
    "primary_classifier",
    "HAS_ENHANCED",
]
