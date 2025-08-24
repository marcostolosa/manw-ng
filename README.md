# MANW-NG

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

**Dynamic Windows API documentation scraper for reverse engineers and security researchers.**

MANW-NG extracts comprehensive documentation from Microsoft Learn for Win32 API, Native API (Nt*/Zw*), WDK/DDI, and UI Controls.

![MANW-NG running alongside radare2 in tmux](/assets/demo.png)
*MANW-NG integrated workflow with radare2 - perfect for reverse engineering sessions*

## Features

- **Comprehensive Coverage**: Win32 API, Native API (Nt*/Zw*), WDK/DDI, UI Controls
- **Intelligent Discovery**: 354+ URL pattern matching with function-specific header mapping
- **Rate Limit Bypass**: Multiple user agents with randomized delays
- **Multiple Output Formats**: Rich terminal, JSON, Markdown
- **Bilingual Support**: English and Portuguese documentation

## Installation

```bash
git clone https://github.com/marcostolosa/manw-ng.git
cd manw-ng
pip install -r requirements.txt
```

## Quick Start

```bash
# Win32 API functions
./manw-ng.py CreateProcessW
./manw-ng.py VirtualAlloc
./manw-ng.py RegOpenKeyEx

# Native API functions  
./manw-ng.py NtAllocateVirtualMemory
./manw-ng.py ZwCreateFile

# UI and graphics functions
./manw-ng.py CreateToolbarEx
./manw-ng.py GetStockObject
```

## Advanced Usage

```bash
# JSON output for automation
./manw-ng.py CreateProcessW --output json

# Portuguese documentation
./manw-ng.py CreateProcessW -l br

# Custom User-Agent
./manw-ng.py CreateProcessW -u "MyTool/1.0"
```

## Command Line Options

```
positional arguments:
  function_name         Windows function name (e.g., CreateProcessW)

options:
  -l {br,us}           Language: 'br' for Portuguese, 'us' for English
  --output FORMAT      Output format: rich, json, or markdown  
  -u USER_AGENT        Custom User-Agent header
  --version           Show version and exit
```

## Integration with RE Tools

MANW-NG is designed to integrate seamlessly with your reverse engineering workflow:

- **radare2**: Use alongside r2 for live API documentation lookup
- **Ghidra**: Export function lists and batch query documentation
- **x64dbg**: Quick API reference during debugging sessions
- **IDA Pro**: Script integration for automated documentation retrieval

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by the original [MANW](https://github.com/leandrofroes/manw) project by [@leandrofroes](https://github.com/leandrofroes)
- Built for the reverse engineering and security research community
- Developed with Claude AI assistance using iterative refinement