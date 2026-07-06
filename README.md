# MANW-NG

![](https://github.com/qtc-de/wconv/workflows/master/badge.svg)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Windows API documentation scraping with heuristic classification + WinAPI Execution**

Multi-layered Windows API documentation tool with a 61k+ function→header mapping database, Microsoft Learn Search integration, intelligent URL discovery, and a Windows API execution engine for reverse engineers and security researchers.

![](/assets/demo.png)

## Installation

```bash
git clone https://github.com/marcostolosa/manw-ng.git
cd manw-ng
pip install -e .
```

This installs a `manw-ng` console command in addition to running the script directly
(`./manw-ng.py ...` below still works the same way).

## Usage

### Documentation Mode
```bash
# Basic usage
./manw-ng.py CreateProcessW
./manw-ng.py VirtualAlloc
./manw-ng.py RegOpenKeyExW

# Portuguese documentation
./manw-ng.py -l br NtCreateFile

# Show parameter value tables (hidden by default)
./manw-ng.py NtCreateFile -l br --tabs

# Output formats
./manw-ng.py VirtualAlloc -o json
./manw-ng.py CreateFile -o markdown
```

### WinAPI Execution Mode
```bash
# Execute Windows APIs directly
./manw-ng.py exec kernel32:Beep 750 300
./manw-ng.py exec u:MessageBoxW 0 "Hello World" "MANW-NG" 0
./manw-ng.py exec user32:FindWindowW "Notepad" 0

# Module abbreviations supported (k, u, n, a32, g, ws2, sh, or any dll name)
./manw-ng.py exec k:GetTickCount

# $b:size allocates a zeroed, writable buffer and hexdumps it after the call
./manw-ng.py exec u:GetCursorPos '$b:8'

# Control the return type, force the wide (W) variant, and report GetLastError
./manw-ng.py exec k:GetCurrentProcessId --ret u32
./manw-ng.py exec u:FindWindowW Notepad 0 --wide
./manw-ng.py exec k:OpenProcess 0x0400 0 99999 --show-error
```

## Command Options

### Documentation Mode
```
./manw-ng.py <function_name> [-l br|us] [-o rich|json|markdown] [-O] [-t] [-u USER_AGENT]

-l {br,us}               Language (default: us)
-o {rich,json,markdown}  Output format (default: rich)  
-O, --obs                Show remarks/observations
-t, --tabs               Show parameter value tables (default: hidden)
-u USER_AGENT            Custom User-Agent
--version                Show version
```

### Execution Mode
```
./manw-ng.py exec <dll:function> [arguments...] [options]

--ret TYPE               Return type (void, u32, i32, u64, i64, bool, ptr)
--wide                   Force Wide (W) variant
--show-error             Show GetLastError/FormatMessage
```

## Key Features

- **Multi-layered Search**: 5-step pipeline for comprehensive API discovery (official search, pattern-based URL generation, heuristic classification, internal catalog, offline JSON mapping)
- **Function Mapping Database**: 61,000+ function→header mappings with heuristic classification (dictionary + regex, not a trained model)
- **Parameter Tables**: Categorized value tables for complex parameters (--tabs flag)
- **WinAPI Execution**: Real `ctypes`-backed Windows API execution — typed return values, buffer allocation with hexdump, `GetLastError` reporting
- **Multi-language**: English and Portuguese documentation support
- **Multiple Formats**: Rich terminal, JSON, and Markdown output (all three respect the selected language)

## Documentation

For detailed technical documentation, see [DOCS.md](DOCS.md).

## Related Tools

- [winapiexec](https://github.com/m417z/winapiexec) - Original WinAPI execution tool 
- [Original MANW Project](https://github.com/leandrofroes/manw) by [@leandrofroes](https://github.com/leandrofroes)

## License

MIT License - see LICENSE file for details.