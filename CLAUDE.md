# CLAUDE.md

Guidance for Claude Code (and other agents) working in this repository.

## What this is

MANW-NG is a Python 3 CLI with two independent modes, invoked as `./manw-ng.py`
(or `manw-ng` after `pip install -e .`):

1. **Documentation mode** (default): scrapes Microsoft Learn to produce structured
   Win32/NTAPI/driver API documentation (signature, params, return value, remarks),
   in `rich` (terminal), `json`, or `markdown` output, in English or Portuguese.
2. **Execution mode** (`./manw-ng.py exec dll:function args... [--ret TYPE] [--wide]
   [--show-error]`): calls a Windows API directly via `ctypes` from the CLI.
   **Windows-only at runtime** (uses `ctypes.WinDLL`); documentation mode is
   cross-platform.

Entry points: [manw-ng.py](manw-ng.py) is a thin shim importing `main()` from
[manw_ng/cli.py](manw_ng/cli.py) — that's where both `main()` (doc mode) and
`handle_exec_fast()` (exec mode, checked before argparse even runs, for fast
startup) actually live.

## Dev environment (important, non-obvious)

- Host is **Windows 11**; the project lives inside **WSL (distro `kali-linux`)** at
  `/home/Tr0p/apps/manw-ng`, opened in VS Code via `\\wsl.localhost\kali-linux\...`.
- Execution mode's `ctypes.WinDLL` calls only work under Windows Python, not the
  WSL/Linux Python. There is a native Windows Python reachable from the same path
  (e.g. via PowerShell), which is what makes it possible to test exec mode for real
  rather than only through mocks.
- To run shell commands against the real project environment from a Windows-side
  agent, use `wsl -d kali-linux -e bash -lc "<cmd>"` (a plain `bash` tool invocation
  from the Windows side can fail with fork errors in this environment).
- `requirements.txt` lists `aiohttp` and `scikit-learn` as required; if a fresh WSL
  environment doesn't have them, `pip install -r requirements.txt` (or
  `pip install --break-system-packages ...` on externally-managed Debian/Kali Python).
- `pip install -e .` works (via `pyproject.toml`) and provides a `manw-ng` console
  command, in addition to running `./manw-ng.py` directly.

## Architecture

```
manw_ng/
  cli.py             main() (doc mode) + handle_exec_fast() (exec mode).
  core/
    scraper.py       Win32APIScraper — orchestrates the 5-step lookup pipeline.
    parser.py        BeautifulSoup-based HTML parser: name/DLL/signature/params/
                      return/remarks/struct-member extraction.
  ml/
    enhanced_classifier.py  ACTUAL primary classifier (see below) — large hardcoded
                             header-mapping dict + reverse lookup from
                             manw_ng/assets/complete_function_mapping.json +
                             regex/keyword heuristics. Not a trained model, despite
                             living under `ml/`.
    function_classifier.py  Real sklearn (TF-IDF + MultinomialNB + RandomForest),
                             online-learning design that persists trained models to
                             ~/.cache/manw-ng/ml_models/*.pkl. No model ships in the
                             repo, so on a fresh checkout it is untrained and
                             predict_headers() returns [] until it has learned from
                             enough successful runtime lookups.
    urltran_bert.py  Orphaned/unused module (nothing imports it); would need
                      transformers+torch, which aren't dependencies. Dead code —
                      left as-is, not deleted, since it's inert and harmless.
  utils/
    dll_map.py              Heuristic DLL-from-function-name detection (used by
                             doc mode's auto-detect, not the same table as exec
                             mode's k/u/n/a32 abbreviations in execution/engine.py).
    http_client.py          Real async HTTP client (aiohttp) with ETag/Last-Modified
                             conditional caching under ~/.cache/manw-ng. Sync callers
                             wrap it with asyncio.run() per call.
    smart_url_generator.py  ~2000+ lines of hardcoded DLL/header maps + regex
                             patterns for candidate URL generation; async validation.
    url_pattern_learner.py  Self-learning URL cache persisted to
                             ~/.cache/manw-ng/url_patterns.json. Imports ml_classifier
                             (function_classifier), so it inherits the "untrained by
                             default" limitation above.
    catalog_integration.py  Simple lookup over manw_ng/assets/win32_api_catalog.json
                             (a separate, smaller catalog: ~678 entries).
  output/
    formatters.py     RichFormatter (function/struct/enum/callback kinds),
                      JSONFormatter, MarkdownFormatter — all three localize to the
                      selected language.
  execution/
    types.py          Argument/return-type parsing ($b:/$s:/int/hex/string syntax,
                       --ret mapping). Pure functions, no ctypes DLL calls — fully
                       unit-testable without Windows.
    memory.py          Buffer tracking + hexdump helper for $b: arguments.
    engine.py           ExecutionEngine: resolves dll/function (k/u/n/a32/g/ws2/sh
                       abbreviations, A/W variant fallback), builds the ctypes call,
                       invokes it, reports GetLastError on --show-error.
                       `self._load_dll` is the one seam that touches
                       `ctypes.WinDLL`, so tests monkeypatch it with a fake loader.
manw_ng/assets/
  complete_function_mapping.json   61,000+ function->header mappings.
  winapi_categories.json           ~7,866 entries, 11MB — large shipped asset.
  win32_api_catalog.json           Separate smaller catalog (~678 entries), used by
                                    catalog_integration.py only.
  comprehensive_test_db.json       Used by .github/workflows/win32-comprehensive-tests.yml.
assets/
  demo.png           README screenshot only — not read by any code, deliberately
                      left at the repo root (not under manw_ng/) so it renders on
                      GitHub via the README's relative image link.
tests/
  pytest suite: test_formatters.py, test_dll_map.py, test_scraper_errors.py,
  test_execution_types.py, test_execution_engine.py. Run with `pytest tests/`.
  CI (.github/workflows/ci.yml) runs this suite as the primary correctness gate;
  the older inline `python -c "..."` smoke scripts remain as a secondary check —
  they mostly test enhanced_classifier's own hardcoded dict, so they're weak
  signal on their own.
```

