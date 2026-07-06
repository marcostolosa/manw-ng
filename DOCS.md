# MANW-NG Documentation

## System Architecture

MANW-NG uses a 5-step pipeline for comprehensive API discovery, tried in order until one
succeeds (special cases and a known-undocumented-API denylist are checked first, as
instant fast exits, before step 1):

```
1. MS Learn Search API   → official search, highest reliability
2. Smart URL Generation  → pattern-based candidate URLs + validation
3. Heuristic Classifier  → dictionary + regex header prediction fallback
4. Internal Catalog      → curated backup dataset
5. Offline JSON Mapping  → local function→header mapping, for offline/fast access
Final: A/W suffix retry  → if the plain name failed, try the A/W variant (or vice versa)
```

Note: the "heuristic classifier" here (`enhanced_classifier.py`) is a large hardcoded
function→header dictionary plus keyword/regex matching, not a trained ML model — see
"Function Classification" below.

## Technical Implementation

### Database Coverage
- **Total Functions**: ~7,866 official Microsoft functions
- **Function Mappings**: 61,000+ including A/W variants and aliases
- **Headers Mapped**: 257 (kernel32, user32, ntdll, drivers, etc.)
- **Categories**: 157 unique API categories

### Function Classification

`manw_ng/ml/enhanced_classifier.py` is the classifier actually used by default
(`primary_classifier` in `manw_ng/ml/__init__.py`). It's a hardcoded
function→header mapping dictionary plus a reverse index built from
`manw_ng/assets/complete_function_mapping.json`, with keyword/regex heuristics and
hand-assigned confidence scores — no training involved. `manw_ng/ml/function_classifier.py`
is a real scikit-learn classifier (TF-IDF + MultinomialNB + RandomForest) with an
online-learning design that persists to `~/.cache/manw-ng/ml_models/*.pkl`; no model
ships in the repo, so on a fresh install it's untrained and contributes nothing until
it has learned from enough successful lookups at runtime.

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
│   ├── ml/             # Heuristic classification + optional trainable ML fallback
│   ├── utils/          # Smart URL generation and HTTP client
│   ├── output/         # Rich, JSON, Markdown formatters
│   ├── execution/      # WinAPI execution engine
│   │   ├── engine.py   # DLL/function resolution + ctypes call
│   │   ├── types.py    # Argument/return-type parsing
│   │   └── memory.py   # Buffer tracking + hexdump
│   └── assets/
│       ├── complete_function_mapping.json    # 61,000+ function mappings
│       └── winapi_categories.json           # Official API database
├── assets/
│   └── demo.png        # README screenshot (not used by any code)
└── tests/              # pytest suite (formatters, dll_map, scraper, execution engine)
```

## Execution Features

Implemented in `manw_ng/execution/` (`types.py` for argument/return-type parsing,
`memory.py` for buffer tracking + hexdump, `engine.py` for DLL/function resolution
and the actual `ctypes` call):

### Safety
- **Parameter Validation**: malformed buffer sizes (`$b:`) and unknown `--ret` types
  are rejected with a clear error before any DLL is touched.
- **Buffer Size Guard**: `$b:` allocations are capped at 64 MiB to avoid
  accidental/malicious huge allocations from a typo'd size.
- **A/W Auto-Resolution**: tries the exact name, then the `W` variant, then the `A`
  variant (or only `W`, if `--wide` is passed).

### Advanced Features
- **Module Abbreviations**: `k`/`u`/`n`/`a32`/`g`/`ws2`/`sh`, or any `name`/`name.dll`.
- **Buffer Hexdump**: `$b:` buffer arguments are hexdumped (offset/hex/ASCII) after
  the call, showing whatever the API wrote into them.
- **GetLastError Integration**: `--show-error` reports `GetLastError()` +
  `FormatMessage`-equivalent text (`ctypes.FormatError`) after the call.

### Parameter Types
- `123` / `-5` - Auto-detected integer (32 or 64-bit signed/unsigned, based on value)
- `0x1000` - Hexadecimal values (same width rule as decimal)
- `"text"` / `text` - Unicode strings (`LPCWSTR`), quotes optional
- `$s:text` - ANSI string (`LPCSTR`)
- `$b:size` - Zeroed, writable buffer of `size` bytes (hexdumped after the call)

## Links

- [Microsoft Learn Documentation](https://learn.microsoft.com/en-us/windows/win32/api/)
- [Windows Driver Kit Documentation](https://learn.microsoft.com/en-us/windows-hardware/drivers/)
- [Windows SDK](https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/) - Complete development kit
- [Original MANW Project](https://github.com/leandrofroes/manw) by [@leandrofroes](https://github.com/leandrofroes)

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