"""
Automatic URL Pattern Learning System
====================================

This module automatically learns and suggests new URL patterns based on successful
function discoveries. It uses machine learning techniques to identify patterns
in successful URLs and suggests new mappings.
"""

import re
import json
import time
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
import hashlib

# Import ML classifier
try:
    from ..ml import ml_classifier, HAS_ML
except ImportError:
    ml_classifier = None
    HAS_ML = False


@dataclass
class URLPattern:
    function_pattern: str
    url_path: str
    header: str
    confidence: float
    success_count: int
    failure_count: int
    last_seen: float
    examples: List[str]


class URLPatternLearner:
    """
    Learns URL patterns automatically from successful function discoveries
    """

    def __init__(self, cache_file: str = None):
        self.cache_file = cache_file or str(
            Path.home() / ".cache" / "manw-ng" / "url_patterns.json"
        )
        Path(self.cache_file).parent.mkdir(parents=True, exist_ok=True)

        # Storage for patterns
        self.learned_patterns: Dict[str, URLPattern] = {}
        self.function_successes: Dict[str, List[Dict]] = defaultdict(list)
        self.header_frequencies: Counter = Counter()
        self.dll_header_mappings: Dict[str, Counter] = defaultdict(Counter)

        # Load existing patterns
        self._load_patterns()

    def _load_patterns(self):
        """Load previously learned patterns from cache"""
        try:
            if Path(self.cache_file).exists():
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for pattern_id, pattern_data in data.get("patterns", {}).items():
                    self.learned_patterns[pattern_id] = URLPattern(**pattern_data)

                self.header_frequencies = Counter(data.get("header_frequencies", {}))

                # Convert nested dict structure
                for dll, header_counts in data.get("dll_header_mappings", {}).items():
                    self.dll_header_mappings[dll] = Counter(header_counts)

        except Exception as e:
            print(f"Warning: Could not load URL patterns cache: {e}")

    def _save_patterns(self):
        """Save learned patterns to cache"""
        try:
            data = {
                "patterns": {
                    pid: asdict(pattern)
                    for pid, pattern in self.learned_patterns.items()
                },
                "header_frequencies": dict(self.header_frequencies),
                "dll_header_mappings": {
                    dll: dict(counter)
                    for dll, counter in self.dll_header_mappings.items()
                },
                "last_updated": time.time(),
            }

            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Warning: Could not save URL patterns cache: {e}")

    def record_success(self, function_name: str, url: str, dll_name: str = None):
        """
        Record a successful function->URL mapping

        Args:
            function_name: Name of the Win32 function
            url: Successfully found URL
            dll_name: DLL containing the function (if known)
        """
        # Extract header from URL
        header = self._extract_header_from_url(url)
        if not header:
            return

        # Train ML classifier if available
        if HAS_ML and ml_classifier:
            try:
                ml_classifier.add_training_example(
                    function_name, header, dll_name, success=True
                )
            except Exception as e:
                pass  # Don't fail on ML errors

        # Record the success
        success_data = {
            "function_name": function_name,
            "url": url,
            "header": header,
            "dll_name": dll_name,
            "timestamp": time.time(),
        }

        self.function_successes[function_name].append(success_data)
        self.header_frequencies[header] += 1

        if dll_name:
            self.dll_header_mappings[dll_name][header] += 1

        # Learn pattern from this success
        self._learn_pattern_from_success(function_name, url, header, dll_name)

        # Save patterns periodically
        if len(self.function_successes) % 10 == 0:
            self._save_patterns()

    def _extract_header_from_url(self, url: str) -> Optional[str]:
        """Extract header name from Microsoft Learn URL"""
        # Pattern: /api/HEADER/nf-HEADER-function
        match = re.search(r"/api/([^/]+)/nf-[^/]+-", url)
        if match:
            return match.group(1)

        # Alternative pattern: /api/HEADER/
        match = re.search(r"/api/([^/]+)/", url)
        if match:
            return match.group(1)

        return None

    def _learn_pattern_from_success(
        self, function_name: str, url: str, header: str, dll_name: str = None
    ):
        """Learn a new pattern from a successful mapping"""
        # Generate function pattern
        function_pattern = self._generate_function_pattern(function_name)

        # Create pattern ID
        pattern_id = hashlib.md5(f"{function_pattern}:{header}".encode()).hexdigest()

        if pattern_id in self.learned_patterns:
            # Update existing pattern
            pattern = self.learned_patterns[pattern_id]
            pattern.success_count += 1
            pattern.last_seen = time.time()
            pattern.confidence = min(
                1.0,
                pattern.success_count
                / (pattern.success_count + pattern.failure_count + 1),
            )

            # Add example if not already present
            if function_name not in pattern.examples:
                pattern.examples.append(function_name)
                # Keep only last 10 examples
                pattern.examples = pattern.examples[-10:]
        else:
            # Create new pattern
            self.learned_patterns[pattern_id] = URLPattern(
                function_pattern=function_pattern,
                url_path=self._extract_url_path(url),
                header=header,
                confidence=0.8,  # Start with good confidence
                success_count=1,
                failure_count=0,
                last_seen=time.time(),
                examples=[function_name],
            )

    def _generate_function_pattern(self, function_name: str) -> str:
        """Generate a regex pattern for similar function names"""
        name_lower = function_name.lower()

        # Remove common suffixes and prefixes to create pattern
        base_patterns = []

        # Handle A/W suffixes
        if name_lower.endswith("a") or name_lower.endswith("w"):
            base_name = name_lower[:-1]
            base_patterns.append(f"^{re.escape(base_name)}[aw]?$")

        # Handle Ex suffixes
        if name_lower.endswith("ex"):
            base_name = name_lower[:-2]
            base_patterns.append(f"^{re.escape(base_name)}(ex)?$")

        # Handle numeric suffixes
        if re.search(r"\d+$", name_lower):
            base_name = re.sub(r"\d+$", "", name_lower)
            base_patterns.append(f"^{re.escape(base_name)}\\d*$")

        # Default: exact match
        base_patterns.append(f"^{re.escape(name_lower)}$")

        # Return most specific pattern
        return base_patterns[0] if base_patterns else f"^{re.escape(name_lower)}$"

    def _extract_url_path(self, url: str) -> str:
        """Extract the path pattern from URL"""
        # Extract path after domain
        match = re.search(r"\.com(/.+)", url)
        if match:
            return match.group(1)
        return url

    def record_failure(self, function_name: str, attempted_headers: List[str]):
        """Record failed attempts to help refine patterns"""
        for header in attempted_headers:
            function_pattern = self._generate_function_pattern(function_name)
            pattern_id = hashlib.md5(
                f"{function_pattern}:{header}".encode()
            ).hexdigest()

            if pattern_id in self.learned_patterns:
                pattern = self.learned_patterns[pattern_id]
                pattern.failure_count += 1
                pattern.confidence = pattern.success_count / (
                    pattern.success_count + pattern.failure_count + 1
                )

    def suggest_headers_for_function(
        self, function_name: str, dll_name: str = None
    ) -> List[Tuple[str, float]]:
        """
        Suggest likely headers for a function based on learned patterns + ML

        Returns:
            List of (header, confidence) tuples sorted by confidence
        """
        suggestions = []

        # ML predictions (highest priority)
        if HAS_ML and ml_classifier and ml_classifier.is_trained:
            try:
                ml_predictions = ml_classifier.predict_headers(
                    function_name, dll_name, top_k=5
                )
                for header, confidence in ml_predictions:
                    suggestions.append(
                        (header, confidence * 1.2)
                    )  # Boost ML confidence
            except Exception:
                pass  # Don't fail on ML errors
        function_lower = function_name.lower()

        # Check learned patterns
        for pattern in self.learned_patterns.values():
            if re.match(pattern.function_pattern, function_lower):
                suggestions.append((pattern.header, pattern.confidence))

        # Use DLL->header mappings if available
        if dll_name and dll_name in self.dll_header_mappings:
            dll_mappings = self.dll_header_mappings[dll_name]
            total = sum(dll_mappings.values())

            for header, count in dll_mappings.most_common(5):
                confidence = count / total
                suggestions.append(
                    (header, confidence * 0.8)
                )  # Slightly lower confidence

        # Add popular headers as fallback
        total_freq = sum(self.header_frequencies.values())
        if total_freq > 0:
            for header, freq in self.header_frequencies.most_common(3):
                confidence = (freq / total_freq) * 0.3  # Low confidence fallback
                suggestions.append((header, confidence))

        # Remove duplicates and sort by confidence
        unique_suggestions = {}
        for header, confidence in suggestions:
            if (
                header not in unique_suggestions
                or unique_suggestions[header] < confidence
            ):
                unique_suggestions[header] = confidence

        return sorted(unique_suggestions.items(), key=lambda x: x[1], reverse=True)

    def get_pattern_suggestions(self, min_confidence: float = 0.6) -> List[Dict]:
        """Get high-confidence patterns that could be added to the URL generator"""
        suggestions = []

        for pattern in self.learned_patterns.values():
            if pattern.confidence >= min_confidence and pattern.success_count >= 2:
                suggestions.append(
                    {
                        "function_pattern": pattern.function_pattern,
                        "header": pattern.header,
                        "confidence": pattern.confidence,
                        "success_count": pattern.success_count,
                        "examples": pattern.examples,
                    }
                )

        return sorted(suggestions, key=lambda x: x["confidence"], reverse=True)

    def cleanup_old_patterns(self, max_age_days: int = 30):
        """Remove old patterns that haven't been seen recently"""
        cutoff_time = time.time() - (max_age_days * 24 * 3600)

        to_remove = []
        for pattern_id, pattern in self.learned_patterns.items():
            if pattern.last_seen < cutoff_time and pattern.success_count < 2:
                to_remove.append(pattern_id)

        for pattern_id in to_remove:
            del self.learned_patterns[pattern_id]

        if to_remove:
            self._save_patterns()

    def get_statistics(self) -> Dict:
        """Get statistics about learned patterns and ML models"""
        total_patterns = len(self.learned_patterns)
        high_confidence = len(
            [p for p in self.learned_patterns.values() if p.confidence >= 0.8]
        )
        total_successes = sum(p.success_count for p in self.learned_patterns.values())

        stats = {
            "total_patterns": total_patterns,
            "high_confidence_patterns": high_confidence,
            "total_recorded_successes": total_successes,
            "unique_headers": len(self.header_frequencies),
            "top_headers": dict(self.header_frequencies.most_common(10)),
            "dll_mappings": len(self.dll_header_mappings),
            "has_ml": HAS_ML,
        }

        # Add ML statistics if available
        if HAS_ML and ml_classifier:
            stats["ml_stats"] = ml_classifier.get_model_stats()

        return stats


# Global instance for easy access
pattern_learner = URLPatternLearner()
