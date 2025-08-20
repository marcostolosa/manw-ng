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
            "signature_language": "c",
            "return_type": "",
            "return_description": "",
            "description": "",
        }

        # Extract all information
        function_info["name"] = self._extract_function_name(soup)
        function_info["dll"] = self._extract_dll(soup)
        signature_info = self._extract_signature_with_language(soup)
        function_info["signature"] = signature_info["signature"]
        function_info["signature_language"] = signature_info["language"]
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

    def _extract_signature_with_language(self, soup: BeautifulSoup) -> Dict:
        """Extract function signature with language detection"""
        # Look for div with class='has-inner-focus'
        focus_div = soup.find("div", class_="has-inner-focus")
        if focus_div:
            signature = focus_div.get_text().strip()
            if signature and "(" in signature and ")" in signature:
                return self._format_signature_with_language(signature, focus_div)

        # Look for Syntax section
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
                        return self._format_signature_with_language(
                            signature, next_elem
                        )
                elif next_elem.name == "div":
                    # Check for code blocks within divs
                    code_elem = next_elem.find(["pre", "code"])
                    if code_elem:
                        signature = code_elem.get_text().strip()
                        if "(" in signature and ")" in signature:
                            return self._format_signature_with_language(
                                signature, code_elem
                            )
                    # Check for has-inner-focus class
                    elif "has-inner-focus" in next_elem.get("class", []):
                        signature = next_elem.get_text().strip()
                        if "(" in signature and ")" in signature:
                            return self._format_signature_with_language(
                                signature, next_elem
                            )

                next_elem = next_elem.find_next_sibling()
                if next_elem and next_elem.name in ["h1", "h2", "h3", "h4"]:
                    break

        return {"signature": "", "language": "c"}

    def _format_signature_with_language(self, signature: str, element) -> Dict:
        """Format signature with proper language detection"""
        # Detect language from element attributes
        language = self._detect_code_language(element)

        # Clean and format the signature
        cleaned_signature = self._clean_signature(signature)

        return {"signature": cleaned_signature, "language": language}

    def _extract_signature(self, soup: BeautifulSoup) -> str:
        """Legacy method for backward compatibility"""
        result = self._extract_signature_with_language(soup)
        return result["signature"]

    def _detect_code_language(self, element) -> str:
        """Detect programming language from code element"""
        # Check for language classes
        classes = element.get("class", [])
        for cls in classes:
            if "lang-" in cls:
                return cls.replace("lang-", "")
            if "language-" in cls:
                return cls.replace("language-", "")
            if cls in [
                "cpp",
                "c",
                "csharp",
                "javascript",
                "python",
                "powershell",
                "bash",
            ]:
                return cls

        # Check parent elements for language indicators
        parent = element.parent
        while parent:
            parent_classes = parent.get("class", [])
            for cls in parent_classes:
                if "lang-" in cls:
                    return cls.replace("lang-", "")
                if "language-" in cls:
                    return cls.replace("language-", "")
            parent = parent.parent

        # Check for data attributes
        lang_attr = element.get("data-lang") or element.get("data-language")
        if lang_attr:
            return lang_attr

        # Detect by content patterns
        content = element.get_text().strip()
        if self._looks_like_cpp(content):
            return "cpp"
        elif self._looks_like_csharp(content):
            return "csharp"
        elif self._looks_like_powershell(content):
            return "powershell"
        elif self._looks_like_javascript(content):
            return "javascript"

        # Default fallback for Win32 API
        return "c"

    def _looks_like_cpp(self, content: str) -> bool:
        """Check if content looks like C/C++ code"""
        cpp_patterns = [
            r"\b(BOOL|DWORD|HANDLE|HWND|LPCSTR|LPCWSTR|LPVOID|NTSTATUS)\b",
            r"\[in\]|\[out\]|\[in,\s*out\]|\[optional\]",
            r"__\w+\s+\w+\s*\(",  # __stdcall, __cdecl, etc.
        ]
        return any(re.search(pattern, content) for pattern in cpp_patterns)

    def _looks_like_csharp(self, content: str) -> bool:
        """Check if content looks like C# code"""
        csharp_patterns = [
            r"\busing\s+System\b",
            r"\bpublic\s+static\s+extern\b",
            r"\[DllImport\(",
            r"\bstring\b.*\w+\s*\(",
        ]
        return any(re.search(pattern, content) for pattern in csharp_patterns)

    def _looks_like_powershell(self, content: str) -> bool:
        """Check if content looks like PowerShell code"""
        ps_patterns = [
            r"^\s*\$\w+",
            r"\bGet-\w+|\bSet-\w+|\bNew-\w+",
            r"-\w+\s+",  # PowerShell parameters
        ]
        return any(re.search(pattern, content, re.MULTILINE) for pattern in ps_patterns)

    def _looks_like_javascript(self, content: str) -> bool:
        """Check if content looks like JavaScript code"""
        js_patterns = [
            r"\bfunction\s+\w+\s*\(",
            r"\bvar\s+\w+\s*=",
            r"\blet\s+\w+\s*=",
            r"\bconst\s+\w+\s*=",
        ]
        return any(re.search(pattern, content) for pattern in js_patterns)

    def _clean_signature(self, signature: str) -> str:
        """Clean and format function signature while preserving indentation"""
        # Split into lines and remove empty lines, but preserve original indentation
        lines = [line for line in signature.split("\n") if line.strip()]

        if not lines:
            return signature

        # Find the minimum indentation (ignoring the first line which might be function name)
        indentations = []
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped and i > 0:  # Skip first line for indentation calculation
                indent = len(line) - len(stripped)
                indentations.append(indent)

        # Calculate minimum indentation to preserve relative structure
        min_indent = min(indentations) if indentations else 0

        # Clean lines while preserving relative indentation
        cleaned_lines = []
        for i, line in enumerate(lines):
            if i == 0:
                # First line: just strip trailing whitespace
                cleaned_lines.append(line.rstrip())
            else:
                # Other lines: preserve indentation relative to minimum
                stripped = line.lstrip()
                if stripped:
                    current_indent = len(line) - len(stripped)
                    relative_indent = max(0, current_indent - min_indent)
                    cleaned_lines.append(" " * relative_indent + stripped)

        return "\n".join(cleaned_lines)

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
                        # This paragraph contains the description - only take first valid one
                        if not current_param[
                            "description"
                        ]:  # Only if we don't have description yet
                            desc_text = next_elem.get_text().strip()
                            # Skip short texts or ones that look like parameter declarations
                            if len(desc_text) > 20 and not re.match(
                                r"^\[.*?\]", desc_text
                            ):
                                current_param["description"] = desc_text

                                # Check for value tables within this description
                                value_tables = self._extract_parameter_value_tables(
                                    next_elem
                                )
                                if value_tables:
                                    current_param["values"] = value_tables

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

    def _extract_parameter_value_tables(self, element) -> List[Dict]:
        """Extract value/meaning tables for parameters"""
        value_tables = []

        # Look for tables within this element and its siblings, but stop at next parameter
        current = element
        while current:
            if current.name == "table":
                table_data = self._parse_value_table(current)
                if table_data:
                    value_tables.append(table_data)
            elif current.name in ["h1", "h2", "h3", "h4"]:
                # Stop at next major section
                break
            elif current.name == "p":
                # Check if this is the start of a new parameter
                code_elem = current.find("code")
                if code_elem:
                    param_text = code_elem.get_text().strip()
                    # If this looks like a parameter declaration, stop here
                    if re.search(r"\[.*?\]\s*\w+$", param_text):
                        break

            # Also check for tables in child elements
            tables = current.find_all("table") if hasattr(current, "find_all") else []
            for table in tables:
                table_data = self._parse_value_table(table)
                if table_data:
                    value_tables.append(table_data)

            current = current.find_next_sibling()
            if not current:
                break

        return value_tables

    def _parse_value_table(self, table) -> Dict:
        """Parse a value/meaning table"""
        # Check if this is a value table by looking at headers
        headers = table.find_all(["th", "td"])
        if not headers:
            return None

        header_texts = [h.get_text().strip().lower() for h in headers[:3]]

        # Look for common value table patterns
        value_patterns = ["value", "valor", "flag", "constant", "constante"]
        meaning_patterns = ["meaning", "significado", "description", "descrição"]

        has_value_col = any(
            pattern in " ".join(header_texts) for pattern in value_patterns
        )
        has_meaning_col = any(
            pattern in " ".join(header_texts) for pattern in meaning_patterns
        )

        if not (has_value_col and has_meaning_col):
            return None

        # Extract table data
        rows = table.find_all("tr")
        if len(rows) < 2:  # Need at least header + 1 data row
            return None

        # Get header indices
        header_row = rows[0]
        header_cells = header_row.find_all(["th", "td"])

        value_idx = -1
        meaning_idx = -1

        for i, cell in enumerate(header_cells):
            text = cell.get_text().strip().lower()
            if any(pattern in text for pattern in value_patterns) and value_idx == -1:
                value_idx = i
            elif (
                any(pattern in text for pattern in meaning_patterns)
                and meaning_idx == -1
            ):
                meaning_idx = i

        if value_idx == -1 or meaning_idx == -1:
            return None

        # Extract data rows
        table_data = {
            "type": "values",
            "title": self._get_table_title(table),
            "entries": [],
        }

        for row in rows[1:]:  # Skip header row
            cells = row.find_all(["td", "th"])
            if len(cells) > max(value_idx, meaning_idx):
                value = (
                    cells[value_idx].get_text().strip()
                    if value_idx < len(cells)
                    else ""
                )
                meaning = (
                    cells[meaning_idx].get_text().strip()
                    if meaning_idx < len(cells)
                    else ""
                )

                if value and meaning:
                    table_data["entries"].append({"value": value, "meaning": meaning})

        return table_data if table_data["entries"] else None

    def _get_table_title(self, table) -> str:
        """Get title for a table by looking at preceding elements"""
        # Look for preceding heading or caption
        prev_elem = table.find_previous(["h1", "h2", "h3", "h4", "h5", "h6", "caption"])
        if prev_elem and prev_elem.name == "caption":
            return prev_elem.get_text().strip()
        elif prev_elem and prev_elem.name.startswith("h"):
            # Check if heading is close to the table
            siblings_between = []
            current = prev_elem.find_next_sibling()
            while current and current != table:
                siblings_between.append(current)
                current = current.find_next_sibling()

            # If only a few elements between heading and table, use the heading
            if len(siblings_between) <= 3:
                return prev_elem.get_text().strip()

        return "Values"

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

            while next_elem:
                if next_elem.name in ["h1", "h2", "h3", "h4"]:
                    break

                if next_elem.name in ["p"]:
                    text = next_elem.get_text().strip()
                    if text and len(text) > 10:  # Removido limite de 500 caracteres
                        content_parts.append(text)

                # Também capturar listas e outros elementos com texto
                elif next_elem.name in ["ul", "ol", "div"]:
                    text = next_elem.get_text().strip()
                    if text and len(text) > 10:
                        content_parts.append(text)

                next_elem = next_elem.find_next_sibling()

            if content_parts:
                # Formatar cada parágrafo como item de lista markdown
                formatted_parts = [
                    f"- {part.strip()}" for part in content_parts if part.strip()
                ]
                return_desc = "\n".join(formatted_parts)
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
                    "NTSTATUS",  # Added for NT functions
                    "HINTERNET",  # Added for WinINet functions
                    "HRESULT",  # Added for COM functions
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
            description_parts = []
            current_elem = title.find_next_sibling()
            paragraph_count = 0
            max_paragraphs = 5  # Limit to avoid getting too much content

            while current_elem and paragraph_count < max_paragraphs:
                # Stop at the next section header (h2, h3, h4, etc.)
                if current_elem.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                    break

                # Collect paragraph text
                if current_elem.name == "p":
                    text = current_elem.get_text().strip()
                    if text and len(text) > 10:  # Skip very short paragraphs
                        # Skip paragraphs that look like navigation or metadata
                        if not any(
                            skip_word in text.lower()
                            for skip_word in [
                                "requirements",
                                "see also",
                                "library",
                                "dll",
                                "header",
                                "unicode",
                                "ansi",
                            ]
                        ):
                            description_parts.append(text)
                            paragraph_count += 1

                current_elem = current_elem.find_next_sibling()

            if description_parts:
                return " ".join(description_parts)

        # Alternative approach: look for content between h1 and first h2/h3
        if title:
            # Find the section containing the main description
            next_section = title.find_next(["h2", "h3", "h4"])
            if next_section:
                description_parts = []
                current = title.next_sibling
                while current and current != next_section:
                    if hasattr(current, "name") and current.name == "p":
                        text = current.get_text().strip()
                        if text and len(text) > 10:
                            description_parts.append(text)
                    current = current.next_sibling
                if description_parts:
                    return " ".join(
                        description_parts[:3]
                    )  # Limit to first 3 paragraphs

        # Final fallback: just get the first paragraph after h1
        if title:
            next_p = title.find_next("p")
            if next_p:
                return next_p.get_text().strip()
        return ""
