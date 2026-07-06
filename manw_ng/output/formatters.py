"""
Output formatters for MANW-NG

Different output formats: Rich, JSON, Markdown
"""

import json
from typing import Dict
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax


class RichFormatter:
    """Rich console formatter for beautiful terminal output"""

    def __init__(self, language="us", show_remarks=False, show_parameter_tables=False):
        import sys

        # Configure console for maximum Windows compatibility
        console_config = {
            "force_terminal": True,
            "legacy_windows": True,
            "color_system": "auto",  # Let Rich auto-detect
        }

        # Add Windows-specific safe encoding
        if sys.platform.startswith("win"):
            console_config.update(
                {"file": sys.stdout, "stderr": False, "force_jupyter": False}
            )

        self.console = Console(**console_config)
        self.language = language
        self.show_remarks = show_remarks
        self.show_parameter_tables = show_parameter_tables
        # Symbol classification removed - using simple classification

        # Elegant Unicode symbols
        self.cross_mark = "❌"
        self.lightbulb = "💡"

        # Localized strings
        self.strings = {
            "us": {
                "win32_function": "Win32 API Function",
                "basic_info": "Basic Information",
                "function_signature": "Function Signature",
                "description": "Description",
                "parameters": "Parameters",
                "return_value": "Return Value",
                "property": "Property",
                "value": "Value",
                "dll": "DLL",
                "calling_convention": "Calling Convention",
                "parameter_count": "Parameter Count",
                "architectures": "Architectures",
                "return_type": "Return Type",
                "name": "Name",
                "type": "Type",
                "documentation_url": "Documentation URL",
            },
            "br": {
                "win32_function": "Função Win32 API",
                "basic_info": "Informações Básicas",
                "function_signature": "Assinatura da Função",
                "description": "Descrição",
                "parameters": "Parâmetros",
                "return_value": "Valor de Retorno",
                "property": "Propriedade",
                "value": "Valor",
                "dll": "DLL",
                "calling_convention": "Convenção de Chamada",
                "parameter_count": "Número de Parâmetros",
                "architectures": "Arquiteturas",
                "return_type": "Tipo de Retorno",
                "name": "Nome",
                "type": "Tipo",
                "documentation_url": "URL da Documentação",
                # Novos tipos de símbolos
                "structure": "Estrutura",
                "enumeration": "Enumeração",
                "callback": "Função de Callback",
                "interface": "Interface COM",
                "members": "Membros",
                "member_count": "Número de Membros",
                "struct_signature": "Definição da Estrutura",
            },
        }

    def get_string(self, key: str) -> str:
        """Get localized string"""
        return self.strings.get(self.language, self.strings["us"]).get(key, key)

    def format_output(self, function_info: Dict) -> None:
        """Format and display symbol information using Rich (adaptado para diferentes tipos)"""

        # Check if function was found
        if (
            not function_info.get("documentation_found")
            or function_info.get("documentation_found") == "False"
        ):
            self._show_not_found_error(
                function_info.get("name", function_info.get("symbol", "Unknown"))
            )
            return

        # Always use localized string for title
        symbol_title = self.get_string("win32_function")

        # Extract symbol name and header from the full name
        full_name = function_info["name"]
        import re

        header_match = re.search(r"\(([^)]+\.h)\)", full_name)
        if header_match:
            header = header_match.group(1)
            # Extract just the symbol name (remove prefixes and header)
            symbol_name = re.sub(
                r"^(Função\s+|Function\s+|Estrutura\s+|Structure\s+)?(.+?)\s*\([^)]+\).*$",
                r"\2",
                full_name,
            )
            title_text = f"{symbol_name} ({header})"
        else:
            # Fallback if no header found
            symbol_name = re.sub(
                r"^(Função\s+|Function\s+|Estrutura\s+|Structure\s+)", "", full_name
            )
            title_text = symbol_name

        # Título principal estilo Monokai adaptado ao tipo
        self.console.print(
            Panel(
                f"[bold #F92672]» {title_text}[/bold #F92672]",
                title=f"[bold #66D9EF]» {symbol_title}[/bold #66D9EF]",
                border_style="#AE81FF",
                expand=False,
                padding=(1, 2),
            )
        )

        # Informações básicas adaptadas ao tipo de símbolo
        self._render_basic_info_table(function_info)

        # Assinatura/Sintaxe adaptada ao tipo
        if function_info["signature"]:
            self._render_signature_section(function_info)

        # Descrição estilo Monokai
        if function_info["description"]:
            self.console.print(
                Panel(
                    f"[#F8F8F2]{function_info['description']}[/#F8F8F2]",
                    title=f"[bold #FD971F]» {self.get_string('description')}[/bold #FD971F]",
                    border_style="#75715E",
                    padding=(1, 2),
                )
            )

        # Renderizar parâmetros ou membros baseado no tipo
        self._render_parameters_or_members(function_info)

        # Valor de retorno (só para funções)
        if function_info.get("kind") in ["function", "callback"] and function_info.get(
            "return_description"
        ):
            self._render_return_value(function_info)

        # Renderizar seção de observações/remarks após valor de retorno (apenas se habilitado)
        if (
            self.show_remarks
            and function_info.get("kind") in ["function", "callback", "struct"]
            and function_info.get("remarks")
        ):
            self._render_remarks(function_info)

        # URL da documentação no final
        doc_url = function_info.get("url", "")
        if doc_url:
            self.console.print()  # Linha em branco
            self.console.print(f"[dim]📖 {doc_url}[/dim]", style="link " + doc_url)

    def _render_signature_section(self, function_info: Dict) -> None:
        """Renderiza seção de assinatura/sintaxe adaptada ao tipo"""
        symbol_kind = function_info.get("kind", "function")

        # Determinar título baseado no tipo de símbolo
        if symbol_kind == "struct":
            title_key = "struct_signature"
            title = self.get_string(title_key)
            if not title or title == title_key:  # Fallback se não encontrar
                title = (
                    "Definição da Estrutura"
                    if self.language == "br"
                    else "Structure Definition"
                )
        else:
            title = self.get_string("function_signature")

        # Use markdown com código C para melhor compatibilidade
        from rich.markdown import Markdown

        signature_markdown = f"```c\n{function_info['signature']}\n```"

        try:
            # Tentar usar Markdown com syntax highlighting
            syntax = Markdown(signature_markdown, code_theme="monokai")
        except Exception:
            # Fallback: Usar manual highlighting
            from rich.text import Text

            highlighted_text = self._manual_syntax_highlight(function_info["signature"])
            syntax = Text.from_markup(highlighted_text)

        self.console.print(
            Panel(
                syntax,
                title=f"[bold #A6E22E]» {title}[/bold #A6E22E]",
                border_style="#75715E",
                padding=(1, 2),
            )
        )

    def _render_basic_info_table(self, function_info: Dict) -> None:
        """Renderiza tabela de informações básicas adaptada ao tipo de símbolo"""
        basic_table = Table(
            title=f"[bold #66D9EF]» {self.get_string('basic_info')}[/bold #66D9EF]",
            border_style="#75715E",
        )
        basic_table.add_column(
            self.get_string("property"), style="#F8F8F2", no_wrap=True
        )
        basic_table.add_column(self.get_string("value"), style="#E6DB74")

        # DLL sempre presente
        basic_table.add_row(self.get_string("dll"), function_info["dll"])

        symbol_kind = function_info.get("kind", "function")

        if symbol_kind in ["function", "callback"]:
            # Campos específicos para funções
            basic_table.add_row(
                self.get_string("calling_convention"),
                function_info["calling_convention"],
            )
            basic_table.add_row(
                self.get_string("parameter_count"),
                str(function_info["parameter_count"]),
            )
            basic_table.add_row(
                self.get_string("return_type"), function_info["return_type"]
            )
        elif symbol_kind == "struct":
            # Campos específicos para estruturas
            member_count = function_info.get(
                "member_count", len(function_info.get("members", []))
            )
            basic_table.add_row(self.get_string("member_count"), str(member_count))
        elif symbol_kind in ["enum", "interface"]:
            # Campos mínimos para enums e interfaces
            pass

        # Arquiteturas sempre no final
        basic_table.add_row(
            self.get_string("architectures"), ", ".join(function_info["architectures"])
        )

        self.console.print(basic_table)

    def _render_parameters_or_members(self, function_info: Dict) -> None:
        """Renderiza parâmetros para funções ou membros para estruturas"""
        symbol_kind = function_info.get("kind", "function")

        if symbol_kind in ["function", "callback"] and function_info["parameters"]:
            self._render_parameters_table(function_info)
        elif symbol_kind == "struct" and function_info.get("members"):
            self._render_members_table(function_info)

    def _render_parameters_table(self, function_info: Dict) -> None:
        """Renderiza tabela de parâmetros para funções"""
        param_table = Table(
            title=f"[bold #AE81FF]» {self.get_string('parameters')}[/bold #AE81FF]",
            expand=True,
            show_lines=True,
            border_style="#75715E",
        )
        param_table.add_column(
            self.get_string("name"), style="#66D9EF", min_width=15, max_width=25
        )
        param_table.add_column(
            self.get_string("type"), style="#E6DB74", min_width=8, max_width=25
        )
        param_table.add_column(
            self.get_string("description"),
            style="#F8F8F2",
            no_wrap=False,
            overflow="fold",
        )

        for param in function_info["parameters"]:
            # Build description with value tables if available
            no_description = (
                "No description available"
                if self.language == "us"
                else "Sem descrição disponível"
            )
            description = param["description"] or no_description

            # Add value tables as structured tables
            if "values" in param and param["values"]:
                description += f"\n\n[bold yellow]Tabelas de valores ({len(param['values'])} tabelas encontradas):[/bold yellow]"

            param_table.add_row(
                param["name"],
                param.get("type", "UNKNOWN"),
                description.strip(),
            )

        self.console.print(param_table)

        # Render value tables for parameters that have them (only if --tabs flag is set)
        if self.show_parameter_tables:
            for param in function_info["parameters"]:
                if "values" in param and param["values"]:
                    self._render_parameter_value_tables(param)

    def _render_members_table(self, function_info: Dict) -> None:
        """Renderiza tabela de membros para estruturas"""
        members = function_info.get("members", [])

        member_table = Table(
            title=f"[bold #AE81FF]» {self.get_string('members')}[/bold #AE81FF]",
            expand=True,
            show_lines=True,
            border_style="#75715E",
        )
        member_table.add_column(
            self.get_string("name"), style="#66D9EF", min_width=15, max_width=25
        )
        member_table.add_column(
            self.get_string("type"), style="#E6DB74", min_width=8, max_width=25
        )
        member_table.add_column(
            self.get_string("description"),
            style="#F8F8F2",
            no_wrap=False,
            overflow="fold",
        )

        for member in members:
            no_description = (
                "No description available"
                if self.language == "us"
                else "Sem descrição disponível"
            )
            description = member.get("description", no_description)

            member_table.add_row(
                member.get("name", "Unknown"),
                member.get("type", "Unknown"),
                description,
            )

        self.console.print(member_table)

    def _render_parameter_value_tables(self, param: Dict) -> None:
        """Render value tables for a parameter"""
        param_name = param.get("name", "Unknown")
        value_tables = param.get("values", [])

        for i, value_table in enumerate(value_tables):
            entries = value_table.get("entries", [])
            if not entries:
                continue

            # Create table for this value set
            table = Table(
                title=f"[bold blue]» {param_name} - Tabela {i+1}[/bold blue]",
                expand=True,
                show_lines=True,
                border_style="#66D9EF",
                show_header=True,
            )
            table.add_column("Valor", style="#AE81FF bold", min_width=20, max_width=40)
            table.add_column(
                "Significado", style="#F8F8F2", no_wrap=False, overflow="fold"
            )

            # Add entries to table
            for entry in entries:
                value = entry.get("value", "").strip()
                meaning = entry.get("meaning", "").strip()

                if value and meaning:
                    table.add_row(f"[bold blue]{value}[/bold blue]", meaning)

            # Print the table
            self.console.print()
            self.console.print(table)

    def _render_return_value(self, function_info: Dict) -> None:
        """Renderiza seção de valor de retorno para funções"""
        if function_info["return_description"]:
            # Se contém markdown bullets (linhas começando com "- "), renderizar como texto com Rich markup
            if function_info["return_description"].strip().startswith("- "):
                self.console.print(
                    Panel(
                        function_info[
                            "return_description"
                        ],  # Rich will handle the markup
                        title=f"[bold #F92672]» {self.get_string('return_value')}[/bold #F92672]",
                        border_style="#75715E",
                        padding=(1, 2),
                    )
                )
            else:
                # Fallback para texto simples se não for markdown
                self.console.print(
                    Panel(
                        f"[#F8F8F2]{function_info['return_description']}[/#F8F8F2]",
                        title=f"[bold #F92672]» {self.get_string('return_value')}[/bold #F92672]",
                        border_style="#75715E",
                        padding=(1, 2),
                    )
                )

    def _render_remarks(self, function_info: Dict) -> None:
        """Renderiza seção de observações/remarks"""
        if function_info.get("remarks"):
            remarks_title = "Observações" if self.language == "br" else "Remarks"
            self.console.print(
                Panel(
                    f"[#F8F8F2]{function_info['remarks']}[/#F8F8F2]",
                    title=f"[bold #F92672]» {remarks_title}[/bold #F92672]",
                    border_style="#75715E",
                    padding=(1, 2),
                )
            )

    def _manual_syntax_highlight(self, code: str) -> str:
        """Manual C++ syntax highlighting fallback for Windows"""
        import re

        # C++ keywords
        keywords = [
            "int",
            "char",
            "void",
            "const",
            "unsigned",
            "signed",
            "long",
            "short",
            "BOOL",
            "DWORD",
            "LPCSTR",
            "LPCWSTR",
            "LPSTR",
            "LPWSTR",
            "HANDLE",
            "HWND",
            "HDC",
            "HINSTANCE",
            "LPVOID",
            "PVOID",
            "SIZE_T",
            "UINT",
            "WORD",
            "BYTE",
            "LONG",
            "ULONG",
            "LPARAM",
            "WPARAM",
            "LRESULT",
            "FARPROC",
            "PROC",
            "CALLBACK",
            "WINAPI",
            "STDCALL",
            "CDECL",
        ]

        # Apply highlighting
        highlighted = code

        # Highlight keywords
        for keyword in keywords:
            pattern = r"\b" + re.escape(keyword) + r"\b"
            highlighted = re.sub(
                pattern,
                f"[#F92672]{keyword}[/#F92672]",
                highlighted,
                flags=re.IGNORECASE,
            )

        # Highlight function names (word followed by parentheses)
        highlighted = re.sub(
            r"\b([A-Za-z_]\w*)\s*\(", r"[#A6E22E]\1[/#A6E22E](", highlighted
        )

        # Highlight string literals
        highlighted = re.sub(r'"([^"]*)"', r'[#E6DB74]"\1"[/#E6DB74]', highlighted)

        # Highlight numbers
        highlighted = re.sub(r"\b(\d+)\b", r"[#AE81FF]\1[/#AE81FF]", highlighted)

        # Highlight comments
        highlighted = re.sub(
            r"//(.*)$", r"[#75715E]//\1[/#75715E]", highlighted, flags=re.MULTILINE
        )

        highlighted = re.sub(
            r"/\*(.*?)\*/", r"[#75715E]/*\1*/[/#75715E]", highlighted, flags=re.DOTALL
        )

        return highlighted

    def _show_not_found_error(self, function_name: str) -> None:
        """Show elegant error message when function is not found"""
        error_messages = {
            "us": {
                "title": "Function Not Found",
                "message": f"The Win32 API function [bold red]'{function_name}'[/bold red] could not be found in Microsoft documentation.",
                "suggestions": [
                    "• Verify the function name spelling",
                    "• Check if the function requires A/W suffix (e.g., CreateFileA/CreateFileW)",
                    "• Some deprecated functions may not be documented",
                    "• Try searching for similar function names",
                ],
            },
            "br": {
                "title": "Função Não Encontrada",
                "message": f"A função Win32 API [bold red]'{function_name}'[/bold red] não foi encontrada na documentação da Microsoft.",
                "suggestions": [
                    "• Verifique a ortografia do nome da função",
                    "• Verifique se a função requer sufixo A/W (ex: CreateFileA/CreateFileW)",
                    "• Algumas funções obsoletas podem não estar documentadas",
                    "• Tente buscar por nomes de funções similares",
                ],
            },
        }

        lang_messages = error_messages.get(self.language, error_messages["us"])

        # Main error panel
        self.console.print()
        self.console.print(
            Panel(
                lang_messages["message"],
                title=f"[bold red]{self.cross_mark} {lang_messages['title']}[/bold red]",
                border_style="red",
                padding=(1, 2),
            )
        )

        # Suggestions panel
        suggestions_text = "\n".join(lang_messages["suggestions"])
        self.console.print(
            Panel(
                suggestions_text,
                title=(
                    f"[bold yellow]{self.lightbulb} Suggestions[/bold yellow]"
                    if self.language == "us"
                    else f"[bold yellow]{self.lightbulb} Sugestões[/bold yellow]"
                ),
                border_style="yellow",
                padding=(1, 2),
            )
        )
        self.console.print()


