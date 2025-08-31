"""
URLTran_BERT Implementation for Win32 Function Header Prediction
================================================================

Implementation of URLTran_BERT based on 2024 research for URL pattern extraction
optimized for Microsoft Learn documentation discovery.
"""

import re
import json
import time
import numpy as np
from typing import Dict, List, Tuple, Optional, Set
from pathlib import Path
from collections import defaultdict, Counter
from dataclasses import dataclass
import hashlib

# Try to import transformers with fallbacks
try:
    from transformers import AutoTokenizer, AutoModel
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from sklearn.metrics.pairwise import cosine_similarity

    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

# Fallback to existing ML
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.ensemble import RandomForestClassifier

    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


@dataclass
class URLTranFeatures:
    """Enhanced features for URLTran_BERT model"""

    function_name: str
    url_tokens: List[str]
    char_features: List[str]  # Character-level features
    semantic_category: str
    dll_hint: Optional[str] = None
    confidence: float = 0.0


class CharBERTEncoder:
    """Character-aware BERT encoder for URL patterns"""

    def __init__(self, model_name: str = "microsoft/codebert-base"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.is_loaded = False

        if HAS_TRANSFORMERS:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModel.from_pretrained(model_name)
                self.is_loaded = True
            except Exception as e:
                print(f"Warning: Could not load {model_name}: {e}")
                self.is_loaded = False

    def encode_function_name(self, function_name: str) -> np.ndarray:
        """Encode function name with character-level awareness"""
        if not self.is_loaded:
            return np.zeros(768)  # Default BERT embedding size

        try:
            # Prepare input with character-level tokenization
            char_tokens = list(function_name.lower())
            word_tokens = self._segment_camel_case(function_name)

            # Combine tokens
            combined_input = " ".join(word_tokens) + " [SEP] " + " ".join(char_tokens)

            # Tokenize and encode
            inputs = self.tokenizer(
                combined_input,
                return_tensors="pt",
                max_length=128,
                truncation=True,
                padding=True,
            )

            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use CLS token embedding
                embedding = outputs.last_hidden_state[:, 0, :].numpy()

            return embedding.flatten()

        except Exception as e:
            print(f"Warning: BERT encoding failed: {e}")
            return np.zeros(768)

    def _segment_camel_case(self, function_name: str) -> List[str]:
        """Segment CamelCase function names"""
        words = re.findall(r"[A-Z][a-z]*|[a-z]+|\d+", function_name)
        return [word.lower() for word in words if len(word) > 1]


class URLTranBERT:
    """
    URLTran_BERT: Advanced transformer-based model for Win32 function header prediction
    """

    def __init__(self, model_dir: str = None):
        self.model_dir = Path(
            model_dir or Path.home() / ".cache" / "manw-ng" / "urltran_models"
        )
        self.model_dir.mkdir(parents=True, exist_ok=True)

        # Initialize encoders
        self.char_bert = CharBERTEncoder() if HAS_TRANSFORMERS else None

        # Traditional ML fallback
        self.tfidf_vectorizer = None
        self.rf_classifier = None
        self.is_trained = False

        # Training data
        self.training_data = []
        self.header_embeddings = {}

        # Load existing models
        self._load_models()

        # URL pattern learning
        self.url_patterns = self._initialize_url_patterns()

    def _initialize_url_patterns(self) -> Dict[str, str]:
        """Initialize Microsoft Learn URL patterns"""
        return {
            "fileapi": "https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-{function}",
            "winuser": "https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-{function}",
            "wingdi": "https://learn.microsoft.com/en-us/windows/win32/api/wingdi/nf-wingdi-{function}",
            "processthreadsapi": "https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-{function}",
            "winreg": "https://learn.microsoft.com/en-us/windows/win32/api/winreg/nf-winreg-{function}",
            "memoryapi": "https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-{function}",
            "wininet": "https://learn.microsoft.com/en-us/windows/win32/api/wininet/nf-wininet-{function}",
            "synchapi": "https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-{function}",
            "winternl": "https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-{function}",
            "wincrypt": "https://learn.microsoft.com/en-us/windows/win32/api/wincrypt/nf-wincrypt-{function}",
        }

    def extract_features(
        self, function_name: str, dll_hint: str = None
    ) -> URLTranFeatures:
        """Extract enhanced features for URLTran_BERT"""

        # Generate potential URLs
        url_tokens = []
        for header, pattern in self.url_patterns.items():
            url = pattern.format(function=function_name.lower())
            url_tokens.extend(url.split("/")[3:])  # Remove domain parts

        # Character-level features
        char_features = list(function_name.lower())

        # Semantic categorization
        semantic_category = self._classify_semantic_category(function_name)

        return URLTranFeatures(
            function_name=function_name,
            url_tokens=url_tokens,
            char_features=char_features,
            semantic_category=semantic_category,
            dll_hint=dll_hint,
        )

    def _classify_semantic_category(self, function_name: str) -> str:
        """Classify function into semantic category"""
        name_lower = function_name.lower()

        # Enhanced semantic categories
        categories = {
            "file_io": [
                "create",
                "open",
                "read",
                "write",
                "delete",
                "copy",
                "move",
                "file",
            ],
            "memory": ["alloc", "free", "virtual", "heap", "memory", "map"],
            "process": ["process", "thread", "create", "open", "terminate"],
            "registry": ["reg", "key", "value", "enum", "query", "set"],
            "network": ["socket", "connect", "send", "recv", "internet", "http"],
            "window": ["window", "create", "show", "hide", "find", "text"],
            "graphics": ["draw", "paint", "dc", "gdi", "bitmap", "brush"],
            "security": ["crypt", "security", "token", "privilege"],
        }

        for category, keywords in categories.items():
            if any(keyword in name_lower for keyword in keywords):
                return category

        return "general"

    def add_training_example(
        self,
        function_name: str,
        header: str,
        dll_name: str = None,
        success: bool = True,
    ):
        """Add training example with BERT encoding"""
        if not success:
            return

        features = self.extract_features(function_name, dll_name)

        # Get BERT embedding if available
        bert_embedding = None
        if self.char_bert and self.char_bert.is_loaded:
            bert_embedding = self.char_bert.encode_function_name(function_name)

        self.training_data.append(
            {
                "function_name": function_name,
                "header": header,
                "dll_name": dll_name,
                "features": features,
                "bert_embedding": bert_embedding,
                "timestamp": time.time(),
            }
        )

        # Store header embeddings for similarity matching
        if bert_embedding is not None:
            if header not in self.header_embeddings:
                self.header_embeddings[header] = []
            self.header_embeddings[header].append(bert_embedding)

        # Retrain periodically
        if len(self.training_data) % 25 == 0:
            self._train_models()

    def predict_headers(
        self, function_name: str, dll_name: str = None, top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Predict headers using URLTran_BERT approach"""
        predictions = []

        # BERT-based predictions (primary)
        if self.char_bert and self.char_bert.is_loaded and self.header_embeddings:
            bert_preds = self._bert_similarity_predict(function_name)
            predictions.extend([(h, c * 1.0) for h, c in bert_preds[:3]])

        # Traditional ML fallback
        if self.is_trained and self.tfidf_vectorizer and self.rf_classifier:
            ml_preds = self._traditional_ml_predict(function_name, dll_name)
            predictions.extend([(h, c * 0.8) for h, c in ml_preds[:3]])

        # Pattern-based predictions
        pattern_preds = self._pattern_based_predict(function_name)
        predictions.extend([(h, c * 0.6) for h, c in pattern_preds[:2]])

        # Remove duplicates and sort
        unique_predictions = {}
        for header, confidence in predictions:
            if (
                header not in unique_predictions
                or unique_predictions[header] < confidence
            ):
                unique_predictions[header] = confidence

        return sorted(unique_predictions.items(), key=lambda x: x[1], reverse=True)[
            :top_k
        ]

    def _bert_similarity_predict(self, function_name: str) -> List[Tuple[str, float]]:
        """BERT-based similarity prediction"""
        if not self.char_bert or not self.char_bert.is_loaded:
            return []

        try:
            # Get function embedding
            func_embedding = self.char_bert.encode_function_name(function_name)

            similarities = []
            for header, embeddings in self.header_embeddings.items():
                if embeddings:
                    # Average embeddings for this header
                    avg_embedding = np.mean(embeddings, axis=0)

                    # Calculate cosine similarity
                    similarity = cosine_similarity(
                        func_embedding.reshape(1, -1), avg_embedding.reshape(1, -1)
                    )[0][0]

                    similarities.append((header, similarity))

            return sorted(similarities, key=lambda x: x[1], reverse=True)

        except Exception as e:
            print(f"Warning: BERT similarity prediction failed: {e}")
            return []

    def _traditional_ml_predict(
        self, function_name: str, dll_name: str = None
    ) -> List[Tuple[str, float]]:
        """Traditional ML prediction as fallback"""
        if not self.is_trained:
            return []

        try:
            features = self.extract_features(function_name, dll_name)

            # Prepare text features
            text = " ".join(
                [
                    features.function_name,
                    features.semantic_category,
                    " ".join(features.url_tokens[:5]),  # Limit URL tokens
                    features.dll_hint or "",
                ]
            )

            X = self.tfidf_vectorizer.transform([text])
            probabilities = self.rf_classifier.predict_proba(X)[0]
            classes = self.rf_classifier.classes_

            predictions = []
            for i, prob in enumerate(probabilities):
                if prob > 0.01:
                    predictions.append((classes[i], prob))

            return sorted(predictions, key=lambda x: x[1], reverse=True)

        except Exception as e:
            print(f"Warning: Traditional ML prediction failed: {e}")
            return []

    def _pattern_based_predict(self, function_name: str) -> List[Tuple[str, float]]:
        """Pattern-based prediction using function name analysis"""
        name_lower = function_name.lower()
        predictions = []

        # Direct pattern matching
        if "file" in name_lower or "create" in name_lower:
            predictions.append(("fileapi", 0.7))
        if "window" in name_lower or "text" in name_lower:
            predictions.append(("winuser", 0.6))
        if "reg" in name_lower:
            predictions.append(("winreg", 0.8))
        if "alloc" in name_lower or "virtual" in name_lower:
            predictions.append(("memoryapi", 0.7))

        return predictions

    def _train_models(self):
        """Train traditional ML models"""
        if not HAS_SKLEARN or len(self.training_data) < 5:
            return

        try:
            # Prepare training data
            texts = []
            labels = []

            for example in self.training_data[-200:]:  # Use recent data
                features = example["features"]
                text = " ".join(
                    [
                        features.function_name,
                        features.semantic_category,
                        " ".join(features.url_tokens[:5]),
                        features.dll_hint or "",
                    ]
                )
                texts.append(text)
                labels.append(example["header"])

            # Train TF-IDF
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=500, ngram_range=(1, 2), lowercase=True
            )
            X = self.tfidf_vectorizer.fit_transform(texts)

            # Train Random Forest
            self.rf_classifier = RandomForestClassifier(
                n_estimators=30, max_depth=8, random_state=42
            )
            self.rf_classifier.fit(X.toarray(), labels)

            self.is_trained = True
            self._save_models()

        except Exception as e:
            print(f"Warning: URLTran_BERT model training failed: {e}")

    def _save_models(self):
        """Save trained models"""
        # Implementation for saving models
        pass

    def _load_models(self):
        """Load existing models"""
        # Implementation for loading models
        pass

    def get_model_stats(self) -> Dict:
        """Get model statistics"""
        return {
            "has_transformers": HAS_TRANSFORMERS,
            "has_sklearn": HAS_SKLEARN,
            "bert_loaded": self.char_bert.is_loaded if self.char_bert else False,
            "is_trained": self.is_trained,
            "training_examples": len(self.training_data),
            "header_embeddings": len(self.header_embeddings),
            "model_type": "URLTran_BERT",
        }


# Global instance
urltran_bert = URLTranBERT() if HAS_TRANSFORMERS or HAS_SKLEARN else None
