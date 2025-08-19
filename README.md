# Win32 API Documentation Scraper 🔧

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macos-lightgrey)](https://github.com/your-username/win32-api-scraper)

A **revolutionary tool** for reverse engineers and Windows developers to extract detailed information about Win32 API functions directly from Microsoft's official documentation.

## ✨ Features

- 🌐 **Multi-language support**: English and Portuguese documentation
- 📝 **Precise extraction**: Function signatures from exact HTML elements (`has-inner-focus` divs)
- 📋 **Detailed parameters**: Complete parameter descriptions with types and directions
- 🎯 **Return values**: Comprehensive return value documentation
- 🎨 **Rich output**: Beautiful terminal output with syntax highlighting
- 🔍 **Smart search**: Automatic function discovery with fallback mechanisms
- ⚡ **Fast & reliable**: Efficient scraping with error handling

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
python win32_scraper.py CreateProcessW

# Extract MessageBoxA documentation in Portuguese
python win32_scraper.py MessageBoxA -l br

# Get help
python win32_scraper.py -h
```

### Command Line Options

```
usage: win32_scraper.py [-h] [-l {br,us}] [--output {rich,json,markdown}] function_name

positional arguments:
  function_name         Win32 function name (e.g., CreateProcessW)

optional arguments:
  -h, --help            show this help message and exit
  -l {br,us}, --language {br,us}
                        Documentation language: 'br' for Portuguese or 'us' for English (default: us)
  --output {rich,json,markdown}
                        Output format (default: rich)
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

### Pre-mapped Functions (25+)
<details>
<summary>View complete list of optimized functions</summary>

- `CreateProcessW` - Process creation
- `CreateFileA/W` - File operations
- `MessageBoxA/W` - User interface
- `ReadFile/WriteFile` - File I/O
- `VirtualAlloc/VirtualFree` - Memory management
- `LoadLibrary/GetProcAddress` - DLL operations
- `FindWindow/ShowWindow` - Window management
- `OpenProcess/TerminateProcess` - Process control
- `GetSystemInfo` - System information
- `CloseHandle` - Handle management
- And more...

</details>

## 📸 Example Output

### English Documentation
```bash
python win32_scraper.py CreateProcessW -l us
```

```
┌─ Win32 API Function ─┐
│   CreateProcessW     │
└──────────────────────┘

        Basic Information        
┌────────────────────────────────┐
│ Property           │ Value     │
├────────────────────┼───────────┤
│ DLL               │ Kernel32.dll │
│ Calling Convention │ __stdcall    │
│ Parameters        │ 10           │
│ Architectures     │ x86, x64     │
│ Return Type       │ BOOL         │
└────────────────────────────────┘

┌────────── Function Signature ──────────┐
│ BOOL CreateProcessW(                    │
│   [in, optional]      LPCWSTR lpAppName│
│   [in, out, optional] LPWSTR lpCmdLine │
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
requests>=2.28.0      # HTTP client for web scraping
beautifulsoup4>=4.11.0 # HTML parsing
rich>=12.0.0          # Terminal formatting and colors
lxml>=4.9.0           # Fast XML/HTML parser
```

## 📝 Output Formats

### Rich (Default)
Beautiful terminal output with colors, tables, and syntax highlighting.

### JSON
```bash
python win32_scraper.py CreateProcessW --output json > createprocessw.json
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
python win32_scraper.py CreateProcessW -l us

# Portuguese documentation  
python win32_scraper.py CreateProcessW -l br
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