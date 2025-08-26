"""
Machine Learning Function Classifier for Win32 API URL Prediction
================================================================

Uses NLP and classification algorithms to predict the most likely header/URL
for a Win32 function based on naming patterns, semantic analysis, and
historical success data.
"""

import re
import json
import time
import pickle
import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from pathlib import Path
from collections import defaultdict, Counter
from dataclasses import dataclass
import hashlib

# Try to import ML libraries with fallbacks
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report

    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    import nltk
    from nltk.stem import PorterStemmer
    from nltk.corpus import stopwords

    HAS_NLTK = True
except ImportError:
    HAS_NLTK = False


@dataclass
class FunctionFeatures:
    """Features extracted from a Win32 function name"""

    name: str
    prefix: str
    suffix: str
    length: int
    has_numbers: bool
    word_count: int
    stems: List[str]
    semantic_category: str
    dll_hint: Optional[str] = None


class Win32FunctionClassifier:
    """
    Advanced ML classifier that learns to predict headers for Win32 functions
    """

    def __init__(self, model_dir: str = None):
        self.model_dir = Path(
            model_dir or Path.home() / ".cache" / "manw-ng" / "ml_models"
        )
        self.model_dir.mkdir(parents=True, exist_ok=True)

        # Initialize stemmer if available
        self.stemmer = PorterStemmer() if HAS_NLTK else None

        # ML Models
        self.tfidf_vectorizer = None
        self.nb_classifier = None
        self.rf_classifier = None
        self.is_trained = False

        # Feature extraction
        self.semantic_keywords = self._build_semantic_keywords()
        self.training_data = []

        # Load existing models
        self._load_models()

    def _build_semantic_keywords(self) -> Dict[str, Set[str]]:
        """Build semantic keyword categories for function classification"""
        return {
            "file_io": {
                "create",
                "open",
                "read",
                "write",
                "delete",
                "copy",
                "move",
                "find",
                "search",
                "file",
                "directory",
                "folder",
                "path",
            },
            "memory": {
                "alloc",
                "free",
                "virtual",
                "heap",
                "memory",
                "map",
                "unmap",
                "protect",
                "query",
                "commit",
                "reserve",
                "global",
                "local",
            },
            "process_thread": {
                "process",
                "thread",
                "create",
                "open",
                "terminate",
                "suspend",
                "resume",
                "wait",
                "exit",
                "duplicate",
                "token",
                "handle",
            },
            "registry": {
                "reg",
                "key",
                "value",
                "enum",
                "query",
                "set",
                "delete",
                "close",
                "registry",
                "hkey",
            },
            "network": {
                "socket",
                "connect",
                "send",
                "recv",
                "bind",
                "listen",
                "accept",
                "internet",
                "http",
                "url",
                "wsa",
                "net",
            },
            "ui_graphics": {
                "window",
                "create",
                "show",
                "hide",
                "find",
                "enum",
                "message",
                "draw",
                "text",
                "paint",
                "dc",
                "gdi",
                "bitmap",
                "brush",
            },
            "security": {
                "crypt",
                "security",
                "token",
                "privilege",
                "acl",
                "sid",
                "impersonate",
                "logon",
                "auth",
                "certificate",
                "hash",
            },
            "service": {
                "service",
                "scm",
                "manager",
                "start",
                "stop",
                "control",
                "query",
                "enum",
                "config",
            },
        }

    def extract_features(
        self, function_name: str, dll_hint: str = None
    ) -> FunctionFeatures:
        """Extract comprehensive features from a function name"""
        name_lower = function_name.lower()

        # Basic features
        prefix = self._extract_prefix(name_lower)
        suffix = self._extract_suffix(name_lower)
        length = len(function_name)
        has_numbers = bool(re.search(r"\d", function_name))

        # Word segmentation (CamelCase/PascalCase)
        words = self._segment_function_name(function_name)
        word_count = len(words)

        # Stemming if available
        stems = []
        if self.stemmer:
            stems = [self.stemmer.stem(word.lower()) for word in words]
        else:
            stems = [word.lower() for word in words]

        # Semantic category
        semantic_category = self._classify_semantic_category(name_lower, words)

        return FunctionFeatures(
            name=function_name,
            prefix=prefix,
            suffix=suffix,
            length=length,
            has_numbers=has_numbers,
            word_count=word_count,
            stems=stems,
            semantic_category=semantic_category,
            dll_hint=dll_hint,
        )

    def _extract_prefix(self, name_lower: str) -> str:
        """Extract common Win32 prefixes"""
        prefixes = [
            "create",
            "open",
            "get",
            "set",
            "enum",
            "query",
            "reg",
            "nt",
            "zw",
            "rtl",
        ]
        for prefix in prefixes:
            if name_lower.startswith(prefix):
                return prefix
        return name_lower[:3] if len(name_lower) >= 3 else name_lower

    def _extract_suffix(self, name_lower: str) -> str:
        """Extract common Win32 suffixes"""
        suffixes = ["a", "w", "ex", "exw", "exa"]
        for suffix in suffixes:
            if name_lower.endswith(suffix):
                return suffix
        return ""

    def _segment_function_name(self, function_name: str) -> List[str]:
        """Segment CamelCase/PascalCase function names into words"""
        # Split on capital letters and numbers
        words = re.findall(r"[A-Z][a-z]*|[a-z]+|\d+", function_name)
        return [word for word in words if len(word) > 1]

    def _classify_semantic_category(self, name_lower: str, words: List[str]) -> str:
        """Classify function into semantic category based on keywords"""
        all_text = name_lower + " " + " ".join(word.lower() for word in words)

        category_scores = {}
        for category, keywords in self.semantic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in all_text)
            if score > 0:
                category_scores[category] = score

        if category_scores:
            return max(category_scores, key=category_scores.get)
        return "unknown"

    def add_training_example(
        self,
        function_name: str,
        header: str,
        dll_name: str = None,
        success: bool = True,
    ):
        """Add a training example to the dataset"""
        if not success:
            return  # Only train on successful mappings

        features = self.extract_features(function_name, dll_name)
        self.training_data.append(
            {
                "function_name": function_name,
                "header": header,
                "dll_name": dll_name,
                "features": features,
                "timestamp": time.time(),
            }
        )

        # Retrain periodically
        if len(self.training_data) % 50 == 0 and len(self.training_data) > 100:
            self._train_models()

    def _prepare_training_data(self) -> Tuple[List[str], List[str]]:
        """Prepare training data for ML models"""
        if not self.training_data:
            return [], []

        # Create text features for TF-IDF
        text_features = []
        labels = []

        for example in self.training_data:
            features = example["features"]

            # Combine various features into text
            text = " ".join(
                [
                    features.name,
                    features.prefix,
                    features.suffix,
                    features.semantic_category,
                    " ".join(features.stems),
                    features.dll_hint or "",
                ]
            )

            text_features.append(text)
            labels.append(example["header"])

        return text_features, labels

    def _train_models(self):
        """Train ML models on accumulated data"""
        if not HAS_SKLEARN or len(self.training_data) < 10:
            return

        try:
            text_features, labels = self._prepare_training_data()
            if not text_features:
                return

            # Prepare TF-IDF features
            if not self.tfidf_vectorizer:
                self.tfidf_vectorizer = TfidfVectorizer(
                    max_features=1000,
                    ngram_range=(1, 2),
                    lowercase=True,
                    stop_words="english" if HAS_NLTK else None,
                )

            X = self.tfidf_vectorizer.fit_transform(text_features)
            y = labels

            # Split data if we have enough examples
            if len(labels) > 50:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42, stratify=y
                )
            else:
                X_train, X_test, y_train, y_test = X, X, y, y

            # Train Naive Bayes
            self.nb_classifier = MultinomialNB(alpha=0.1)
            self.nb_classifier.fit(X_train, y_train)

            # Train Random Forest
            self.rf_classifier = RandomForestClassifier(
                n_estimators=50, max_depth=10, random_state=42
            )
            self.rf_classifier.fit(X_train.toarray(), y_train)

            # Calculate accuracy
            if len(set(y_test)) > 1:  # Only if we have multiple classes
                nb_score = accuracy_score(y_test, self.nb_classifier.predict(X_test))
                rf_score = accuracy_score(
                    y_test, self.rf_classifier.predict(X_test.toarray())
                )
                print(f"ML Model Performance - NB: {nb_score:.3f}, RF: {rf_score:.3f}")

            self.is_trained = True
            self._save_models()

        except Exception as e:
            print(f"Warning: ML model training failed: {e}")

    def predict_headers(
        self, function_name: str, dll_name: str = None, top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Predict most likely headers using ML models"""
        if not self.is_trained or not HAS_SKLEARN:
            return []

        try:
            features = self.extract_features(function_name, dll_name)

            # Prepare text for prediction
            text = " ".join(
                [
                    features.name,
                    features.prefix,
                    features.suffix,
                    features.semantic_category,
                    " ".join(features.stems),
                    features.dll_hint or "",
                ]
            )

            predictions = []

            # Naive Bayes predictions
            if self.nb_classifier and self.tfidf_vectorizer:
                X = self.tfidf_vectorizer.transform([text])
                nb_probs = self.nb_classifier.predict_proba(X)[0]
                nb_classes = self.nb_classifier.classes_

                for class_idx, prob in enumerate(nb_probs):
                    if prob > 0.01:  # Filter low probability predictions
                        predictions.append(
                            (nb_classes[class_idx], prob * 0.6)
                        )  # Weight NB less

            # Random Forest predictions
            if self.rf_classifier:
                X = self.tfidf_vectorizer.transform([text])
                rf_probs = self.rf_classifier.predict_proba(X.toarray())[0]
                rf_classes = self.rf_classifier.classes_

                for class_idx, prob in enumerate(rf_probs):
                    if prob > 0.01:
                        header = rf_classes[class_idx]
                        # Combine with NB prediction if available
                        existing = next(
                            (p for p in predictions if p[0] == header), None
                        )
                        if existing:
                            # Ensemble: average the probabilities
                            combined_prob = (existing[1] + prob * 0.8) / 2
                            predictions = [
                                (h, p) if h != header else (h, combined_prob)
                                for h, p in predictions
                            ]
                        else:
                            predictions.append((header, prob * 0.8))

            # Sort by confidence and return top_k
            predictions.sort(key=lambda x: x[1], reverse=True)
            return predictions[:top_k]

        except Exception as e:
            print(f"Warning: ML prediction failed: {e}")
            return []

    def _save_models(self):
        """Save trained models to disk"""
        if not self.is_trained:
            return

        try:
            # Save models
            if self.tfidf_vectorizer:
                with open(self.model_dir / "tfidf_vectorizer.pkl", "wb") as f:
                    pickle.dump(self.tfidf_vectorizer, f)

            if self.nb_classifier:
                with open(self.model_dir / "nb_classifier.pkl", "wb") as f:
                    pickle.dump(self.nb_classifier, f)

            if self.rf_classifier:
                with open(self.model_dir / "rf_classifier.pkl", "wb") as f:
                    pickle.dump(self.rf_classifier, f)

            # Save training data
            with open(self.model_dir / "training_data.json", "w") as f:
                # Convert to serializable format
                serializable_data = []
                for example in self.training_data[-1000:]:  # Keep only recent data
                    features = example["features"]
                    serializable_data.append(
                        {
                            "function_name": example["function_name"],
                            "header": example["header"],
                            "dll_name": example["dll_name"],
                            "timestamp": example["timestamp"],
                        }
                    )
                json.dump(serializable_data, f, indent=2)

        except Exception as e:
            print(f"Warning: Could not save ML models: {e}")

    def _load_models(self):
        """Load trained models from disk"""
        try:
            # Load models
            tfidf_path = self.model_dir / "tfidf_vectorizer.pkl"
            nb_path = self.model_dir / "nb_classifier.pkl"
            rf_path = self.model_dir / "rf_classifier.pkl"
            data_path = self.model_dir / "training_data.json"

            if tfidf_path.exists() and HAS_SKLEARN:
                with open(tfidf_path, "rb") as f:
                    self.tfidf_vectorizer = pickle.load(f)

            if nb_path.exists() and HAS_SKLEARN:
                with open(nb_path, "rb") as f:
                    self.nb_classifier = pickle.load(f)

            if rf_path.exists() and HAS_SKLEARN:
                with open(rf_path, "rb") as f:
                    self.rf_classifier = pickle.load(f)

            if data_path.exists():
                with open(data_path, "r") as f:
                    stored_data = json.load(f)
                    for item in stored_data:
                        # Reconstruct features for loaded data
                        features = self.extract_features(
                            item["function_name"], item.get("dll_name")
                        )
                        self.training_data.append(
                            {
                                "function_name": item["function_name"],
                                "header": item["header"],
                                "dll_name": item.get("dll_name"),
                                "features": features,
                                "timestamp": item["timestamp"],
                            }
                        )

            if self.tfidf_vectorizer and (self.nb_classifier or self.rf_classifier):
                self.is_trained = True
                # Silent loading - no print message to avoid delays

        except Exception as e:
            print(f"Warning: Could not load ML models: {e}")

    def get_model_stats(self) -> Dict:
        """Get statistics about the ML models"""
        return {
            "has_sklearn": HAS_SKLEARN,
            "has_nltk": HAS_NLTK,
            "is_trained": self.is_trained,
            "training_examples": len(self.training_data),
            "has_nb_classifier": self.nb_classifier is not None,
            "has_rf_classifier": self.rf_classifier is not None,
            "has_tfidf": self.tfidf_vectorizer is not None,
        }


# Global ML classifier instance
ml_classifier = Win32FunctionClassifier() if HAS_SKLEARN else None
