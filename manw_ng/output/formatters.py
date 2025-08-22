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
from ..core.symbol_classifier import Win32SymbolClassifier


class RichFormatter:
    """Rich console formatter for beautiful terminal output"""

    def __init__(self, language="us"):
        self.console = Console(
            force_terminal=True,
            legacy_windows=True,  # Enable Windows compatibility
            # Remove width fixo para se adaptar ao terminal
            color_system="truecolor",  # Force true color support
        )
        self.language = language
        self.classifier = Win32SymbolClassifier()

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
        # Get symbol classification info
        symbol_info = function_info.get("symbol_info")
        if symbol_info:
            display_info = self.classifier.get_display_info(symbol_info, self.language)
            symbol_title = display_info["type_display"]
        else:
            # Fallback para compatibilidade
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

        # Renderizar seção de observações/remarks após valor de retorno
        if function_info.get("kind") in ["function", "callback"] and function_info.get(
            "remarks"
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

            # Add value tables with Monokai colors
            if "values" in param and param["values"]:
                description += "\n\n"
                for value_table in param["values"]:
                    description += f"[bold #A6E22E]{value_table.get('title', 'Values')}:[/bold #A6E22E]\n"
                    for entry in value_table.get("entries", []):
                        # Use Monokai colors
                        description += f"• [#66D9EF]{entry['value']}[/#66D9EF]: [#F8F8F2]{entry['meaning']}[/#F8F8F2]\n"
                    description += "\n"

            param_table.add_row(
                param["name"],
                param.get("type", "UNKNOWN"),
                description.strip(),
            )

        self.console.print(param_table)

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

    def _render_return_value(self, function_info: Dict) -> None:
        """Renderiza seção de valor de retorno para funções"""
        if function_info["return_description"]:
            # Se contém markdown bullets (linhas começando com "- "), renderizar como markdown
            if function_info["return_description"].strip().startswith("- "):
                self.console.print(
                    Panel(
                        Markdown(function_info["return_description"]),
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


class JSONFormatter:
    """JSON formatter for machine-readable output"""

    @staticmethod
    def format_output(function_info: Dict) -> str:
        """Format function information as JSON"""
        return json.dumps(function_info, indent=2, ensure_ascii=False)


class MarkdownFormatter:
    """Markdown formatter for documentation"""

    @staticmethod
    def format_output(function_info: Dict) -> str:
        """Format function information as Markdown"""
        md_content = f"""# {function_info['name']}

## Informações Básicas

- **DLL**: {function_info['dll']}
- **Calling Convention**: {function_info['calling_convention']}  
- **Parâmetros**: {function_info['parameter_count']}
- **Arquiteturas**: {', '.join(function_info['architectures'])}
- **Tipo de Retorno**: {function_info['return_type']}

## Assinatura

```{function_info.get('signature_language', 'c')}
{function_info['signature']}
```

## Descrição

{function_info['description']}

## Parâmetros
"""

        for param in function_info.get("parameters", []):
            md_content += f"\n### {param['name']}\n{param['description']}\n"

            # Add value tables if present
            if "values" in param and param["values"]:
                for value_table in param["values"]:
                    md_content += f"\n#### {value_table.get('title', 'Values')}\n\n"
                    md_content += "| Value | Meaning |\n|-------|---------|\n"
                    for entry in value_table.get("entries", []):
                        value = entry["value"].replace("|", "\\|")
                        meaning = entry["meaning"].replace("|", "\\|")
                        md_content += f"| `{value}` | {meaning} |\n"
                    md_content += "\n"

        if function_info.get("return_description"):
            md_content += (
                f"\n## Valor de Retorno\n\n{function_info['return_description']}"
            )

        if function_info.get("remarks"):
            section_title = "Observações" if self.language == "br" else "Remarks"
            md_content += f"\n## {section_title}\n\n{function_info['remarks']}"

        return md_content
