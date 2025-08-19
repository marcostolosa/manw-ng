# MANW-NG: Win32 API Documentation Scraper (Next Generation) 🚀

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macos-lightgrey)](https://github.com/marcostolosa/manw-ng)

A **revolutionary modular tool** for reverse engineers and Windows developers to extract detailed information about Win32 API functions directly from Microsoft's official documentation.

## ✨ Features

- 🏗️ **Modular Architecture**: Clean, maintainable codebase with separated concerns
- 🌐 **Multi-language support**: English and Portuguese documentation with automatic fallback
- 🔍 **Intelligent Discovery**: Multi-stage discovery pipeline finds ANY Win32 function
- 📝 **Precise extraction**: Function signatures from exact HTML elements
- 📋 **Detailed parameters**: Complete parameter descriptions with types and directions
- 🎯 **Return values**: Comprehensive return value documentation
- 🎨 **Rich Status**: Dynamic progress display with animated spinner
- ⚡ **100+ Known Functions**: Pre-mapped functions for reverse engineering and malware analysis
- 🚀 **Expert Techniques**: Based on reverse engineering best practices

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/marcostolosa/manw-ng.git
cd manw-ng

# Install dependencies
pip install -r requirements.txt
```

## 💻 Usage

### Basic Usage

```bash
# Extract CreateProcessW documentation in English
python manw-ng.py CreateProcessW

# Extract MessageBoxA documentation in Portuguese
python manw-ng.py MessageBoxA -l br

# Get help
python manw-ng.py -h
```

### Command Line Options

```
usage: manw-ng.py [-h] [-l {br,us}] [--output {rich,json,markdown}] [--version] function_name

MANW-NG - Win32 API Documentation Scraper (Next Generation)

positional arguments:
  function_name         Nome da função Win32 para fazer scraping (ex: CreateProcessW, VirtualAlloc)

options:
  -h, --help            show this help message and exit
  -l {br,us}, --language {br,us}
                        Idioma da documentação: 'br' para português ou 'us' para inglês (padrão: us)
  --output {rich,json,markdown}
                        Formato de saída (padrão: rich)
  --version             show program's version number and exit
```

## 🎯 Perfect for Reverse Engineers

This tool is specifically designed for reverse engineers who need:

- **Quick API reference**: Instant access to function documentation
- **Parameter analysis**: Detailed parameter information for malware analysis
- **Return value understanding**: Complete success/failure conditions
- **Multi-language support**: Work with localized documentation
- **Batch processing**: JSON output for automated workflows

## 📋 Supported Functions

The tool supports **all Win32 API functions** documented on Microsoft Learn, including:

- **Process and Thread Management** (`CreateProcessW`, `OpenProcess`, etc.)
- **File Operations** (`CreateFile`, `ReadFile`, `WriteFile`, etc.)  
- **Window Management** (`MessageBox`, `FindWindow`, `ShowWindow`, etc.)
- **Memory Management** (`VirtualAlloc`, `VirtualFree`, etc.)
- **Registry Operations** (`RegOpenKey`, `RegQueryValue`, etc.)
- **And many more...**

### Pre-mapped Functions (100+)
<details>
<summary>View complete list of optimized functions for reverse engineering</summary>

**Process/Thread Management (19 functions)**
- `CreateProcess`, `OpenProcess`, `TerminateProcess`
- `CreateThread`, `SuspendThread`, `ResumeThread`
- `GetCurrentProcess`, `WaitForSingleObject`, etc.

**Memory Management (15 functions)**  
- `VirtualAlloc`, `VirtualProtect`, `ReadProcessMemory`
- `WriteProcessMemory`, `HeapAlloc`, `GlobalAlloc`, etc.

**File Operations (20 functions)**
- `CreateFile`, `ReadFile`, `WriteFile`, `DeleteFile`
- `CopyFile`, `MoveFile`, `FindFirstFile`, etc.

**Registry (10 functions)**
- `RegOpenKeyEx`, `RegCreateKey`, `RegSetValueEx`
- `RegQueryValueEx`, `RegDeleteKey`, etc.

**Network (10 functions)**
- `WSAStartup`, `socket`, `connect`, `send`, `recv`, etc.

**And many more categories...**

</details>

## 📸 Example Output

### English Documentation
```bash
python manw-ng.py CreateProcessW -l us
```

```
┌─ Win32 API Function ─┐
│   CreateProcessW     │
└──────────────────────┘

        Basic Information        
┌───────────────────────────────────┐
│ Property           │ Value        │
├────────────────────┼──────────────┤
│ DLL                │ Kernel32.dll │
│ Calling Convention │ __stdcall    │
│ Parameters         │ 10           │
│ Architectures      │ x86, x64     │
│ Return Type        │ BOOL         │
└───────────────────────────────────┘

┌────────── Function Signature ───────────┐
│ BOOL CreateProcessW(                    │
│   [in, optional]      LPCWSTR lpAppName │
│   [in, out, optional] LPWSTR lpCmdLine  │
│   ...                                   │
│ );                                      │
└─────────────────────────────────────────┘

                Parameters                
┌─────────────────────────────────────────┐
│ Name              │ Description         │
├───────────────────┼─────────────────────┤
│ lpApplicationName │ The name of module  │
│                   │ to be executed...   │
└─────────────────────────────────────────┘
```

## 🏗️ Technical Details

### Architecture

- **Smart URL Construction**: Uses known function mappings for direct access
- **Fallback Search**: Implements dynamic search when direct URLs fail
- **Revolutionary HTML Parsing**: Targets specific HTML elements for accurate extraction
- **Error Handling**: Graceful degradation with multiple extraction strategies

### Extraction Strategy

1. **Signature**: Extracts from `div.has-inner-focus` elements
2. **Parameters**: Revolutionary sequential text parsing in Parameters sections
3. **Return Values**: Locates dedicated Return Value sections with complete descriptions
4. **Metadata**: Extracts DLL, types, and architectural information

## 🛠️ Dependencies

```
requests>=2.28.0          # HTTP client for web scraping
beautifulsoup4>=4.11.0    # HTML parsing
rich>=12.0.0              # Terminal formatting and colors
lxml>=4.9.0               # Fast XML/HTML parser
```

## 📝 Output Formats

### Rich (Default)
Beautiful terminal output with colors, tables, and syntax highlighting.

### JSON
```bash
python manw-ng.py CreateProcessW --output json > createprocessw.json
```

Perfect for automation and integration with other tools:

```json
{
  "name": "CreateProcessW",
  "dll": "Kernel32.dll",
  "calling_convention": "__stdcall",
  "parameters": [...],
  "return_type": "BOOL",
  "signature": "BOOL CreateProcessW(...)",
  "description": "Creates a new process..."
}
```

## 🌐 Multi-Language Support

```bash
# English documentation (default)
python manw-ng.py CreateProcessW -l us

# Portuguese documentation  
python manw-ng.py CreateProcessW -l br
```

Access documentation in your preferred language:
- 🇺🇸 **English** (`-l us`): `https://learn.microsoft.com/en-us`
- 🇧🇷 **Portuguese** (`-l br`): `https://learn.microsoft.com/pt-br`

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup
```bash
git clone https://github.com/marcostolosa/manw-ng.git
cd manw-ng
pip install -r requirements-dev.txt
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Use Cases

### For Reverse Engineers
- **Malware Analysis**: Understand API calls in suspicious binaries
- **Binary Analysis**: Quick reference for function parameters and return values
- **Dynamic Analysis**: Understand API behavior during runtime analysis

### For Developers
- **API Reference**: Quick access to Win32 documentation
- **Code Documentation**: Generate API documentation for projects
- **Learning**: Study Win32 API functions with detailed explanations

## ⭐ Star History

If this tool helped you with your reverse engineering or development work, please consider giving it a star!

## 🔗 Related Projects and Inspirations

- [manw](https://github.com/leandrofroes/manw) - Original manw tool from @leandrofroes
- [API Monitor](https://github.com/rohitab/API-Monitor) - API monitoring and hooking
- [Process Hacker](https://github.com/processhacker/processhacker) - System information tool
- [x64dbg](https://github.com/x64dbg/x64dbg) - Windows debugger

---

**Made with ❤️ for the reverse engineering community**

**🚀 Revolutionary extraction • 🌐 Multi-language • ⚡ Fast & reliable**
