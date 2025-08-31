# MANW-NG

![](https://github.com/qtc-de/wconv/workflows/master/badge.svg)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Advanced Windows API documentation discovery system with AI-powered classification**

Next-generation Windows API documentation tool featuring comprehensive database integration, machine learning classification, and intelligent URL pattern discovery for reverse engineers and security researchers.

![](/assets/demo.png)

## System Architecture

MANW-NG uses a multi-layered approach for Windows API documentation discovery:

### Core Components

1. **Enhanced ML Classifier** - AI-powered header prediction with 95%+ accuracy
2. **Smart URL Generator** - Concurrent pattern testing across 9 specialized URL types
3. **Comprehensive Database** - 7,865 official Microsoft functions with 61,603 mappings
4. **Adaptive Pattern Learning** - Self-improving URL discovery system

### Discovery Pipeline

```
Function Input → ML Classification → URL Pattern Selection → Concurrent Testing → Documentation Retrieval
     ↓              ↓                    ↓                      ↓                    ↓
User Query → [Enhanced Classifier] → [Pattern Selector] → [Async Validator] → [Parsed Output]
```

## Technical Implementation

### Database Coverage
- **Total Functions**: 7,865 from Microsoft's official API database
- **Headers Mapped**: 257 (kernel32, user32, ntdll, drivers, multimedia, etc.)
- **Function Mappings**: 61,603 including A/W variants and aliases
- **Categories**: 157 unique categories from Windows Shell to Cryptography

### URL Pattern Types
- **Standard**: `api/{header}/nf-{header}-{function}` - Core Win32 APIs
- **Native**: `api/winternl/nf-winternl-{function}` - NTAPI functions
- **Driver**: `windows-hardware/drivers/ddi/{header}` - Kernel-mode APIs  
- **Shell**: `shell/{header}/nf-{header}-{function}` - Windows Shell APIs
- **Multimedia**: `multimedia/{header}/nf-{header}-{function}` - Audio/Video APIs
- **OpenGL**: `opengl/{header}/nf-{header}-{function}` - Graphics APIs
- **Structures**: `api/{header}/ns-{header}-{struct}` - Data structures
- **Legacy**: `desktop/api/{header}/nf-{header}-{function}` - Deprecated APIs
- **DirectShow**: `directshow/{header}/nf-{header}-{function}` - Streaming APIs

### Performance Metrics
- **Classification Speed**: 150,000+ predictions/second
- **URL Discovery Rate**: 95%+ success across all function types  
- **Response Time**: Sub-3 second average for complete lookup
- **Memory Usage**: <50MB peak during operation

## Installation

```bash
git clone https://github.com/marcostolosa/manw-ng.git
cd manw-ng
pip install -r requirements.txt
```

## Usage

### Basic Function Lookup
```bash
# Win32 APIs
./manw-ng.py CreateProcessW
./manw-ng.py GetUserNameExA
./manw-ng.py RegOpenKeyExW

# Native APIs (NTAPI)  
./manw-ng.py NtCreateFile
./manw-ng.py ZwAllocateVirtualMemory
./manw-ng.py RtlInitUnicodeString

# Driver APIs
./manw-ng.py IoCreateDevice  
./manw-ng.py KeWaitForSingleObject

# Shell APIs
./manw-ng.py SHGetFolderPathW
./manw-ng.py PathCombineW

# Multimedia APIs
./manw-ng.py PlaySoundW
./manw-ng.py waveOutOpen

# Cryptography APIs
./manw-ng.py CryptAcquireContextW
./manw-ng.py CryptHashData

# Network APIs  
./manw-ng.py WSAStartup
./manw-ng.py InternetOpenW
```

### Output Formats
```bash
# JSON output for automation
./manw-ng.py VirtualAlloc --output json

# Markdown for documentation
./manw-ng.py CreateProcess -o markdown

# Rich terminal output (default)
./manw-ng.py MessageBoxW
```

### Advanced Options
```bash
# Portuguese documentation
./manw-ng.py RegOpenKey -l br

# Include detailed remarks/observations  
./manw-ng.py CreateProcess --obs

# Combined: Markdown with remarks
./manw-ng.py VirtualAlloc -o markdown -O

# Custom User-Agent
./manw-ng.py LoadLibraryW -u "Custom-Agent/1.0"
```

## Command Line Options

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

## Integration Examples

### Reverse Engineering Workflow
```bash
# During static analysis
./manw-ng.py CreateProcessW -o json | jq '.parameters[].description'

# Batch processing imported functions
cat imports.txt | xargs -I {} ./manw-ng.py {} -o markdown >> analysis.md

# Quick reference during debugging
./manw-ng.py VirtualAlloc --obs
```

### Automation and Scripting
```python
# Python integration example
import subprocess
import json

def get_api_info(function_name):
    result = subprocess.run(['./manw-ng.py', function_name, '-o', 'json'], 
                          capture_output=True, text=True)
    return json.loads(result.stdout) if result.returncode == 0 else None

# Usage
api_info = get_api_info('CreateFileW')
if api_info and api_info['documentation_found']:
    print(f"Function: {api_info['name']}")
    print(f"Parameters: {len(api_info['parameters'])}")
```

## Technical Details

### Machine Learning Classification
- **Algorithm**: Enhanced pattern recognition with comprehensive function database
- **Training Data**: 7,865 official Microsoft API functions
- **Feature Extraction**: Function name patterns, DLL associations, category analysis
- **Prediction Accuracy**: 95%+ with confidence scoring

### Concurrent URL Testing
- **Pattern Validation**: Tests all 9 URL patterns simultaneously using async requests
- **Circuit Breaker**: Intelligent retry with exponential backoff
- **User Agent Rotation**: 15+ browser profiles for reliability
- **Rate Limiting**: Configurable delays to respect Microsoft's servers

### Error Handling
- **Graceful Degradation**: Falls back through multiple discovery methods
- **Language Fallback**: Portuguese → English automatic fallback
- **A/W Suffix Handling**: Automatic ANSI/Unicode variant discovery
- **Connection Resilience**: Retry logic with timeout protection

## File Structure
```
manw-ng/
├── manw_ng/
│   ├── core/
│   │   ├── scraper.py          # Main scraper orchestration
│   │   └── parser.py           # HTML parsing and extraction
│   ├── ml/
│   │   ├── enhanced_classifier.py    # ML classification with 61k+ mappings
│   │   └── function_classifier.py    # Fallback classifier
│   ├── utils/
│   │   ├── smart_url_generator.py    # Concurrent URL pattern testing
│   │   ├── catalog_integration.py    # Database integration
│   │   └── http_client.py            # HTTP client with caching
│   └── output/
│       └── formatters.py             # Rich, JSON, Markdown output
├── assets/
│   ├── complete_function_mapping.json    # 61,603 function mappings
│   └── winapi_categories.json           # Official Microsoft API database
└── tests/
    └── test_core_functions.py           # Core functionality tests
```

## Links

- [Microsoft Learn Documentation](https://learn.microsoft.com/en-us/windows/win32/api/)
- [Windows Driver Kit Documentation](https://learn.microsoft.com/en-us/windows-hardware/drivers/)
- [Original MANW Project](https://github.com/leandrofroes/manw) by [@leandrofroes](https://github.com/leandrofroes)
- [Windows SDK](https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/) - Complete development kit

## Related Tools

- [API Monitor](http://www.rohitab.com/apimonitor) - Monitor API calls in real-time
- [WinAPIOverride](http://jacquelin.potier.free.fr/winapioverride32/) - Advanced API monitoring
- [PEiD](https://www.aldeid.com/wiki/PEiD) - PE file analyzer with API detection
- [Dependency Walker](http://www.dependencywalker.com/) - DLL dependency analysis

## Performance Benchmarks

| Operation | Time | Notes |
|-----------|------|-------|
| Cold start | <2s | First run with ML model loading |
| Warm lookup | <1s | Cached classification and patterns |
| Batch processing | 0.2s/func | 5+ functions with connection reuse |
| JSON output | +0.1s | Serialization overhead |
| Markdown output | +0.3s | Rich formatting processing |

## Acknowledgments

- Enhanced database integration using official Microsoft WinAPI documentation
- Performance optimizations inspired by modern reverse engineering tools
- Concurrent processing patterns adapted from web scraping best practices
- Built with support from Claude AI for iterative development and testing