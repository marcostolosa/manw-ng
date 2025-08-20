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

    def __init__(self):
        self.console = Console(
            force_terminal=True,
            legacy_windows=True,  # Enable Windows compatibility
            # Remove width fixo para se adaptar ao terminal
            color_system="truecolor",  # Force true color support
        )

    def format_output(self, function_info: Dict) -> None:
        """Format and display function information using Rich"""
        # Extract function name and header from the full name
        full_name = function_info["name"]

        # Check if name contains header info like "Função VirtualAllocEx (memoryapi.h)"
        import re

        header_match = re.search(r"\(([^)]+\.h)\)", full_name)
        if header_match:
            header = header_match.group(1)
            # Extract just the function name (remove "Função " prefix and header)
            func_name = re.sub(
                r"^(Função\s+|Function\s+)?(.+?)\s*\([^)]+\).*$", r"\2", full_name
            )
            title_text = f"{func_name} ({header})"
        else:
            # Fallback if no header found
            func_name = re.sub(r"^(Função\s+|Function\s+)", "", full_name)
            title_text = func_name

        # Título principal estilo Monokai
        self.console.print(
            Panel(
                f"[bold #F92672]» {title_text}[/bold #F92672]",
                title="[bold #66D9EF]» Win32 API Function[/bold #66D9EF]",
                border_style="#AE81FF",
                expand=False,
                padding=(1, 2),
            )
        )

        # Informacoes basicas estilo Monokai
        basic_table = Table(
            title="[bold #66D9EF]» Informacoes Basicas[/bold #66D9EF]",
            border_style="#75715E",
        )
        basic_table.add_column("Propriedade", style="#F8F8F2", no_wrap=True)
        basic_table.add_column("Valor", style="#E6DB74")

        basic_table.add_row("DLL", function_info["dll"])
        basic_table.add_row("Calling Convention", function_info["calling_convention"])
        basic_table.add_row(
            "Número de Parâmetros", str(function_info["parameter_count"])
        )
        basic_table.add_row("Arquiteturas", ", ".join(function_info["architectures"]))
        basic_table.add_row("Tipo de Retorno", function_info["return_type"])

        self.console.print(basic_table)

        # Assinatura da função estilo Monokai
        if function_info["signature"]:
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
                    title="[bold #A6E22E]» Assinatura da Funcao[/bold #A6E22E]",
                    border_style="#75715E",
                    padding=(1, 2),
                )
            )

        # Descrição estilo Monokai
        if function_info["description"]:
            self.console.print(
                Panel(
                    f"[#F8F8F2]{function_info['description']}[/#F8F8F2]",
                    title="[bold #FD971F]» Descrição[/bold #FD971F]",
                    border_style="#75715E",
                    padding=(1, 2),
                )
            )

        # Parâmetros estilo Monokai
        if function_info["parameters"]:
            param_table = Table(
                title="[bold #AE81FF]» Parâmetros[/bold #AE81FF]",
                expand=True,
                show_lines=True,
                border_style="#75715E",
            )
            param_table.add_column("Nome", style="#66D9EF", min_width=15, max_width=25)
            param_table.add_column("Tipo", style="#E6DB74", min_width=8, max_width=25)
            param_table.add_column(
                "Descrição", style="#F8F8F2", no_wrap=False, overflow="fold"
            )

            for param in function_info["parameters"]:
                # Build description with value tables if available
                description = param["description"] or "Sem descrição disponível"

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

        # Valor de retorno estilo Monokai
        if function_info["return_description"]:
            # Se contém markdown bullets (linhas começando com "- "), renderizar como markdown
            if function_info["return_description"].strip().startswith("- "):
                self.console.print(
                    Panel(
                        Markdown(function_info["return_description"]),
                        title="[bold #F92672]» Valor de Retorno[/bold #F92672]",
                        border_style="#75715E",
                        padding=(1, 2),
                    )
                )
            else:
                # Fallback para texto simples se não for markdown
                self.console.print(
                    Panel(
                        f"[#F8F8F2]{function_info['return_description']}[/#F8F8F2]",
                        title="[bold #F92672]» Valor de Retorno[/bold #F92672]",
                        border_style="#75715E",
                        padding=(1, 2),
                    )
                )

    def _manual_syntax_highlight(self, code: str) -> str:
        """Manual C++ syntax highlighting fallback for Windows"""
        import re
        
        # C++ keywords
        keywords = [
            'int', 'char', 'void', 'const', 'unsigned', 'signed', 'long', 'short',
            'BOOL', 'DWORD', 'LPCSTR', 'LPCWSTR', 'LPSTR', 'LPWSTR', 'HANDLE',
            'HWND', 'HDC', 'HINSTANCE', 'LPVOID', 'PVOID', 'SIZE_T', 'UINT',
            'WORD', 'BYTE', 'LONG', 'ULONG', 'LPARAM', 'WPARAM', 'LRESULT',
            'FARPROC', 'PROC', 'CALLBACK', 'WINAPI', 'STDCALL', 'CDECL'
        ]
        
        # Apply highlighting
        highlighted = code
        
        # Highlight keywords
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            highlighted = re.sub(
                pattern, 
                f'[#F92672]{keyword}[/#F92672]', 
                highlighted, 
                flags=re.IGNORECASE
            )
        
        # Highlight function names (word followed by parentheses)
        highlighted = re.sub(
            r'\b([A-Za-z_]\w*)\s*\(',
            r'[#A6E22E]\1[/#A6E22E](',
            highlighted
        )
        
        # Highlight string literals
        highlighted = re.sub(
            r'"([^"]*)"',
            r'[#E6DB74]"\1"[/#E6DB74]',
            highlighted
        )
        
        # Highlight numbers
        highlighted = re.sub(
            r'\b(\d+)\b',
            r'[#AE81FF]\1[/#AE81FF]',
            highlighted
        )
        
        # Highlight comments
        highlighted = re.sub(
            r'//(.*)$',
            r'[#75715E]//\1[/#75715E]',
            highlighted,
            flags=re.MULTILINE
        )
        
        highlighted = re.sub(
            r'/\*(.*?)\*/',
            r'[#75715E]/*\1*/[/#75715E]',
            highlighted,
            flags=re.DOTALL
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

        return md_content
