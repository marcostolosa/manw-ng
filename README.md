# MANW-NG

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

A command-line tool for extracting Windows API documentation from Microsoft Learn. Designed for reverse engineers, malware analysts, and Windows developers who need programmatic access to API documentation.

![](/assets/demo.png)

## Features

- **Comprehensive API Coverage**: Win32 API, Native API (Nt*/Zw*), WDK/DDI, and UI Controls
- **Multiple Output Formats**: Terminal (rich), JSON, and Markdown
- **Intelligent Discovery**: Pattern-based URL generation with function-specific header mapping
- **Rate Limit Handling**: Multiple user agents with randomized delays
- **Bilingual Support**: English and Portuguese documentation
- **Cross-platform**: Works on Linux, macOS, and Windows

## Installation

### From Source

```bash
git clone https://github.com/marcostolosa/manw-ng.git
cd manw-ng
pip install -r requirements.txt
```

## Usage

### Basic Examples

```bash
# Win32 API functions
./manw-ng.py CreateProcessW
./manw-ng.py GetCommandLineA
./manw-ng.py VirtualAlloc

# Native API functions
./manw-ng.py NtAllocateVirtualMemory
./manw-ng.py ZwCreateFile

# UI and graphics functions
./manw-ng.py CreateToolbarEx
./manw-ng.py GetStockObject
```

### Output Formats

```bash
# JSON output for automation
./manw-ng.py CreateProcessW --output json

# Markdown for documentation
./manw-ng.py CreateProcessW --output markdown

# Portuguese documentation
./manw-ng.py CreateProcessW -l br
```

### Command Line Options

```
usage: manw-ng.py [-h] [-l {br,us}] [--output {rich,json,markdown}] 
                  [-u USER_AGENT] [--version] function_name

positional arguments:
  function_name         Windows function name (e.g., CreateProcessW, VirtualAlloc)

options:
  -h, --help           show this help message and exit
  -l {br,us}           language: 'br' for Portuguese, 'us' for English (default: us)
  --output FORMAT      output format: rich, json, or markdown (default: rich)
  -u USER_AGENT        custom User-Agent header (default: random)
  --version            show version number and exit
```

## Architecture

```
manw-ng/
├── manw_ng/
│   ├── core/           # Core scraping and parsing logic
│   ├── output/         # Output formatters (Rich, JSON, Markdown)
│   └── utils/          # URL generation and HTTP handling
├── tests/              # Test suite
└── .github/workflows/  # CI/CD pipelines
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Related Projects

- [WinAPIOverride](http://jacquelin.potier.free.fr/winapioverride32/) - API monitoring
- [API Monitor](http://www.rohitab.com/apimonitor) - API hooking tool

## Acknowledgments

- Inspired by the original [MANW](https://github.com/leandrofroes/manw) project
- Built for the reverse engineering and security research community
- Developed with Claude (Sonnet 4) assistance using iterative refinement