class JSONFormatter:
    """JSON formatter for machine-readable output"""

    @staticmethod
    def format_output(
        function_info: Dict,
        show_remarks: bool = False,
        show_parameter_tables: bool = False,
    ) -> str:
        """Format function information as JSON"""
        # Convert SymbolInfo objects to dict for JSON serialization
        json_compatible = JSONFormatter._make_json_serializable(function_info)
        return json.dumps(json_compatible, indent=2, ensure_ascii=False, default=str)

    @staticmethod
    def _make_json_serializable(obj):
        """Make object JSON serializable"""
        if hasattr(obj, "__dict__"):
            # Convert dataclass or object to dict
            return {
                k: JSONFormatter._make_json_serializable(v)
                for k, v in obj.__dict__.items()
            }
        elif isinstance(obj, dict):
            return {k: JSONFormatter._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [JSONFormatter._make_json_serializable(item) for item in obj]
        elif isinstance(obj, (set, frozenset)):
            return list(obj)
        elif isinstance(obj, (bool, int, float, str, type(None))):
            # JSON-native types, keep as-is
            return obj
        elif hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes)):
            # Handle other iterables
            return [JSONFormatter._make_json_serializable(item) for item in obj]
        else:
            # Try to convert to string for unsupported types
            try:
                return str(obj)
            except Exception:
                return repr(obj)