### The scraping pipeline

`Win32APIScraper.scrape_function()` in [manw_ng/core/scraper.py](manw_ng/core/scraper.py)
runs, in order, until one step succeeds: special-case shortcuts and a known-undocumented
API denylist (instant fast exits) → (1) MS Learn Search API → (2) Smart URL Generation →
(3) heuristic ML classifier fallback → (4) internal catalog → (5) offline JSON mapping →
final A/W suffix retry. `SmartURLGenerator` and the HTTP caching layer are the
best-engineered parts of the codebase; treat them as the reliable core when reasoning
about doc-mode behavior.

### "ML classification" — read this before trusting the branding

"Heuristic classification" (formerly branded "AI-powered" in the README — since fixed)
refers to `enhanced_classifier.py`'s hardcoded dictionary + reverse-index, **not** a
trained model. The one real sklearn classifier (`function_classifier.py`) ships
untrained. Don't assume `predict_headers()` calls involve inference unless you've
checked which classifier (`enhanced_ml_classifier` vs `ml_classifier`) is actually
being called — `manw_ng/ml/__init__.py` aliases
`primary_classifier = enhanced_ml_classifier`.

## Fixed in the 3.4.0 pass (for history/context only — don't re-fix these)

- `scraper.py` had `_search_microsoft_learn()` defined twice (dead first copy
  referenced a nonexistent `self.http_client`); the priority chain called it three
  times redundantly under inconsistent labels; a dead "direct mapping" block
  (`_try_direct_url()` was a permanent no-op) did nothing. All removed/deduped;
  pipeline renumbered to a clean 5-step chain.
- `get_string("function_not_found")` was called with a key that didn't exist in
  `self.strings`, so error messages printed the literal text `function_not_found`.
  Fixed by adding the key with a real, per-language templated message.
- `MarkdownFormatter.format_output()` hardcoded Portuguese section headers
  regardless of the `language` argument. Fixed with a proper us/br string table.
- Version mismatch between `manw_ng/__init__.py` and `--version` — now both read
  from `manw_ng.__version__` (currently `3.4.0`).
- `assets/` (repo root) → `manw_ng/assets/` for the JSON data files actually loaded
  by code, so `pip install`/wheels carry them; `assets/demo.png` stays at the repo
  root for the README image; dead backup copies and an unused mapping file were
  deleted; the stray `assets/__init__.py` was removed (it's a data dir, not a
  package).
- Added `pyproject.toml` (packaging didn't exist before at all) and moved CLI logic
  into `manw_ng/cli.py` so it's importable for the `manw-ng` console-script entry
  point.
- Execution mode's `--ret`/`--wide`/`--show-error`/`$b:`/`$s:` and the whole
  `manw_ng/execution/` package were built from scratch — previously only a ~70-line
  stub existed with no return-type control, no error reporting, no buffer support.
- Added the first real pytest suite (`tests/`); previously only `__init__.py` existed.

## Known remaining rough edges (not fixed in this pass, flagged for later)

- Doc-mode CLI runs can print an `aiohttp` "Unclosed client session" warning on
  stderr in some code paths — a pre-existing async-cleanup nuance, not addressed
  here.
- `win32-comprehensive-tests.yml` does live HTTP validation against
  learn.microsoft.com — flaky-by-design, mostly `|| true`/lenient thresholds.
- `function_classifier.py`'s sklearn model still ships untrained; nothing trains
  it as part of the build. It's harmless (falls back to `[]`) but contributes
  nothing until enough successful runtime lookups accumulate in
  `~/.cache/manw-ng/ml_models/`.

## Conventions

- Formatters take `show_remarks` / `show_parameter_tables` flags — these are
  opt-in (`-O`/`--obs`, `-t`/`--tabs`) and hidden by default; preserve that default
  when touching CLI args or formatter signatures.
- Prefer running the CLI directly to validate changes (`python manw-ng.py <Func> -o json`)
  and running `pytest tests/` before considering a change done.
- `ExecutionEngine._load_dll` is the intentional seam for testing exec mode without
  Windows — don't call `ctypes.WinDLL` directly elsewhere in `execution/`.
