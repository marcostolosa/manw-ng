"""
Elite Windows API Execution Engine

Advanced runtime function invocation system inspired by winapiexec
with enhanced Python integration, intelligent error handling,
and comprehensive logging.
"""

import ctypes as ct
from ctypes import wintypes as wt
from typing import Any, Dict, List, Tuple, Optional, Union
import sys
import traceback
from contextlib import contextmanager

from .types import FunctionSignature, TypeConverter, ArgumentParser


class ExecutionResult:
    """Encapsulates the result of API execution with metadata"""
    
    def __init__(self, 
                 function_name: str,
                 dll_name: str,
                 resolved_name: str,
                 return_value: Any,
                 success: bool,
                 error_code: Optional[int] = None,
                 error_message: Optional[str] = None,
                 execution_time: float = 0.0,
                 buffer_dumps: Optional[List[str]] = None):
        
        self.function_name = function_name
        self.dll_name = dll_name
        self.resolved_name = resolved_name
        self.return_value = return_value
        self.success = success
        self.error_code = error_code
        self.error_message = error_message
        self.execution_time = execution_time
        self.buffer_dumps = buffer_dumps or []
    
    def __str__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        return f"[{status}] {self.dll_name}!{self.resolved_name} = {self.return_value}"
    
    def to_dict(self) -> Dict:
        """Convert result to dictionary for JSON serialization"""
        return {
            'function_name': self.function_name,
            'dll_name': self.dll_name,
            'resolved_name': self.resolved_name,
            'return_value': self.return_value,
            'success': self.success,
            'error_code': self.error_code,
            'error_message': self.error_message,
            'execution_time': self.execution_time,
            'buffer_dumps': self.buffer_dumps
        }