class MarkdownFormatter:
    """Markdown formatter for documentation"""

    @staticmethod
    def format_output(
        function_info: Dict,
        language: str = "br",
        show_remarks: bool = False,
        show_parameter_tables: bool = False,
    ) -> str:
        """Format function information as Markdown"""

        # Check if function was found
        if (
            not function_info.get("documentation_found")
            or function_info.get("documentation_found") == "False"
        ):
            function_name = function_info.get(
                "name", function_info.get("symbol", "Unknown")
            )
            if language == "br":
                return f"""# Função Não Encontrada

A função Win32 API '{function_name}' não foi encontrada na documentação da Microsoft.

## Sugestões
- Verifique a ortografia do nome da função
- Verifique se a função requer sufixo A/W (ex: CreateFileA/CreateFileW)
- Algumas funções obsoletas podem não estar documentadas
- Tente buscar por nomes de funções similares"""
            else:
                return f"""# Function Not Found

The Win32 API function '{function_name}' could not be found in Microsoft documentation.

## Suggestions
- Verify the function name spelling
- Check if the function requires A/W suffix (e.g., CreateFileA/CreateFileW)
- Some deprecated functions may not be documented
- Try searching for similar function names"""

        strings = {
            "us": {
                "basic_info": "Basic Information",
                "calling_convention": "Calling Convention",
                "parameters_field": "Parameter Count",
                "architectures": "Architectures",
                "return_type": "Return Type",
                "signature": "Signature",
                "description": "Description",
                "parameters": "Parameters",
                "return_value": "Return Value",
                "remarks": "Remarks",
                "values": "Values",
            },
            "br": {
                "basic_info": "Informações Básicas",
                "calling_convention": "Calling Convention",
                "parameters_field": "Parâmetros",
                "architectures": "Arquiteturas",
                "return_type": "Tipo de Retorno",
                "signature": "Assinatura",
                "description": "Descrição",
                "parameters": "Parâmetros",
                "return_value": "Valor de Retorno",
                "remarks": "Observações",
                "values": "Valores",
            },
        }
        s = strings.get(language, strings["br"])

        md_content = f"""# {function_info['name']}

## {s['basic_info']}

- **DLL**: {function_info['dll']}
- **{s['calling_convention']}**: {function_info['calling_convention']}
- **{s['parameters_field']}**: {function_info['parameter_count']}
- **{s['architectures']}**: {', '.join(function_info['architectures'])}
- **{s['return_type']}**: {function_info['return_type']}

## {s['signature']}

```{function_info.get('signature_language', 'c')}
{function_info['signature']}
```

## {s['description']}

{function_info['description']}

## {s['parameters']}
"""

        for param in function_info.get("parameters", []):
            md_content += f"\n### {param['name']}\n{param['description']}\n"

            # Add value tables if present
            if "values" in param and param["values"]:
                for value_table in param["values"]:
                    md_content += f"\n#### {value_table.get('title', s['values'])}\n\n"
                    md_content += "| Value | Meaning |\n|-------|---------|\n"
                    for entry in value_table.get("entries", []):
                        value = entry["value"].replace("|", "\\|")
                        meaning = entry["meaning"].replace("|", "\\|")
                        md_content += f"| `{value}` | {meaning} |\n"
                    md_content += "\n"

        if function_info.get("return_description"):
            md_content += (
                f"\n## {s['return_value']}\n\n{function_info['return_description']}"
            )

        if show_remarks and function_info.get("remarks"):
            md_content += f"\n## {s['remarks']}\n\n{function_info['remarks']}"

        return md_content
