"""
Parser module for MANW-NG

Extracts function information from Microsoft documentation pages.
"""

import re
from typing import Dict, List, Tuple, Optional
from bs4 import BeautifulSoup


class Win32PageParser:
    """
    Parser for Microsoft Win32 API documentation pages
    """

    def parse_function_page(self, soup: BeautifulSoup, url: str) -> Dict:
        """
        Parse Microsoft documentation page and extract function information
        """
        function_info = {
            "url": url,
            "name": "",
            "dll": "",
            "calling_convention": "__stdcall",
            "parameters": [],
            "parameter_count": 0,
            "architectures": ["x86", "x64"],
            "signature": "",
            "return_type": "",
            "return_description": "",
            "description": "",
        }

        # Extract all information
        function_info["name"] = self._extract_function_name(soup)
        function_info["dll"] = self._extract_dll(soup)
        function_info["signature"] = self._extract_signature(soup)
        function_info["parameters"] = self._extract_parameters(soup)
        function_info["parameter_count"] = len(function_info["parameters"])
        function_info["return_type"], function_info["return_description"] = (
            self._extract_return_info(soup)
        )
        function_info["architectures"] = self._extract_architectures(soup)
        function_info["description"] = self._extract_description(soup)

        return function_info

    def _extract_function_name(self, soup: BeautifulSoup) -> str:
        """Extract function name from page"""
        title = soup.find("h1")
        if title:
            title_text = title.get_text().strip()
            title_text = re.sub(
                r"\s+(function|api|Function|API).*$",
                "",
                title_text,
                flags=re.IGNORECASE,
            )
            if title_text:
                return title_text

        # Fallback: extract from code signature
        code_blocks = soup.find_all(["pre", "code"])
        for block in code_blocks:
            text = block.get_text()
            match = re.search(r"\b(\w+)\s*\(", text)
            if match and not match.group(1).upper() in ["IF", "FOR", "WHILE", "SWITCH"]:
                return match.group(1)

        return "FunçãoDesconhecida"

    def _extract_dll(self, soup: BeautifulSoup) -> str:
        """Extract DLL name"""
        dll_patterns = [r"(\w+\.dll)", r"Library:\s*(\w+\.dll)", r"DLL:\s*(\w+\.dll)"]
        text = soup.get_text()

        for pattern in dll_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return "kernel32.dll"

    def _extract_signature(self, soup: BeautifulSoup) -> str:
        """Extract function signature"""
        # Look for div with class='has-inner-focus'
        focus_div = soup.find("div", class_="has-inner-focus")
        if focus_div:
            signature = focus_div.get_text().strip()
            if signature and "(" in signature and ")" in signature:
                return signature

        # Fallback: look for Syntax section
        syntax_headers = soup.find_all(
            ["h2", "h3", "h4"],
            string=re.compile(r"Syntax|Sintaxe|syntax|sintaxe", re.IGNORECASE),
        )

        for header in syntax_headers:
            next_elem = header.find_next()
            while next_elem:
                if next_elem.name in ["pre", "code"]:
                    signature = next_elem.get_text().strip()
                    if "(" in signature and ")" in signature:
                        return signature
                elif next_elem.name == "div" and "has-inner-focus" in next_elem.get(
                    "class", []
                ):
                    signature = next_elem.get_text().strip()
                    if "(" in signature and ")" in signature:
                        return signature
                next_elem = next_elem.find_next_sibling()
                if next_elem and next_elem.name in ["h1", "h2", "h3", "h4"]:
                    break

        return ""

    def _extract_parameters(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract detailed parameter information"""
        parameters = []

        # Look for Parameters section
        param_headers = soup.find_all(
            ["h2", "h3", "h4"],
            string=re.compile(r"Parameters|Parâmetros|parameters", re.IGNORECASE),
        )

        for header in param_headers:
            next_elem = header.find_next_sibling()
            current_param = {}

            while next_elem:
                if next_elem.name in ["h1", "h2", "h3", "h4"]:
                    break

                # New format: <p><code>[in] paramName</code></p>
                if next_elem.name == "p":
                    code_elem = next_elem.find("code")
                    if code_elem:
                        # Save previous parameter if exists
                        if current_param.get("name"):
                            parameters.append(current_param)

                        param_text = code_elem.get_text().strip()
                        # Extract parameter name, removing brackets
                        param_match = re.search(r"(\w+)$", param_text)
                        if param_match:
                            param_name = param_match.group(1)
                            # Extract type from signature if available
                            param_type = self._extract_param_type_from_signature(
                                soup, param_name
                            )
                            current_param = {
                                "name": param_name,
                                "type": param_type,
                                "description": "",
                            }
                    elif current_param.get("name") and next_elem.get_text().strip():
                        # This paragraph contains the description
                        desc_text = next_elem.get_text().strip()
                        # Skip short texts or ones that look like parameter declarations
                        if len(desc_text) > 20 and not re.match(r"^\[.*?\]", desc_text):
                            # Limit to first 2 sentences or ~200 chars
                            sentences = desc_text.split(". ")
                            if len(sentences) >= 2:
                                desc_text = ". ".join(sentences[:2]) + "."
                            elif len(desc_text) > 200:
                                desc_text = desc_text[:200] + "..."
                            current_param["description"] = desc_text

                # Legacy format: <dt><dd>
                elif next_elem.name == "dt":
                    if current_param.get("name"):
                        parameters.append(current_param)

                    param_name = next_elem.get_text().strip()
                    param_name = re.sub(r"^\[.*?\]\s*", "", param_name)
                    current_param = {
                        "name": param_name,
                        "type": self._extract_type_from_text(param_name),
                        "description": "",
                    }

                elif next_elem.name == "dd" and current_param.get("name"):
                    current_param["description"] = next_elem.get_text().strip()

                next_elem = next_elem.find_next_sibling()

            if current_param.get("name"):
                parameters.append(current_param)

            if parameters:
                break

        return parameters

    def _extract_param_type_from_signature(
        self, soup: BeautifulSoup, param_name: str
    ) -> str:
        """Extract parameter type from function signature"""
        signature = self._extract_signature(soup)
        if signature and param_name:
            # Look for pattern: TYPE paramName
            pattern = rf"\s+(\w+)\s+{re.escape(param_name)}\b"
            match = re.search(pattern, signature)
            if match:
                return match.group(1)
        return self._extract_type_from_text(param_name)

    def _extract_type_from_text(self, text: str) -> str:
        """Extract Win32 data type from text"""
        win32_types = [
            "BOOL",
            "DWORD",
            "HANDLE",
            "HWND",
            "LPCSTR",
            "LPCWSTR",
            "LPSTR",
            "LPWSTR",
            "LPVOID",
            "PVOID",
            "UINT",
            "INT",
            "LONG",
            "ULONG",
            "BYTE",
            "WORD",
            "SIZE_T",
            "HMODULE",
        ]

        text_upper = text.upper()
        for win_type in win32_types:
            if win_type in text_upper:
                return win_type

        return "UNKNOWN"

    def _extract_return_info(self, soup: BeautifulSoup) -> Tuple[str, str]:
        """Extract return type and description"""
        return_type = "BOOL"
        return_desc = ""

        # Look for Return value section
        return_headers = soup.find_all(
            ["h2", "h3", "h4"],
            string=re.compile(
                r"Return\s+value|Valor\s+de\s+retorno|Retornar\s+valor|Valor\s+retornado|return\s+value",
                re.IGNORECASE,
            ),
        )

        for header in return_headers:
            content_parts = []
            next_elem = header.find_next_sibling()
            paragraph_count = 0

            while next_elem and paragraph_count < 2:
                if next_elem.name in ["h1", "h2", "h3", "h4"]:
                    break

                if next_elem.name in ["p"]:
                    text = next_elem.get_text().strip()
                    if text and 10 < len(text) < 500:
                        content_parts.append(text)
                        paragraph_count += 1

                next_elem = next_elem.find_next_sibling()

            if content_parts:
                return_desc = " ".join(content_parts)
                break

        # Extract return type from signature
        signature = self._extract_signature(soup)
        if signature:
            match = re.search(
                r"^\s*(?:\w+\s+)*(\w+)\s+\w+\s*\(", signature, re.MULTILINE
            )
            if match:
                potential_type = match.group(1).upper()
                if potential_type in [
                    "BOOL",
                    "DWORD",
                    "HANDLE",
                    "HWND",
                    "INT",
                    "UINT",
                    "LONG",
                    "ULONG",
                    "VOID",
                    "LPVOID",
                    "HMODULE",
                ]:
                    return_type = potential_type

        return return_type, return_desc

    def _extract_architectures(self, soup: BeautifulSoup) -> List[str]:
        """Extract supported architectures"""
        text = soup.get_text().lower()
        architectures = []

        if "x64" in text or "64-bit" in text:
            architectures.append("x64")
        if "x86" in text or "32-bit" in text or "desktop" in text:
            architectures.append("x86")

        return architectures if architectures else ["x86", "x64"]

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract function description"""
        title = soup.find("h1")
        if title:
            next_p = title.find_next("p")
            if next_p:
                return next_p.get_text().strip()
        return ""
