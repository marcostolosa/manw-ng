# MANW-NG

![](https://github.com/qtc-de/wconv/workflows/master/badge.svg)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Advanced Windows API documentation discovery with AI-powered classification**

Multi-layered Windows API documentation tool with ML classification, Microsoft Learn Search integration, and intelligent URL discovery for reverse engineers and security researchers.

![](/assets/demo.png)

## System Architecture

MANW-NG uses a 6-priority pipeline for comprehensive API discovery:

```
Special Cases → Smart URL → MS Learn Search → ML Fallback → Local DB → A/W Suffix
    <1s           <3s           3-8s            8-15s         <1s       +5-10s
   100%           85%            10%              3%            1%         1%
```

## Installation

```bash
git clone https://github.com/marcostolosa/manw-ng.git
cd manw-ng
pip install -r requirements.txt
```

## Usage

### Basic Examples
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
```

### Command Options
```
./manw-ng.py <function_name> [-l br|us] [-o rich|json|markdown] [-O] [-u USER_AGENT]

-l {br,us}               Language (default: us)
-o {rich,json,markdown}  Output format (default: rich)  
-O, --obs                Show remarks/observations
-u USER_AGENT            Custom User-Agent
--version                Show version
```

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
│   └── output/         # Rich, JSON, Markdown formatters
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

## Related Tools

- [API Monitor](http://www.rohitab.com/apimonitor) - Monitor API calls in real-time
- [WinAPIOverride](http://jacquelin.potier.free.fr/winapioverride32/) - Advanced API monitoring  
- [PEiD](https://www.aldeid.com/wiki/PEiD) - PE file analyzer with API detection
- [Dependency Walker](http://www.dependencywalker.com/) - DLL dependency analysis

## Acknowledgments

- Enhanced database integration using official Microsoft WinAPI documentation
- Microsoft Learn Search API integration for comprehensive coverage
- Performance optimizations inspired by modern reverse engineering tools
- Built with support from Claude AI for iterative development and testing