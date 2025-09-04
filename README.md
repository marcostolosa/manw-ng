# MANW-NG

![](https://github.com/qtc-de/wconv/workflows/master/badge.svg)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Windows API documentation scraping with AI-powered  + WinAPI Execution**

Multi-layered Windows API documentation tool with ML classification, Microsoft Learn Search integration, intelligent URL discovery, and Windows API execution engine.

![](/assets/demo.png)


## Installation

```bash
git clone https://github.com/marcostolosa/manw-ng.git
cd manw-ng
pip install -r requirements.txt
```

## Usage

### Documentation Mode
```bash
# Win32 APIs (Priority 1: <3s)
./manw-ng.py CreateProcessW
./manw-ng.py VirtualAlloc
./manw-ng.py RegOpenKeyExW

# C Runtime Functions (Special: <1s)  
./manw-ng.py memcpy
./manw-ng.py malloc

# Network APIs
./manw-ng.py WSAStartup
./manw-ng.py InternetOpenW

# Output formats
./manw-ng.py VirtualAlloc -o json
./manw-ng.py CreateFile -o markdown

# Show detailed parameter tables
./manw-ng.py NtCreateFile -l br -t
```

### WinAPI Execution Mode
```bash
# Execute Windows APIs directly - ultra-simple syntax
./manw-ng.py exec kernel32:Beep 750 300
./manw-ng.py exec u:MessageBoxW 0 "Hello World" "MANW-NG" 0
./manw-ng.py exec user32:FindWindowW "Notepad" 0 --ret ptr
./manw-ng.py exec --show-error k32:GetModuleHandleW "kernel32.dll" --ret ptr

# Module abbreviations supported (k=kernel32, u=user32, a32=advapi32, etc.)
./manw-ng.py exec k:GetTickCount --ret u32
./manw-ng.py exec u:GetCursorPos '$b:8' --ret bool
```

### Command Options

#### Documentation Mode
```
./manw-ng.py <function_name> [-l br|us] [-o rich|json|markdown] [-O] [-t] [-u USER_AGENT]

-l {br,us}               Language (default: us)
-o {rich,json,markdown}  Output format (default: rich)  
-O, --obs                Show remarks/observations
-t, --tabs               Show parameter value tables (default: hidden)
-u USER_AGENT            Custom User-Agent
--version                Show version
```

#### Execution Mode
```
./manw-ng.py exec <dll:function> [arguments...] [options]

--ret TYPE               Return type (void, u32, i32, u64, i64, bool, ptr)
--wide                   Force Wide (W) variant
--show-error             Show GetLastError/FormatMessage
```

### Parameter Types (ultra-simplified)
- `123` - Auto-detected integer (32 or 64-bit based on value)
- `0x1000` - Hexadecimal values
- `"text"` - Unicode strings (auto-detected)
- `text` - Unicode strings (no quotes needed)
- `$b:size` - Buffer allocation (with automatic hexdump)
- `$s:text` - ASCII string (if needed)
- Original winapiexec syntax still supported for compatibility

## Technical Implementation

### Database Coverage
- **Total Functions**: 7,865 official Microsoft functions
- **Function Mappings**: 61,603 including A/W variants and aliases
- **Headers Mapped**: 257 (kernel32, user32, ntdll, drivers, etc.)
- **Categories**: 157 unique API categories

### URL Pattern Types
- **Standard**: `api/{header}/nf-{header}-{function}` (Win32 APIs)
- **Native**: `api/winternl/nf-winternl-{function}` (NTAPI functions)
- **Driver**: `windows-hardware/drivers/ddi/{header}` (Kernel APIs)
- **C Runtime**: `cpp/c-runtime-library/reference/{function}` (CRT functions)
- **Legacy**: `desktop/api/{header}/nf-{header}-{function}` (Deprecated APIs)
- **Shell**: `shell/{header}/nf-{header}-{function}` (Windows Shell APIs)
- **Multimedia**: `multimedia/{header}/nf-{header}-{function}` (Audio/Video)
- **Structures**: `api/{header}/ns-{header}-{struct}` (Data structures)
- **DirectShow**: `directshow/{header}/nf-{header}-{function}` (Streaming)

## Integration Examples

### Automation
```bash
# JSON output for scripting
./manw-ng.py CreateProcessW -o json | jq '.parameters[].description'

# Batch processing
cat imports.txt | xargs -I {} ./manw-ng.py {} -o markdown >> analysis.md
```

### Python Integration
```python
import subprocess, json

def get_api_info(function_name):
    result = subprocess.run(['./manw-ng.py', function_name, '-o', 'json'], 
                          capture_output=True, text=True)
    return json.loads(result.stdout) if result.returncode == 0 else None

api_info = get_api_info('CreateFileW')
```

## File Structure
```
manw-ng/
├── manw_ng/
│   ├── core/           # Main scraper and parser
│   ├── ml/             # ML classification with 61k+ mappings  
│   ├── utils/          # Smart URL generation and HTTP client
│   ├── output/         # Rich, JSON, Markdown formatters
│   └── execution/      # WinAPI execution engine
│       ├── engine.py   # Main execution engine
│       ├── types.py    # Advanced type system
│       └── memory.py   # Smart memory management
├── assets/
│   ├── complete_function_mapping.json    # 61,603 function mappings
│   └── winapi_categories.json           # Official API database
└── tests/              # Core functionality tests
```

## Links

- [Microsoft Learn Documentation](https://learn.microsoft.com/en-us/windows/win32/api/)
- [Windows Driver Kit Documentation](https://learn.microsoft.com/en-us/windows-hardware/drivers/)
- [Windows SDK](https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/) - Complete development kit
- [Original MANW Project](https://github.com/leandrofroes/manw) by [@leandrofroes](https://github.com/leandrofroes)

## Execution Features

### Performance Optimizations
- **Function Caching**: Intelligent caching of resolved functions and modules
- **Memory Management**: Advanced memory management with automatic cleanup
- **Fast Resolution**: Sub-millisecond function resolution on subsequent calls

### Security & Safety
- **Parameter Validation**: Rigorous validation of all parameters
- **Memory Protection**: Safe buffer allocation with bounds checking  
- **Error Recovery**: Robust error handling and resource cleanup
- **Thread Safety**: Safe operation in multi-threaded environments

### Advanced Features
- **A/W Auto-Resolution**: Intelligent ANSI/Wide function variant selection
- **Module Abbreviations**: Support for winapiexec-style abbreviations
- **Buffer Hexdump**: Automatic hexdump of output buffers
- **GetLastError Integration**: Comprehensive error reporting

## Related Tools

- [winapiexec](https://github.com/m417z/winapiexec) - Original WinAPI execution tool 
- [API Monitor](http://www.rohitab.com/apimonitor) - Monitor API calls in real-time
- [WinAPIOverride](http://jacquelin.potier.free.fr/winapioverride32/) - Advanced API monitoring  
- [PEiD](https://www.aldeid.com/wiki/PEiD) - PE file analyzer with API detection
- [Dependency Walker](http://www.dependencywalker.com/) - DLL dependency analysis

## Acknowledgments

- Enhanced database integration using official Microsoft WinAPI documentation
- Microsoft Learn Search API integration for comprehensive coverage
- Performance optimizations inspired by modern reverse engineering tools
- Built with support from Claude AI for iterative development and testing