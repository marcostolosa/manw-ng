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
        # Título principal
        self.console.print(
            Panel(
                f"[bold blue]{function_info['name']}[/bold blue]",
                title="Win32 API Function",
                expand=False,
            )
        )

        # Informações básicas
        basic_table = Table(title="Informações Básicas")
        basic_table.add_column("Propriedade", style="cyan")
        basic_table.add_column("Valor", style="magenta")

        basic_table.add_row("DLL", function_info["dll"])
        basic_table.add_row("Calling Convention", function_info["calling_convention"])
        basic_table.add_row(
            "Número de Parâmetros", str(function_info["parameter_count"])
        )
        basic_table.add_row("Arquiteturas", ", ".join(function_info["architectures"]))
        basic_table.add_row("Tipo de Retorno", function_info["return_type"])

        self.console.print(basic_table)

        # Assinatura da função
        if function_info["signature"]:
            self.console.print(
                Panel(
                    Markdown(f"```c\n{function_info['signature']}\n```"),
                    title="Assinatura da Função",
                )
            )

        # Descrição
        if function_info["description"]:
            self.console.print(Panel(function_info["description"], title="Descrição"))

        # Parâmetros
        if function_info["parameters"]:
            param_table = Table(title="Parâmetros", expand=True, show_lines=True)
            param_table.add_column("Nome", style="cyan", min_width=15, max_width=25)
            param_table.add_column("Tipo", style="yellow", min_width=8, max_width=25)
            param_table.add_column(
                "Descrição", style="green", no_wrap=False, overflow="fold"
            )

            for param in function_info["parameters"]:
                param_table.add_row(
                    param["name"],
                    param.get("type", "UNKNOWN"),
                    param["description"] or "Sem descrição disponível",
                )

            self.console.print(param_table)

        # Valor de retorno
        if function_info["return_description"]:
            self.console.print(
                Panel(function_info["return_description"], title="Valor de Retorno")
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

```c
{function_info['signature']}
```

## Descrição

{function_info['description']}

## Parâmetros
"""

        for param in function_info.get("parameters", []):
            md_content += f"\n### {param['name']}\n{param['description']}\n"

        if function_info.get("return_description"):
            md_content += (
                f"\n## Valor de Retorno\n\n{function_info['return_description']}"
            )

        return md_content
