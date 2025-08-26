# MANW-NG

![](https://github.com/qtc-de/wconv/workflows/master/badge.svg)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Dynamic Windows API documentation scraper for reverse engineers**

Professional-grade Windows API documentation tool with intelligent pattern matching and elegant interface.

![MANW-NG running alongside radare2 in tmux](/assets/demo.png)
_MANW-NG integrated workflow with radare2 on tmux - perfect for debugging sessions_

## Features

- **Comprehensive Coverage**: Win32 API, Native API (Nt*/Zw*), COM, Shell APIs
- **Intelligent Discovery**: Smart URL pattern matching with 500+ patterns  
- **Rate Limit Bypass**: Multiple user agents with randomized delays
- **Multi-format Output**: Rich terminal, JSON, Markdown formats
- **Multilingual**: English and Portuguese documentation support

## Installation

```bash
git clone https://github.com/marcostolosa/manw-ng.git
cd manw-ng
pip install -r requirements.txt
```

## Usage

```bash
# Basic lookup
./manw-ng.py CreateProcessW
./manw-ng.py NtAllocateVirtualMemory

# JSON output
./manw-ng.py VirtualAlloc --output json

# Portuguese docs
./manw-ng.py RegOpenKey -l br

# Include remarks/observations
./manw-ng.py CreateProcess --obs

# Markdown with remarks
./manw-ng.py VirtualAlloc -o markdown -O
```

## Options

```
usage: manw-ng.py [-h] [-l {br,us}] [-o {rich,json,markdown}] [-O] [-u USER_AGENT] [--version] function_name

positional arguments:
  function_name            Windows function name

options:
  -l {br,us}               Language (default: us)
  -o {rich,json,markdown}  Output format (default: rich)
  -O, --obs                Show remarks/observations (default: hide)
  -u USER_AGENT            Custom User-Agent
  --version                Show version
```

## Integration with RE Tools

MANW-NG is designed to integrate seamlessly with your reverse engineering workflow:

- **radare2**: Use alongside r2 for live API documentation lookup
- **Ghidra**: Export function lists and batch query documentation
- **x64dbg**: Quick API reference during debugging sessions
- **IDA Pro**: Script integration for automated documentation retrieval

## Acknowledgments

- Inspired by the original [MANW](https://github.com/leandrofroes/manw) project by [@leandrofroes](https://github.com/leandrofroes)
- Built for the reverse engineering and security research community
- Developed with Claude AI assistance using iterative refinement

## Related Tools

- [API Monitor](http://www.rohitab.com/apimonitor) - monitor and control API calls made by applications and services
- [WinAPIOverride](http://jacquelin.potier.free.fr/winapioverride32/) - advanced api monitoring software