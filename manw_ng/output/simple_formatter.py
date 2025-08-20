"""
Simple formatter for Windows compatibility
"""

from typing import Dict


def format_function_rich(function_info: Dict) -> str:
    """Simple text formatter for Windows terminals"""

    output = []
    output.append("=" * 60)
    output.append(f"WIN32 API FUNCTION: {function_info['name']}")
    output.append("=" * 60)

    # Basic Information
    output.append("\nBASIC INFORMATION:")
    output.append("-" * 20)
    output.append(f"DLL: {function_info['dll']}")
    output.append(f"Calling Convention: {function_info['calling_convention']}")
    output.append(f"Parameters: {function_info['parameter_count']}")
    output.append(f"Architectures: {', '.join(function_info['architectures'])}")
    output.append(f"Return Type: {function_info['return_type']}")

    # Function Signature
    if function_info.get("signature"):
        output.append("\nFUNCTION SIGNATURE:")
        output.append("-" * 20)
        output.append(function_info["signature"])

    # Parameters
    if function_info.get("parameters"):
        output.append(f"\nPARAMETERS ({len(function_info['parameters'])}):")
        output.append("-" * 20)

        for i, param in enumerate(function_info["parameters"], 1):
            output.append(f"{i}. {param['name']} ({param['type']})")
            output.append(f"   {param['description']}")

            # Parameter values if present
            if param.get("values"):
                for value_section in param["values"]:
                    if value_section.get("entries"):
                        output.append("   Values:")
                        for entry in value_section["entries"][:5]:  # Show max 5 values
                            output.append(
                                f"     - {entry.get('name', 'N/A')}: {entry.get('description', 'N/A')}"
                            )
                        if len(value_section["entries"]) > 5:
                            output.append(
                                f"     ... and {len(value_section['entries']) - 5} more"
                            )
            output.append("")

    # Return Value
    if function_info.get("return_description"):
        output.append("RETURN VALUE:")
        output.append("-" * 15)
        output.append(function_info["return_description"])

    # Description
    if function_info.get("description"):
        output.append("\nDESCRIPTION:")
        output.append("-" * 12)
        output.append(function_info["description"])

    output.append("\n" + "=" * 60)

    return "\n".join(output)