class WinAPIExecutor:
    """Elite Windows API execution engine with advanced features"""
    
    def __init__(self):
        self.type_converter = TypeConverter()
        self._loaded_modules: Dict[str, wt.HMODULE] = {}
        self._function_cache: Dict[str, Tuple[wt.HMODULE, Any]] = {}
        
        # Lazy initialization
        self.kernel32 = None
    
    def _ensure_kernel32(self):
        """Lazy initialize kernel32 only when needed"""
        if self.kernel32 is None:
            self.kernel32 = ct.WinDLL("kernel32", use_last_error=True)
            # Setup core functions
            self.kernel32.LoadLibraryW.argtypes = [wt.LPCWSTR]
            self.kernel32.LoadLibraryW.restype = wt.HMODULE
            self.kernel32.GetProcAddress.argtypes = [wt.HMODULE, wt.LPCSTR]
            self.kernel32.GetProcAddress.restype = ct.c_void_p
    
    def load_module(self, module_name: str) -> wt.HMODULE:
        """Load a module with caching and error handling"""
        
        self._ensure_kernel32()
        
        # Resolve module abbreviations
        resolved_name = self.type_converter.resolve_module(module_name)
        
        if resolved_name in self._loaded_modules:
            return self._loaded_modules[resolved_name]
        
        try:
            module_handle = self.kernel32.LoadLibraryW(resolved_name)
            if not module_handle:
                error_code = ct.get_last_error()
                error_msg = self._get_error_message(error_code)
                raise OSError(f"Failed to load {resolved_name}: {error_msg} (Error: {error_code})")
            
            self._loaded_modules[resolved_name] = module_handle
            return module_handle
            
        except Exception as e:
            raise
    
    def resolve_function(self, module_name: str, function_name: str, 
                        force_wide: bool = False) -> Tuple[wt.HMODULE, Any, str]:
        """
        Resolve function address with intelligent A/W suffix handling
        Similar to winapiexec's MyGetProcAddress
        """
        
        cache_key = f"{module_name}!{function_name}:{force_wide}"
        if cache_key in self._function_cache:
            return self._function_cache[cache_key]
        
        module_handle = self.load_module(module_name)
        
        # Build candidate list (winapiexec style)
        candidates = [function_name]
        
        if force_wide:
            candidates = [function_name + "W", function_name]
        else:
            # Try original, then A/W variants
            candidates.extend([function_name + "A", function_name + "W"])
        
        resolved_name = None
        function_addr = None
        
        for candidate in candidates:
            try:
                addr = self.kernel32.GetProcAddress(module_handle, candidate.encode('ascii'))
                if addr:
                    function_addr = addr
                    resolved_name = candidate
                    break
            except Exception:
                continue
        
        if not function_addr:
            raise AttributeError(
                f"Function '{function_name}' not found in {module_name}. "
                f"Tried variants: {candidates}"
            )
        
        result = (module_handle, function_addr, resolved_name)
        self._function_cache[cache_key] = result
        
        return result
    
    def _get_error_message(self, error_code: int) -> str:
        """Get formatted error message from error code"""
        if error_code == 0:
            return "Success"
        
        try:
            buffer = ct.create_unicode_buffer(1024)
            length = self.kernel32.FormatMessageW(
                0x00001000,  # FORMAT_MESSAGE_FROM_SYSTEM
                None,
                error_code,
                0,
                buffer,
                len(buffer),
                None
            )
            
            if length:
                return buffer.value.strip()
            else:
                return f"Unknown error (code: {error_code})"
                
        except Exception:
            return f"Error {error_code} (failed to format message)"
    
    def _build_function_prototype(self, function_addr: Any, signature: FunctionSignature) -> Any:
        """Build function prototype with correct calling convention and types"""
        
        # Parse arguments to get ctypes types
        arg_values, arg_types = signature.parse_arguments()
        return_type = signature.get_return_type()
        
        # Create function prototype (WINFUNCTYPE for stdcall/x64 ABI)
        if return_type is None:  # void function
            func_proto = ct.WINFUNCTYPE(None, *arg_types)
        else:
            func_proto = ct.WINFUNCTYPE(return_type, *arg_types)
        
        return func_proto(function_addr)
    
    @contextmanager
    def _execution_context(self):
        """Execution context with automatic cleanup"""
        try:
            yield
        finally:
            # Cleanup is handled by memory manager and garbage collection
            pass
    
    def execute(self, dll_spec: str, function_name: str, args: List[str], 
                return_type: str = "u64", force_wide: bool = False,
                show_last_error: bool = False) -> ExecutionResult:
        """
        Execute Windows API function with elite error handling
        
        Args:
            dll_spec: DLL name or abbreviation (e.g., 'kernel32.dll', 'k32', 'k')
            function_name: Function name to call
            args: List of argument strings in winapiexec format
            return_type: Expected return type
            force_wide: Force Wide (W) variant
            show_last_error: Include GetLastError in result
        """
        
        import time
        start_time = time.time()
        
        try:
            with self._execution_context():
                # Create function signature
                signature = FunctionSignature(function_name, dll_spec, args, return_type)
                
                # Resolve function
                module_handle, function_addr, resolved_name = self.resolve_function(
                    dll_spec, function_name, force_wide
                )
                
                # Build function prototype
                func = self._build_function_prototype(function_addr, signature)
                
                # Parse and convert arguments
                arg_values, arg_types = signature.parse_arguments()
                
                # Execute function
                
                if return_type.lower() == "void":
                    func(*arg_values)
                    result_value = None
                else:
                    result_value = func(*arg_values)
                
                # Collect buffer dumps
                buffer_dumps = self._collect_buffer_dumps(signature.parser)
                
                # Get error information if requested
                error_code = None
                error_message = None
                if show_last_error:
                    error_code = ct.get_last_error()
                    error_message = self._get_error_message(error_code)
                
                # Clean up signature resources
                signature.cleanup()
                
                execution_time = time.time() - start_time
                
                result = ExecutionResult(
                    function_name=function_name,
                    dll_name=dll_spec,
                    resolved_name=resolved_name,
                    return_value=result_value,
                    success=True,
                    error_code=error_code,
                    error_message=error_message,
                    execution_time=execution_time,
                    buffer_dumps=buffer_dumps
                )
                
                return result
                
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            logger.error(f"Execution failed: {error_msg}")
            logger.debug(f"Stack trace:\n{traceback.format_exc()}")
            
            return ExecutionResult(
                function_name=function_name,
                dll_name=dll_spec,
                resolved_name=function_name,
                return_value=None,
                success=False,
                error_code=-1,
                error_message=error_msg,
                execution_time=execution_time
            )
    
    def _collect_buffer_dumps(self, parser: ArgumentParser) -> List[str]:
        """Collect hexdumps from output buffers"""
        dumps = []
        
        for buffer in parser.allocated_buffers:
            try:
                if hasattr(buffer, 'hexdump'):
                    dumps.append(buffer.hexdump())
                else:
                    # Manual hexdump for ctypes arrays
                    size = ct.sizeof(buffer)
                    data = ct.string_at(buffer, size)
                    hex_str = ' '.join(f'{b:02x}' for b in data[:64])  # Limit to 64 bytes
                    dumps.append(hex_str)
            except Exception as e:
                logger.warning(f"Failed to dump buffer: {e}")
                dumps.append(f"<failed to dump buffer: {e}>")
        
        return dumps
    
    def execute_simple(self, spec: str, *args, **kwargs) -> ExecutionResult:
        """
        Simplified execution interface
        
        Args:
            spec: "dll!function" or "dll:function" format
            *args: Function arguments
            **kwargs: Options (return_type, force_wide, show_last_error)
        """
        
        # Parse spec
        if '!' in spec:
            dll, func = spec.split('!', 1)
        elif ':' in spec:
            dll, func = spec.split(':', 1)
        else:
            dll, func = "kernel32.dll", spec
        
        # Convert args to strings
        str_args = [str(arg) for arg in args]
        
        return self.execute(
            dll_spec=dll,
            function_name=func,
            args=str_args,
            return_type=kwargs.get('return_type', 'u64'),
            force_wide=kwargs.get('force_wide', False),
            show_last_error=kwargs.get('show_last_error', False)
        )
    
    def cleanup(self):
        """Clean up all resources"""
        # Clear caches
        self._function_cache.clear()
        self._loaded_modules.clear()
    
    def __del__(self):
        """Cleanup on destruction"""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore cleanup errors