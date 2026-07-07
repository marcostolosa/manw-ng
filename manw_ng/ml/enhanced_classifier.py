"""
Enhanced ML Classifier - Final Integration
==========================================

Enhanced classifier integrating a comprehensive WinAPI database with
intelligent header mapping and URL pattern discovery.
"""

from typing import Dict, List, Tuple
from pathlib import Path

from ..utils.assets import load_json_asset

# Header -> list-of-functions mapping. Extracted from a ~2,800-line inline dict
# into a packaged JSON asset to keep this module small; behaviour is identical.
COMPREHENSIVE_HEADER_MAPPING = load_json_asset("header_mapping.json")


class EnhancedFunctionClassifier:
    """
    Enhanced classifier with comprehensive WinAPI database integration
    """

    def __init__(self, model_dir: str = None):
        self.model_dir = Path(
            model_dir or Path.home() / ".cache" / "manw-ng" / "enhanced_ml"
        )
        self.model_dir.mkdir(parents=True, exist_ok=True)

        # Build reverse lookup mapping
        self.function_to_header = self._build_function_mapping()

        # URL patterns discovered from testing (expanded)
        self.url_patterns = {
            "standard": "https://learn.microsoft.com/en-us/windows/win32/api/{header}/nf-{header}-{function}",
            "native": "https://learn.microsoft.com/en-us/windows/win32/api/winternl/nf-winternl-{function}",
            "driver": "https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/{header}/nf-{header}-{function}",
            "legacy": "https://learn.microsoft.com/en-us/windows/desktop/api/{header}/nf-{header}-{function}",
            "struct": "https://learn.microsoft.com/en-us/windows/win32/api/{header}/ns-{header}-{function}",
            "shell": "https://learn.microsoft.com/en-us/windows/win32/shell/{header}/nf-{header}-{function}",
            "multimedia": "https://learn.microsoft.com/en-us/windows/win32/multimedia/{header}/nf-{header}-{function}",
            "opengl": "https://learn.microsoft.com/en-us/windows/win32/opengl/{header}/nf-{header}-{function}",
            "directshow": "https://learn.microsoft.com/en-us/windows/win32/directshow/{header}/nf-{header}-{function}",
        }

        self.is_ready = True

    def _build_function_mapping(self) -> Dict[str, str]:
        """Build function name to header mapping (load from complete database)"""
        mapping = {}

        # First, add from comprehensive header mapping (for samples/display)
        for header, functions in COMPREHENSIVE_HEADER_MAPPING.items():
            for func in functions:
                # Add all variants
                mapping[func.lower()] = header
                mapping[func] = header

                # Add A/W variants
                mapping[f"{func.lower()}a"] = header
                mapping[f"{func.lower()}w"] = header
                mapping[f"{func}A"] = header
                mapping[f"{func}W"] = header

                # Add Ex variants
                mapping[f"{func.lower()}ex"] = header
                mapping[f"{func}Ex"] = header

        # Then, load the complete mapping asset (all 61k+ function->header entries).
        try:
            mapping.update(load_json_asset("complete_function_mapping.json"))
        except FileNotFoundError:
            # The optional bulk mapping asset is absent; the base mapping above
            # is still fully functional.
            pass

        return mapping

    def predict_headers(
        self, function_name: str, dll_name: str = None, top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """Predict headers with high accuracy using comprehensive mapping"""
        predictions = {}

        func_lower = function_name.lower()

        # 1. Direct lookup (95% confidence)
        if func_lower in self.function_to_header:
            header = self.function_to_header[func_lower]
            predictions[header] = 0.95

        # 2. A/W variant lookup (90% confidence)
        if func_lower.endswith(("a", "w")):
            base_func = func_lower[:-1]
            if base_func in self.function_to_header:
                header = self.function_to_header[base_func]
                predictions[header] = predictions.get(header, 0) + 0.90

        # 3. Ex variant lookup (85% confidence)
        if func_lower.endswith("ex"):
            base_func = func_lower[:-2]
            if base_func in self.function_to_header:
                header = self.function_to_header[base_func]
                predictions[header] = predictions.get(header, 0) + 0.85

        # 4. Pattern-based prediction (60-80% confidence)
        if not predictions:
            # Native functions
            if function_name.startswith(("Nt", "Zw")):
                predictions["winternl"] = 0.80
                predictions["ntddk"] = 0.70  # Alternative for driver context
            elif function_name.startswith(("Rtl", "Ldr")):
                predictions["winternl"] = 0.75

            # Common patterns
            elif any(pattern in func_lower for pattern in ["reg", "registry"]):
                predictions["winreg"] = 0.80
            elif any(
                pattern in func_lower
                for pattern in [
                    "file",
                    "create",
                    "open",
                    "read",
                    "write",
                    "delete",
                    "copy",
                    "move",
                ]
            ):
                predictions["fileapi"] = 0.70
            elif any(
                pattern in func_lower
                for pattern in ["window", "message", "dc", "text", "button"]
            ):
                predictions["winuser"] = 0.70
            elif any(pattern in func_lower for pattern in ["process", "thread"]):
                predictions["processthreadsapi"] = 0.70
            elif any(
                pattern in func_lower
                for pattern in ["virtual", "alloc", "free", "memory", "heap"]
            ):
                predictions["memoryapi"] = 0.65
            elif any(
                pattern in func_lower
                for pattern in ["mutex", "event", "semaphore", "wait", "sleep"]
            ):
                predictions["synchapi"] = 0.65
            elif any(
                pattern in func_lower
                for pattern in ["draw", "text", "bitmap", "brush", "pen", "pixel"]
            ):
                predictions["wingdi"] = 0.65
            elif any(
                pattern in func_lower
                for pattern in ["socket", "bind", "listen", "connect", "send", "recv"]
            ):
                predictions["winsock2"] = 0.75
            elif any(pattern in func_lower for pattern in ["internet", "http", "url"]):
                predictions["wininet"] = 0.75
            elif any(
                pattern in func_lower
                for pattern in ["crypt", "hash", "encrypt", "decrypt", "sign"]
            ):
                predictions["wincrypt"] = 0.75
            else:
                predictions["winbase"] = 0.40  # Default fallback

        # 5. DLL-based hints (if available)
        if dll_name:
            dll_lower = dll_name.lower()
            dll_bonus = 0.10

            if "user32" in dll_lower:
                predictions["winuser"] = predictions.get("winuser", 0) + dll_bonus
            elif "gdi32" in dll_lower:
                predictions["wingdi"] = predictions.get("wingdi", 0) + dll_bonus
            elif "kernel32" in dll_lower:
                predictions["winbase"] = predictions.get("winbase", 0) + dll_bonus
            elif "advapi32" in dll_lower:
                predictions["winreg"] = predictions.get("winreg", 0) + dll_bonus
            elif "ws2_32" in dll_lower:
                predictions["winsock2"] = predictions.get("winsock2", 0) + dll_bonus
            elif "wininet" in dll_lower:
                predictions["wininet"] = predictions.get("wininet", 0) + dll_bonus
            elif "ntdll" in dll_lower:
                predictions["winternl"] = predictions.get("winternl", 0) + dll_bonus

        # Sort by confidence and return top results
        sorted_predictions = sorted(
            predictions.items(), key=lambda x: x[1], reverse=True
        )
        return sorted_predictions[:top_k]

    def generate_url(
        self, function_name: str, header: str, url_type: str = "function"
    ) -> str:
        """Generate Microsoft Learn URL for function or structure"""
        func_lower = function_name.lower()

        # Choose pattern based on URL type and header type
        if url_type == "struct":
            pattern = self.url_patterns["struct"]
        elif header in ["winternl"]:
            pattern = self.url_patterns["native"]
        elif header in ["ntddk", "wdm"]:
            pattern = self.url_patterns["driver"]
        elif header in ["shlobj"]:
            pattern = self.url_patterns["shell"]
        elif header in ["mmsystem", "vfw", "mfapi"]:
            pattern = self.url_patterns["multimedia"]
        elif header in ["gl"]:
            pattern = self.url_patterns["opengl"]
        else:
            pattern = self.url_patterns["standard"]

        return pattern.format(header=header, function=func_lower)

    def get_model_stats(self) -> Dict:
        """Get model statistics"""
        return {
            "model_type": "EnhancedComprehensiveClassifier",
            "is_ready": self.is_ready,
            "mapped_headers": len(COMPREHENSIVE_HEADER_MAPPING),
            "mapped_functions": len(self.function_to_header),
            "url_patterns": len(self.url_patterns),
            "has_comprehensive_mapping": True,
        }


# Global enhanced classifier instance
enhanced_ml_classifier = EnhancedFunctionClassifier()
