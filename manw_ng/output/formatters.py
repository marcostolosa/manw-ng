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


class RichFormatter:
    """Rich console formatter for beautiful terminal output"""

    def __init__(self):
        self.console = Console()

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

        # Título principal com estilo moderno
        self.console.print(
            Panel(
                f"[bold bright_blue]» {title_text}[/bold bright_blue]",
                title="[bold bright_cyan]» Win32 API Function[/bold bright_cyan]",
                border_style="bright_blue",
                expand=False,
                padding=(1, 2)
            )
        )

        # Informações básicas com estilo moderno
        basic_table = Table(title="[bold bright_cyan]» Informações Básicas[/bold bright_cyan]", border_style="cyan")
        basic_table.add_column("Propriedade", style="bright_cyan", no_wrap=True)
        basic_table.add_column("Valor", style="bright_magenta")

        basic_table.add_row("DLL", function_info["dll"])
        basic_table.add_row("Calling Convention", function_info["calling_convention"])
        basic_table.add_row(
            "Número de Parâmetros", str(function_info["parameter_count"])
        )
        basic_table.add_row("Arquiteturas", ", ".join(function_info["architectures"]))
        basic_table.add_row("Tipo de Retorno", function_info["return_type"])

        self.console.print(basic_table)

        # Assinatura da função com estilo moderno
        if function_info["signature"]:
            # Use detected language or fallback to 'c'
            lang = function_info.get("signature_language", "c")
            self.console.print(
                Panel(
                    Markdown(f"```{lang}\n{function_info['signature']}\n```"),
                    title="[bold bright_yellow]» Assinatura da Função[/bold bright_yellow]",
                    border_style="yellow",
                    padding=(1, 2)
                )
            )

        # Descrição com estilo moderno
        if function_info["description"]:
            self.console.print(
                Panel(
                    function_info["description"], 
                    title="[bold bright_white]» Descrição[/bold bright_white]",
                    border_style="white",
                    padding=(1, 2)
                )
            )

        # Parâmetros com estilo moderno
        if function_info["parameters"]:
            param_table = Table(
                title="[bold bright_red]» Parâmetros[/bold bright_red]", 
                expand=True, 
                show_lines=True,
                border_style="red"
            )
            param_table.add_column("Nome", style="bright_cyan", min_width=15, max_width=25)
            param_table.add_column("Tipo", style="bright_yellow", min_width=8, max_width=25)
            param_table.add_column(
                "Descrição", style="bright_green", no_wrap=False, overflow="fold"
            )

            for param in function_info["parameters"]:
                # Build description with value tables if available
                description = param["description"] or "Sem descrição disponível"

                # Add value tables if present using Rich markup (not markdown)
                if "values" in param and param["values"]:
                    description += "\n\n"
                    for value_table in param["values"]:
                        description += (
                            f"[bold]{value_table.get('title', 'Values')}:[/bold]\n"
                        )
                        for entry in value_table.get("entries", []):
                            # Use Rich markup instead of markdown
                            description += (
                                f"• [cyan]{entry['value']}[/cyan]: {entry['meaning']}\n"
                            )
                        description += "\n"

                param_table.add_row(
                    param["name"],
                    param.get("type", "UNKNOWN"),
                    description.strip(),
                )

            self.console.print(param_table)

        # Valor de retorno - renderizar markdown com estilo moderno
        if function_info["return_description"]:
            # Se contém markdown bullets (linhas começando com "- "), renderizar como markdown
            if function_info["return_description"].strip().startswith("- "):
                self.console.print(
                    Panel(
                        Markdown(function_info["return_description"]), 
                        title="[bold green]» Valor de Retorno[/bold green]",
                        border_style="green",
                        padding=(1, 2)
                    )
                )
            else:
                # Fallback para texto simples se não for markdown
                self.console.print(
                    Panel(
                        function_info["return_description"], 
                        title="[bold green]» Valor de Retorno[/bold green]",
                        border_style="green",
                        padding=(1, 2)
                    )
                )


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
