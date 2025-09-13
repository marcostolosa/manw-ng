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

    def __init__(self):
        pass

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
            "remarks": "",
            "description": "",
            # Novos campos de metadata expandida
            "documentation_found": True,
            "documentation_online": True,
            "documentation_language": "en-us" if "en-us" in url else "pt-br",
            "symbol_type": "unknown",
            "fallback_used": False,
            "fallback_attempts": [],
            # Campos de classificação profissional
            "symbol_info": None,
            "kind": "unknown",
            "surface": "unknown",
            "header": "unknown",
        }

        # Extract all information
        function_info["name"] = self._extract_function_name(soup)

        # Fallback: if name extraction failed and we have empty HTML, use URL
        if function_info["name"] == "FunçãoDesconhecida" and len(soup.find_all()) == 0:
            function_info["name"] = self._extract_function_name_from_url(url)

        # Classificar o símbolo profissionalmente
        # Simple symbol classification without external classifier
        symbol_info = {
            "symbol": function_info["name"],
            "kind": "function",
            "surface": (
                "win32"
                if "/win32/" in url
                else "driver" if "/drivers/" in url else "unknown"
            ),
            "header": "unknown",
            "dll": None,
            "library": None,
            "api_set": None,
            "url_pattern": "nf-" if "/nf-" in url else "",
            "confidence": 0.95,
        }
        function_info["symbol_info"] = symbol_info
        function_info["kind"] = symbol_info["kind"]
        function_info["surface"] = symbol_info["surface"]
        function_info["header"] = symbol_info["header"]
        function_info["symbol_type"] = symbol_info["kind"]  # Backward compatibility

        # DLL baseada na classificação profissional
        function_info["dll"] = symbol_info["dll"] or self._extract_dll(soup)

        # Extrair assinatura/sintaxe para todos os tipos de símbolos
        signature_info = self._extract_signature_with_language(soup)
        function_info["signature"] = signature_info["signature"]
        function_info["signature_language"] = signature_info["language"]

        # Para estruturas, certificar que a definição C seja extraída
        if symbol_info["kind"] == "struct" and not function_info["signature"]:
            struct_definition = self._extract_struct_definition(soup)
            if struct_definition:
                function_info["signature"] = struct_definition
                function_info["signature_language"] = "c"

        # Extrair informações baseadas no tipo de símbolo
        if symbol_info["kind"] in ["function", "callback"]:
            function_info["parameters"] = self._extract_parameters(soup)
            function_info["parameter_count"] = len(function_info["parameters"])
            function_info["return_type"], function_info["return_description"] = (
                self._extract_return_info(soup)
            )
            function_info["remarks"] = self._extract_remarks(soup)
        elif symbol_info["kind"] == "struct":
            # Para estruturas, extrair membros ao invés de parâmetros
            function_info["members"] = self._extract_struct_members(soup)
            function_info["member_count"] = len(function_info.get("members", []))
            function_info["parameters"] = []  # Limpar parâmetros irrelevantes
            function_info["parameter_count"] = 0
            function_info["calling_convention"] = "N/A"  # Não aplicável a estruturas
            function_info["return_type"] = "N/A"
            # Extrair remarks/observações para structures também
            function_info["remarks"] = self._extract_remarks(soup)

        function_info["architectures"] = self._extract_architectures(soup)
        function_info["description"] = self._extract_complete_description(
            soup, symbol_info["kind"]
        )

        return function_info

    def _extract_function_name(self, soup: BeautifulSoup) -> str:
        """Extract function name from page"""
        title = soup.find("h1")

        # Also try other title elements
        if not title:
            title = soup.find("title")

        if title:
            title_text = title.get_text().strip()

            # Try to extract function name and header info from title
            # Example: "HeapAlloc function (heapapi.h)" -> "HeapAlloc (heapapi.h)"
            # Example: "Função CreateProcessW (processthreadsapi.h)" -> "CreateProcessW (processthreadsapi.h)"

            # Look for pattern: "FunctionName function (header.h)" or "Função FunctionName (header.h)"
            header_match = re.search(
                r"^(?:Função\s+)?(\w+)\s+(?:function|rotina)\s+\(([^)]+\.h)\)",
                title_text,
                re.IGNORECASE,
            )
            if header_match:
                func_name = header_match.group(1)
                header = header_match.group(2)
                return f"{func_name} ({header})"

            # Fallback: just remove "function" suffix
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

    def _extract_function_name_from_url(self, url: str) -> str:
        """Extract function name from URL as fallback when HTML is empty"""
        import re

        # Extract from URLs like: /nf-processenv-getcommandlinea
        # Use case-sensitive regex on original URL to preserve capitalization
        url_match = re.search(r"/nf-[^/]+-([^/]+?)/?$", url)
        if url_match:
            func_name = url_match.group(1)
            if func_name:
                # Convert first letter to uppercase to match Win32 convention
                return func_name[0].upper() + func_name[1:]
        return "FunçãoDesconhecida"

    def _extract_dll(self, soup: BeautifulSoup) -> str:
        """Extract DLL name - prioritize Requirements section"""

        # First, look for Requirements/Requisitos section
        requirements_headers = soup.find_all(
            ["h2", "h3", "h4", "strong", "b"],
            string=re.compile(r"Requirements?|Requisitos?", re.IGNORECASE)
        )

        for header in requirements_headers:
            # Get the next elements after Requirements header
            next_elem = header.find_next_sibling()
            while next_elem and next_elem.name not in ["h1", "h2", "h3", "h4"]:
                text = next_elem.get_text()
                # Look for Library/DLL specifically
                dll_match = re.search(r"(?:Library|DLL):\s*([A-Za-z0-9]+\.(?:dll|exe))", text, re.IGNORECASE)
                if dll_match:
                    return dll_match.group(1)
                next_elem = next_elem.find_next_sibling()

        # Fallback: look for any table that might contain requirements
        tables = soup.find_all("table")
        for table in tables:
            table_text = table.get_text()
            if re.search(r"(?:Library|DLL|Minimum)", table_text, re.IGNORECASE):
                dll_match = re.search(r"([A-Za-z0-9]+\.(?:dll|exe))", table_text, re.IGNORECASE)
                if dll_match:
                    return dll_match.group(1)

        # Final fallback: general DLL patterns in page
        dll_patterns = [r"Library:\s*([A-Za-z0-9]+\.(?:dll|exe))", r"DLL:\s*([A-Za-z0-9]+\.(?:dll|exe))", r"([A-Za-z0-9]+\.dll)"]
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

        # Special handling for function modifiers like DECLSPEC_ALLOCATOR
        # If first line contains only modifier keywords, merge with next line
        if len(lines) > 1:
            first_line = lines[0].strip()
            modifiers = [
                "DECLSPEC_ALLOCATOR",
                "WINAPI",
                "CALLBACK",
                "STDCALL",
                "CDECL",
                "__stdcall",
                "__cdecl",
            ]

            # Check if first line is just a modifier
            if (
                any(modifier in first_line for modifier in modifiers)
                and first_line.count("(") == 0
            ):
                # Merge first line with second line
                second_line = lines[1].strip()
                merged = f"{first_line} {second_line}"
                lines = [merged] + lines[2:]

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
        """Extract detailed parameter information with improved logic"""
        parameters = []

        # Look for Parameters section
        param_headers = soup.find_all(
            ["h2", "h3", "h4"],
            string=re.compile(r"Parameters|Parâmetros|parameters", re.IGNORECASE),
        )

        for header in param_headers:
            next_elem = header.find_next_sibling()
            current_param = {}
            collected_descriptions = []  # Store descriptions for current parameter
            header_level = int(
                header.name[1]
            )  # Get numeric level (h2 -> 2, h3 -> 3, etc.)

            while next_elem:
                # Only break on headers of same or higher level (h2 breaks h2/h1, h3 breaks h3/h2/h1)
                if next_elem.name and next_elem.name.startswith("h"):
                    current_header_level = int(next_elem.name[1])
                    if current_header_level <= header_level:
                        break
                    # For lower level headers (like h4, h5), continue processing
                    # These might be sub-sections within parameters

                # New format: <p><code>[in] paramName</code></p>
                if next_elem.name == "p":
                    code_elem = next_elem.find("code")
                    if code_elem:
                        # Save previous parameter if exists
                        if current_param.get("name"):
                            # Join all collected descriptions for the previous parameter
                            if collected_descriptions:
                                current_param["description"] = " ".join(
                                    collected_descriptions
                                )
                            parameters.append(current_param)
                            collected_descriptions = []  # Reset descriptions

                        param_text = code_elem.get_text().strip()

                        # Skip expressions like (lpAddress+dwSize) or mathematical expressions
                        if param_text.startswith("(") and param_text.endswith(")"):
                            continue
                        if "+" in param_text or "-" in param_text or "*" in param_text:
                            continue

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
                    elif current_param.get("name"):
                        # This paragraph contains description for current parameter
                        desc_text = next_elem.get_text().strip()
                        # Skip short texts or ones that look like parameter declarations
                        if len(desc_text) > 15 and not re.match(r"^\[.*?\]", desc_text):
                            # Don't look for code elements inside - this breaks the logic
                            # Just collect the text as description
                            collected_descriptions.append(desc_text)

                            # Extract tables for parameters that likely have them (only once per parameter)
                            if (
                                current_param.get("name")
                                and "values" not in current_param
                            ):
                                param_name = current_param["name"].lower()
                                # Common parameters that have value tables
                                complex_params = [
                                    "utype",
                                    "dwdesiredaccess",
                                    "desiredaccess",
                                    "dwsharemode",
                                    "shareaccess",
                                    "dwcreationdisposition",
                                    "createdisposition",
                                    "dwflagsandattributes",
                                    "dwcreationflags",
                                    "createoptions",
                                    "objectattributes",
                                    "fileattributes",
                                ]
                                if any(
                                    complex_param in param_name
                                    for complex_param in complex_params
                                ):
                                    value_tables = self._extract_parameter_value_tables(
                                        next_elem
                                    )
                                    if value_tables:
                                        current_param["values"] = value_tables

                # Legacy format: <dt><dd>
                elif next_elem.name == "dt":
                    if current_param.get("name"):
                        if collected_descriptions:
                            current_param["description"] = " ".join(
                                collected_descriptions
                            )
                        parameters.append(current_param)
                        collected_descriptions = []

                    param_name = next_elem.get_text().strip()
                    param_name = re.sub(r"^\[.*?\]\s*", "", param_name)
                    current_param = {
                        "name": param_name,
                        "type": self._extract_type_from_text(param_name),
                        "description": "",
                    }

                elif next_elem.name == "dd" and current_param.get("name"):
                    desc_text = next_elem.get_text().strip()
                    collected_descriptions.append(
                        self._clean_description_text(desc_text)
                    )

                next_elem = next_elem.find_next_sibling()

            # Don't forget the last parameter
            if current_param.get("name"):
                if collected_descriptions:
                    current_param["description"] = " ".join(collected_descriptions)
                parameters.append(current_param)

            if parameters:
                break

        return parameters

    def _extract_parameter_value_tables(self, element) -> List[Dict]:
        """Extract value/meaning tables for parameters - FIXED VERSION"""
        value_tables = []
        current = element.find_next_sibling()  # Start from next element after parameter

        while current:
            # FIRST: Check if we hit the next parameter (HIGHEST PRIORITY)
            if current.name == "p":
                code_elem = current.find("code")
                if code_elem:
                    param_text = code_elem.get_text().strip()
                    # Check if this is a parameter definition
                    if re.search(r"\[.*?\].*?[A-Za-z]", param_text):
                        # This is the next parameter - STOP immediately
                        break

            # SECOND: Check for return value section
            elif current.name in ["h1", "h2", "h3"]:
                section_text = current.get_text().strip().lower()
                if any(
                    keyword in section_text
                    for keyword in [
                        "return",
                        "valor de retorno",
                        "remarks",
                        "observações",
                    ]
                ):
                    break

            # THIRD: Extract tables and lists
            elif current.name == "table":
                table_data = self._parse_value_table(current)
                if table_data and not self._is_return_value_table(table_data):
                    value_tables.append(table_data)

            elif current.name in ["ul", "ol"]:
                list_data = self._parse_list_items(current)
                if list_data:
                    value_tables.append(list_data)

            # Move to next sibling
            current = current.find_next_sibling()

        return value_tables

    def _is_return_value_table(self, table_data: Dict) -> bool:
        """Check if a table contains return values (like IDOK, IDCANCEL, etc.)"""
        if not table_data or not table_data.get("entries"):
            return False

        # Check if entries contain return value patterns
        return_value_patterns = [
            "ID",
            "IDOK",
            "IDCANCEL",
            "IDABORT",
            "IDRETRY",
            "IDYES",
            "IDNO",
        ]

        for entry in table_data["entries"]:
            value = entry.get("value", "").upper()
            if any(pattern in value for pattern in return_value_patterns):
                return True

        return False

    def _parse_list_items(self, list_element) -> Dict:
        """Parse ul/ol list into table-like format"""
        try:
            list_items = list_element.find_all("li")
            if not list_items or len(list_items) < 2:
                return None

            entries = []
            for li in list_items:
                item_text = li.get_text().strip()
                if len(item_text) > 10:  # Only substantial items
                    # Try to split on colon or dash to get value/meaning
                    if ":" in item_text:
                        parts = item_text.split(":", 1)
                        if len(parts) == 2:
                            value = parts[0].strip()
                            meaning = parts[1].strip()
                        else:
                            value = ""
                            meaning = item_text
                    elif " - " in item_text:
                        parts = item_text.split(" - ", 1)
                        if len(parts) == 2:
                            value = parts[0].strip()
                            meaning = parts[1].strip()
                        else:
                            value = ""
                            meaning = item_text
                    else:
                        value = ""
                        meaning = item_text

                    if meaning:
                        entries.append({"value": value, "meaning": meaning})

            if entries:
                return {"title": "List Items", "entries": entries}
        except Exception:
            pass

        return None

    def _parse_value_table(self, table) -> Dict:
        """Parse a value/meaning table"""
        # Check if this is a value table by looking at headers
        headers = table.find_all(["th", "td"])
        if not headers:
            return None

        header_texts = [h.get_text().strip().lower() for h in headers[:3]]

        # Look for common value table patterns
        value_patterns = ["value", "valor", "flag", "constant", "constante", "code", "código", "status", "return"]
        meaning_patterns = ["meaning", "significado", "description", "descrição", "descrição"]

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
                value_cell = cells[value_idx] if value_idx < len(cells) else None
                meaning_cell = cells[meaning_idx] if meaning_idx < len(cells) else None

                if value_cell and meaning_cell:
                    # Extract value with better parsing for Microsoft docs structure
                    value = self._extract_table_value(value_cell)
                    meaning = self._clean_description_text(
                        meaning_cell.get_text().strip()
                    )

                    if value and meaning:
                        table_data["entries"].append(
                            {"value": value, "meaning": meaning}
                        )

        return table_data if table_data["entries"] else None

    def _get_table_title(self, table) -> str:
        """Get title for a table by looking at preceding elements and content"""
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
                title = prev_elem.get_text().strip()
                if title and len(title) < 100:
                    return title

        # Look for paragraph before table that might describe it
        prev_p = table.find_previous("p")
        if prev_p:
            p_text = prev_p.get_text().strip()
            # Look for descriptive phrases that indicate table category
            if "botões" in p_text.lower() or "buttons" in p_text.lower():
                return "Botões"
            elif "ícone" in p_text.lower() or "icon" in p_text.lower():
                return "Ícones"
            elif "padrão" in p_text.lower() or "default" in p_text.lower():
                return "Botão Padrão"
            elif "modal" in p_text.lower():
                return "Modalidade"
            elif "opções" in p_text.lower() or "options" in p_text.lower():
                return "Opções Adicionais"

        # Analyze table content to categorize
        rows = table.find_all("tr")
        if len(rows) > 1:
            # Get first few values to determine category
            first_values = []
            for row in rows[1:3]:  # Check first 2 data rows
                cells = row.find_all(["td", "th"])
                if cells:
                    value_text = cells[0].get_text().strip().upper()
                    first_values.append(value_text)
            
            # Categorize based on common patterns in Microsoft docs
            value_str = " ".join(first_values)
            if any(btn in value_str for btn in ["MB_OK", "MB_YESNO", "MB_CANCEL", "ABORT", "RETRY"]):
                return "Botões"
            elif any(icon in value_str for icon in ["MB_ICON", "INFORMATION", "WARNING", "ERROR", "QUESTION"]):
                return "Ícones"
            elif any(def_btn in value_str for def_btn in ["MB_DEFBUTTON", "DEFBUTTON"]):
                return "Botão Padrão"
            elif any(modal in value_str for modal in ["MB_APPLMODAL", "MB_SYSTEMMODAL", "MB_TASKMODAL"]):
                return "Modalidade"
            elif any(opt in value_str for opt in ["MB_TOPMOST", "MB_RIGHT", "MB_SETFOREGROUND"]):
                return "Opções Adicionais"

        return "Valores"

    def _extract_table_value(self, cell) -> str:
        """Extract constant value from Microsoft docs table cell structure"""
        # Microsoft docs often use this structure:
        # <dl><dt><b>CONSTANT_NAME</b></dt><dt>0x00000001L</dt></dl>
        # Or for return values: "IDABORT 3" or similar

        const_name = None
        numeric_value = None

        # Try to find the constant name in bold tags first
        bold_tags = cell.find_all(["b", "strong"])
        for bold in bold_tags:
            name = bold.get_text().strip()
            if name and re.match(r"^[A-Z_][A-Z0-9_]*$", name):
                const_name = name
                break

        # Look for hex values in dt elements first
        dt_elements = cell.find_all("dt")
        for dt in dt_elements:
            dt_text = dt.get_text().strip()
            if re.match(r"0x[0-9A-Fa-f]+L?$", dt_text):
                numeric_value = dt_text
                break
            # Also check for decimal numbers (return values)
            elif re.match(r"^\d+$", dt_text):
                numeric_value = dt_text
                break

        # If no value in dt, search the entire cell text
        if not numeric_value:
            cell_text = cell.get_text()
            # First try hex values
            hex_match = re.search(r"0x[0-9A-Fa-f]+L?", cell_text)
            if hex_match:
                numeric_value = hex_match.group()
            else:
                # Then try decimal numbers (for return values like IDABORT 3)
                decimal_match = re.search(r"\b(\d+)\b", cell_text)
                if decimal_match:
                    numeric_value = decimal_match.group(1)

        # If we found both constant name and numeric value, combine them
        if const_name and numeric_value:
            return f"{const_name} ({numeric_value})"
        elif const_name:
            return const_name

        # Fallback: try to extract any constant-looking text
        cell_text = cell.get_text().strip()
        lines = [line.strip() for line in cell_text.split("\n") if line.strip()]

        for line in lines:
            # Look for patterns like "IDABORT 3" or "MB_OK"
            const_match = re.match(r"^([A-Z_][A-Z0-9_]*)", line)
            if const_match:
                const_name = const_match.group(1)

                # Look for any numeric value in the same line or cell
                if re.search(r"\d", cell_text):
                    # Try hex first
                    hex_match = re.search(r"0x[0-9A-Fa-f]+L?", cell_text)
                    if hex_match:
                        return f"{const_name} ({hex_match.group()})"
                    # Then decimal
                    decimal_match = re.search(r"\b(\d+)\b", cell_text)
                    if decimal_match:
                        return f"{const_name} ({decimal_match.group(1)})"

                return const_name

        # Last resort: return the first non-empty line
        return lines[0] if lines else cell_text

    def _extract_param_type_from_signature(
        self, soup: BeautifulSoup, param_name: str
    ) -> str:
        """Extract parameter type from function signature"""
        signature = self._extract_signature(soup)
        if signature and param_name:
            # Match patterns like:
            # [in] const MSG *lpMsg
            # [out] LPCSTR lpszString
            # HANDLE hProcess
            # const RECT *lpRect
            # struct POINT *lpPoint
            pattern = rf"\[(?:in|out|in,\s*out|optional)\]\s+((?:const\s+)?(?:struct\s+)?(?:\w+\s+)*\w+)\s*\*?\s*{re.escape(param_name)}\b"

            match = re.search(pattern, signature, re.IGNORECASE | re.MULTILINE)
            if match:
                param_type = match.group(1).strip()
                # Check if there's a pointer indicator after the type
                # Look for * between the type and parameter name
                full_match = match.group(0)
                if "*" in full_match:
                    param_type += "*"
                return param_type

            # Fallback: Try pattern without [in/out] directives
            pattern = rf"((?:const\s+)?(?:struct\s+)?(?:\w+\s+)*\w+)\s*\*?\s*{re.escape(param_name)}\b"
            match = re.search(pattern, signature, re.IGNORECASE | re.MULTILINE)
            if match:
                param_type = match.group(1).strip()
                # Check if there's a pointer indicator
                full_match = match.group(0)
                if "*" in full_match:
                    param_type += "*"
                return param_type

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
            return_value_tables = []
            next_elem = header.find_next_sibling()

            while next_elem:
                if next_elem.name in ["h1", "h2", "h3", "h4"]:
                    break

                if next_elem.name in ["p"]:
                    text = next_elem.get_text().strip()
                    if text and len(text) > 10:  # Removido limite de 500 caracteres
                        content_parts.append(text)

                # Capture tables in return value section
                elif next_elem.name == "table":
                    table_data = self._parse_value_table(next_elem)
                    if table_data:
                        return_value_tables.append(table_data)

                # Também capturar listas e outros elementos com texto
                elif next_elem.name in ["ul", "ol", "div"]:
                    text = next_elem.get_text().strip()
                    if text and len(text) > 10:
                        content_parts.append(text)

                next_elem = next_elem.find_next_sibling()

            if content_parts or return_value_tables:
                # Formatar cada parágrafo como item de lista markdown
                formatted_parts = [
                    f"- {part.strip()}" for part in content_parts if part.strip()
                ]

                # Add tables to return description
                if return_value_tables:
                    formatted_parts.append("\n- Valores de retorno possíveis:")
                    for table in return_value_tables:
                        for entry in table.get("entries", []):
                            # Highlight constants in blue for Rich formatting
                            formatted_parts.append(
                                f"  - [bold blue]{entry['value']}[/bold blue]: {entry['meaning']}"
                            )

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

    def _extract_remarks(self, soup: BeautifulSoup) -> str:
        """Extract Remarks section from documentation"""
        remarks_content = ""

        # Look for Remarks section in multiple languages
        remarks_headers = soup.find_all(
            ["h2", "h3", "h4"],
            string=re.compile(
                r"Remarks|Observações|Comentários|remarks",
                re.IGNORECASE,
            ),
        )

        for header in remarks_headers:
            content_parts = []
            next_elem = header.find_next_sibling()

            while next_elem:
                if next_elem.name in ["h1", "h2", "h3", "h4"]:
                    break

                if next_elem.name in ["p"]:
                    text = next_elem.get_text().strip()
                    if text and len(text) > 10:
                        content_parts.append(text)

                # Also capture lists and other elements with text
                elif next_elem.name in ["ul", "ol", "div"]:
                    text = next_elem.get_text().strip()
                    if text and len(text) > 10:
                        content_parts.append(text)

                next_elem = next_elem.find_next_sibling()

            if content_parts:
                remarks_content = "\n\n".join(content_parts)
                break

        return remarks_content

    def _extract_architectures(self, soup: BeautifulSoup) -> List[str]:
        """Extract supported architectures"""
        text = soup.get_text().lower()
        architectures = []

        if "x64" in text or "64-bit" in text:
            architectures.append("x64")
        if "x86" in text or "32-bit" in text or "desktop" in text:
            architectures.append("x86")

        return architectures if architectures else ["x86", "x64"]

    def _extract_complete_description(
        self, soup: BeautifulSoup, symbol_kind: str
    ) -> str:
        """Extract COMPLETE description for any type of symbol"""
        title = soup.find("h1")
        if not title:
            return ""

        description_parts = []
        current_elem = title.find_next_sibling()

        # Para estruturas, buscar em mais seções incluindo comentários
        max_paragraphs = None if symbol_kind in ["struct", "enum", "interface"] else 10
        paragraph_count = 0
        found_comments_section = False

        while current_elem:
            # Para estruturas, procurar também seções de comentários/observações
            if current_elem.name in ["h1", "h2", "h3"]:
                header_text = current_elem.get_text().strip().lower()
                # Se é uma seção de comentários, observações, sintaxe ou notas, continuar
                if any(
                    section in header_text
                    for section in [
                        "comment",
                        "remark",
                        "note",
                        "observa",
                        "nota",
                        "comentário",
                        "sintaxe",
                        "syntax",
                    ]
                ):
                    found_comments_section = True
                    # Para seções de comentários, incluir o conteúdo todo
                    current_elem = current_elem.find_next_sibling()

                    # Coletar conteúdo da seção de comentários
                    while current_elem and current_elem.name not in ["h1", "h2", "h3"]:
                        if current_elem.name == "p":
                            text = current_elem.get_text().strip()
                            if text and len(text) > 10:
                                description_parts.append(text)
                                paragraph_count += 1
                        elif current_elem.name in ["pre", "code"]:
                            # Incluir também código de exemplo da seção comentários
                            code_text = current_elem.get_text().strip()
                            if code_text and "typedef" in code_text:
                                description_parts.append(
                                    f"Sintaxe para Windows 64-bit:\\n{code_text}"
                                )
                        current_elem = current_elem.find_next_sibling()
                    continue
                elif not found_comments_section or symbol_kind not in [
                    "struct",
                    "enum",
                ]:
                    break

            # Collect paragraph text
            if current_elem.name == "p":
                text = current_elem.get_text().strip()
                if text and len(text) > 5:  # Lowered threshold
                    # Skip navigation/metadata paragraphs but be less aggressive
                    if not any(
                        skip_word in text.lower()
                        for skip_word in [
                            "requirements",
                            "see also",
                            "library:",
                            "dll:",
                            "header:",
                            "minimum supported client",
                            "minimum supported server",
                            "target platform",
                        ]
                    ):
                        description_parts.append(text)
                        paragraph_count += 1

                        # Check paragraph limit only if set
                        if max_paragraphs and paragraph_count >= max_paragraphs:
                            break

            # Also collect from divs and other containers
            elif current_elem.name in ["div", "section"]:
                # Look for paragraphs within divs
                for p in current_elem.find_all("p", recursive=True):
                    text = p.get_text().strip()
                    if text and len(text) > 5:
                        # Avoid duplicates
                        if text not in description_parts:
                            description_parts.append(text)
                            paragraph_count += 1

                            if max_paragraphs and paragraph_count >= max_paragraphs:
                                break

                if max_paragraphs and paragraph_count >= max_paragraphs:
                    break

            current_elem = current_elem.find_next_sibling()

        if description_parts:
            # Join with proper spacing, preserving paragraph breaks
            full_description = " ".join(description_parts)
            return self._clean_description_text(full_description)

        # Fallback: try to get any content near the title
        return self._extract_description_fallback(soup)

    def _extract_description_fallback(self, soup: BeautifulSoup) -> str:
        """Fallback method for description extraction"""
        title = soup.find("h1")
        if title:
            next_p = title.find_next("p")
            if next_p:
                return next_p.get_text().strip()
        return ""

    def _extract_struct_members(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract structure members for struct types"""
        members = []

        # Look for Members or Membros section
        member_headers = soup.find_all(
            ["h2", "h3", "h4"],
            string=re.compile(r"Members|Membros|members", re.IGNORECASE),
        )

        for header in member_headers:
            next_elem = header.find_next_sibling()

            # Limite para evitar loop infinito
            max_iterations = 50
            iteration_count = 0

            while next_elem and iteration_count < max_iterations:
                iteration_count += 1

                if next_elem.name in ["h1", "h2", "h3"]:
                    break

                # Look for member definitions in various formats
                if next_elem.name in ["dl", "table", "div", "p"]:
                    struct_members = self._parse_struct_members_from_element(next_elem)
                    members.extend(struct_members)

                next_elem = next_elem.find_next_sibling()

            if members:
                break

        # Segunda tentativa: Extract from structure definition in <pre> blocks
        if not members:
            members = self._extract_members_from_code_blocks(soup)

        return members

    def _extract_members_from_code_blocks(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract structure members from C typedef definitions in <pre> blocks"""
        members = []

        # Find all pre/code blocks that might contain struct definitions
        code_blocks = soup.find_all(["pre", "code"])

        for block in code_blocks:
            code_text = block.get_text()

            # Look for typedef struct patterns
            if "typedef" in code_text and "{" in code_text and "}" in code_text:
                struct_members = self._parse_c_struct_definition(code_text, soup)
                if struct_members:
                    members.extend(struct_members)
                    break

        return members

    def _parse_c_struct_definition(
        self, code_text: str, soup: BeautifulSoup
    ) -> List[Dict]:
        """Parse C struct definition to extract member names and types"""
        members = []

        # Find the struct body between { and }
        struct_match = re.search(r"\{([^}]+)\}", code_text, re.DOTALL)
        if not struct_match:
            return members

        struct_body = struct_match.group(1)

        # Split into lines and process each member
        lines = struct_body.split("\n")

        for line in lines:
            line = line.strip()
            if not line or line.startswith("//") or line.startswith("/*"):
                continue

            # Remove trailing semicolon and comments
            line = re.sub(r";.*$", "", line).strip()
            if not line:
                continue

            # Parse member: type name or type name[size]
            # Examples: "BYTE Reserved1[2]", "BOOLEAN BeingDebugged", "PPEB_LDR_DATA Ldr"
            member_match = re.match(
                r"^([A-Z_][A-Z0-9_]*\s*\*?\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\[\d+\])?",
                line,
                re.IGNORECASE,
            )

            if member_match:
                member_type = member_match.group(1).strip()
                member_name = member_match.group(2)
                array_suffix = member_match.group(3) or ""

                # Add array suffix to type if present
                if array_suffix:
                    member_type += array_suffix

                members.append(
                    {
                        "name": member_name,
                        "type": member_type,
                        "description": self._get_member_description_from_docs(
                            soup, member_name
                        ),
                    }
                )

        return members

    def _get_member_description_from_docs(
        self, soup: BeautifulSoup, member_name: str
    ) -> str:
        """Try to find description for a specific struct member in the documentation"""
        # 1. Look for Members/Membros section with detailed descriptions
        member_headers = soup.find_all(
            ["h2", "h3", "h4"],
            string=re.compile(r"Members|Membros|members", re.IGNORECASE),
        )

        for header in member_headers:
            current_elem = header.find_next_sibling()

            while current_elem and current_elem.name not in ["h1", "h2"]:
                # Look for subsections with member names
                if current_elem.name in ["h3", "h4", "h5"]:
                    heading_text = current_elem.get_text().strip()
                    if member_name in heading_text:
                        # Found member heading, get next paragraph
                        next_p = current_elem.find_next_sibling("p")
                        if next_p:
                            return next_p.get_text().strip()

                # Look for dt/dd lists with member descriptions
                elif current_elem.name == "dl":
                    dts = current_elem.find_all("dt")
                    for dt in dts:
                        if member_name.lower() in dt.get_text().lower():
                            dd = dt.find_next_sibling("dd")
                            if dd:
                                return dd.get_text().strip()

                # Look for paragraphs that start with the member name
                elif current_elem.name == "p":
                    p_text = current_elem.get_text().strip()
                    if p_text.startswith(member_name) or f"`{member_name}`" in p_text:
                        # Extract description after the member name
                        if ":" in p_text:
                            desc = p_text.split(":", 1)[1].strip()
                            if desc:
                                return desc
                        # Se só tem o nome, não retornar, continuar para fallbacks
                        if len(p_text.strip()) <= len(member_name) + 10:
                            continue
                        return p_text

                current_elem = current_elem.find_next_sibling()

        # 2. Fallback: look for any mention in the document (skip if just member name)
        paragraphs = soup.find_all("p")
        for p in paragraphs:
            p_text = p.get_text().strip()
            # Skip if paragraph is just the member name or very similar
            if (
                p_text == member_name
                or p_text == f"{member_name}[{member_name}]"
                or p_text.startswith(f"{member_name}[")
                and p_text.endswith("]")
            ):
                continue
            if member_name in p_text and len(p_text) > len(member_name) + 10:
                return p_text

        # 3. Default description based on member name patterns
        if "reserved" in member_name.lower():
            return "Campo reservado para uso interno do sistema"
        elif member_name.lower() == "beingdebugged":
            return "Indica se o processo está sendo depurado"
        elif member_name.lower() == "ldr":
            return "Ponteiro para dados do loader de módulos carregados"
        elif member_name.lower() == "processparameters":
            return "Ponteiro para parâmetros do processo como linha de comando"
        elif member_name.lower() == "sessionid":
            return "Identificador da sessão do Terminal Services"
        elif "atlthunk" in member_name.lower():
            return "Ponteiro para lista ATL thunk para compatibilidade"
        elif "postprocessinit" in member_name.lower():
            return "Rotina de inicialização pós-processo"
        else:
            return "Membro da estrutura"

    def _extract_struct_definition(self, soup: BeautifulSoup) -> str:
        """Extract the complete C struct definition for display"""
        # Look for pre/code blocks that contain typedef struct definitions
        code_blocks = soup.find_all(["pre", "code"])

        for block in code_blocks:
            code_text = block.get_text().strip()

            # Look for typedef struct patterns - be more flexible
            if (
                ("typedef" in code_text or "struct" in code_text)
                and "{" in code_text
                and "}" in code_text
            ):

                # Clean and format the struct definition with proper indentation
                lines = code_text.split("\n")
                formatted_lines = []

                # Find minimum indentation to preserve structure
                non_empty_lines = [line for line in lines if line.strip()]
                if non_empty_lines:
                    min_indent = min(
                        len(line) - len(line.lstrip())
                        for line in non_empty_lines
                        if line.strip()
                    )
                else:
                    min_indent = 0

                for line in lines:
                    # Remove minimum indentation but preserve relative structure
                    if line.strip() and not line.strip().startswith("//"):
                        if len(line) >= min_indent:
                            formatted_line = line[min_indent:]
                        else:
                            formatted_line = line.strip()
                        formatted_lines.append(formatted_line)

                if formatted_lines:
                    return "\n".join(formatted_lines)

        return ""

    def _parse_struct_members_from_element(self, element) -> List[Dict]:
        """Parse struct members from dl, table, or div elements"""
        members = []

        if element.name == "dl":
            # Definition list format
            dts = element.find_all("dt")
            for i, dt in enumerate(dts[:50]):  # Limite de 50 elementos
                dd = dt.find_next_sibling("dd")
                if dd:
                    member_name = dt.get_text().strip()
                    description = dd.get_text().strip()
                    members.append(
                        {
                            "name": member_name,
                            "type": "Unknown",  # Type extraction would need more work
                            "description": description,
                        }
                    )

        elif element.name == "table":
            # Table format
            rows = element.find_all("tr")
            for row in rows[1:50]:  # Skip header row, limite de 50 rows
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    name = cells[0].get_text().strip()
                    desc = cells[1].get_text().strip()
                    members.append(
                        {"name": name, "type": "Unknown", "description": desc}
                    )

        elif element.name == "p":
            # Paragraph format - parse structured text (PEB style)
            text = element.get_text().strip()

            # Check if this paragraph contains a member name (short line with member identifier)
            lines = text.split("\n")
            first_line = lines[0].strip() if lines else text

            # Member name pattern: short line, contains alphanumeric/underscore/brackets
            is_member_name = len(first_line) < 50 and (  # Short line
                ("[" in first_line and "]" in first_line)  # Array notation
                or (
                    first_line.replace("_", "")
                    .replace("[", "")
                    .replace("]", "")
                    .isalnum()
                    and len(first_line) > 2
                )
            )  # Simple identifier

            if is_member_name:
                # This is a member name, look for description in next paragraph
                member_name = first_line
                description = "Membro da estrutura"

                # Try to find description in next sibling paragraph(s)
                next_p = element.find_next_sibling("p")
                if next_p:
                    desc_text = next_p.get_text().strip()
                    # Description should be longer than member name
                    if len(desc_text) > len(member_name) + 10:
                        description = desc_text

                        # If description is cut off, try to get more from subsequent paragraphs
                        if len(desc_text) > 400 and not desc_text.endswith("."):
                            next_next_p = next_p.find_next_sibling("p")
                            if next_next_p:
                                next_desc = next_next_p.get_text().strip()
                                # Only add if it seems like a continuation (long text, not another member name)
                                if (
                                    len(next_desc) > 50
                                    and not next_desc.replace("_", "")
                                    .replace("[", "")
                                    .replace("]", "")
                                    .isalnum()
                                ):
                                    description += " " + next_desc

                        # Limit final description length
                        description = description[:800]

                members.append(
                    {"name": member_name, "type": "Unknown", "description": description}
                )

        return members

    def _clean_description_text(self, text: str) -> str:
        """
        Clean description text by removing excessive whitespace and newlines
        """
        if not text:
            return ""

        # Remove excessive newlines and whitespace
        text = re.sub(r"\n\s*\n", " ", text)  # Replace \n\n with single space
        text = re.sub(r"\s+", " ", text)  # Replace multiple spaces with single space
        text = text.strip()

        return text
