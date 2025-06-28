"""Enhanced MCP tools for all XRPL models with proper parameter schemas."""

import inspect
import re
from enum import Enum
from types import ModuleType
from typing import Dict, List, Type, Union, get_args, get_origin

import xrpl.models.amounts as amounts
import xrpl.models.currencies as currencies
import xrpl.models.requests as requests
import xrpl.models.transactions as transactions
from xrpl.models import AuthAccount, Path, PathStep, Response, XChainBridge
from xrpl.models.base_model import BaseModel
from xrpl.models.required import REQUIRED
from xrpl.server.config import mcp


def extract_enum_info(enum_class: Type[Enum]) -> Dict[str, object]:
    """Extract enum values and their documentation."""
    enum_info = {
        "type": "enum",
        "name": enum_class.__name__,
        "values": {},
        "description": enum_class.__doc__ or "",
    }

    for member in enum_class:
        enum_info["values"][member.name] = {
            "value": member.value,
            "description": member.__doc__ or "",
        }

    return enum_info


def get_field_type_info(field_type: object) -> Dict[str, object]:
    """Extract detailed type information from a field type."""
    type_info = {
        "python_type": str(field_type),
        "is_optional": False,
        "is_list": False,
        "inner_type": None,
        "enum_info": None,
    }

    origin = get_origin(field_type)
    args = get_args(field_type)

    # Handle Union types (Optional[T] is Union[T, None])
    if origin is Union:
        # Check if it's Optional (Union with None)
        if len(args) == 2 and type(None) in args:
            type_info["is_optional"] = True
            # Get the non-None type
            inner_type = args[0] if args[1] is type(None) else args[1]
            type_info["inner_type"] = str(inner_type)

            # Recursively check the inner type
            inner_info = get_field_type_info(inner_type)
            type_info.update(
                {k: v for k, v in inner_info.items() if k not in ["is_optional"]}
            )

    # Handle List types
    elif origin is list or origin is List:
        type_info["is_list"] = True
        if args:
            type_info["inner_type"] = str(args[0])
            # Check if list item type is enum
            if inspect.isclass(args[0]) and issubclass(args[0], Enum):
                type_info["enum_info"] = extract_enum_info(args[0])

    # Handle direct enum types
    elif inspect.isclass(field_type) and issubclass(field_type, Enum):
        type_info["enum_info"] = extract_enum_info(field_type)

    return type_info


def get_comprehensive_model_info(model_class: Type[BaseModel]) -> Dict[str, object]:
    """Extract comprehensive information about a model class including enums."""
    model_fields = {}

    if hasattr(model_class, "__dataclass_fields__"):
        for field_name, field_info in model_class.__dataclass_fields__.items():
            is_required = field_info.default == REQUIRED

            # Get type information
            field_type = field_info.type
            type_info = get_field_type_info(field_type)

            # Extract docstring from the field
            field_doc = ""
            if hasattr(field_info, "metadata") and field_info.metadata:
                field_doc = field_info.metadata.get("doc", "")

            # Try to get docstring from class annotations
            if not field_doc and hasattr(model_class, "__annotations__"):
                # Look for docstring in the source code after the field
                try:
                    source = inspect.getsource(model_class)
                    # Simple regex to find docstring after field definition
                    pattern = rf"{field_name}:.*?\n\s*\"\"\"(.*?)\"\"\""
                    match = re.search(pattern, source, re.DOTALL)
                    if match:
                        field_doc = match.group(1).strip()
                except Exception:
                    pass

            model_fields[field_name] = {
                "required": is_required,
                "type_info": type_info,
                "default": None if is_required else field_info.default,
                "description": field_doc,
            }

    return {
        "name": model_class.__name__,
        "description": model_class.__doc__ or "",
        "fields": model_fields,
    }


def create_dynamic_model_tool(model_class: Type[BaseModel], category: str) -> None:
    """Create a dynamic MCP tool with explicit parameter signatures."""
    model_info = get_comprehensive_model_info(model_class)
    fields = model_info["fields"]

    # Build function parameters and documentation
    required_params = []
    optional_params = []
    param_docs = []

    for field_name, field_info in fields.items():
        type_info = field_info["type_info"]
        is_required = field_info["required"]
        description = field_info["description"]

        # Build parameter documentation
        param_doc = f"        {field_name}: "

        if type_info["enum_info"]:
            enum_info = type_info["enum_info"]
            param_doc += f"Enum {enum_info['name']} - {enum_info['description']}\n"
            param_doc += f"            Valid values: {list(enum_info['values'].keys())}"
        else:
            param_doc += f"{type_info['python_type']}"

        if description:
            param_doc += f" - {description}"

        if not is_required:
            param_doc += " (Optional)"

        param_docs.append(param_doc)

        # Collect parameter names for function signature
        if is_required:
            required_params.append(field_name)
        else:
            optional_params.append(field_name)

    # Create the tool function dynamically with explicit parameters
    tool_name = f"create_{category.lower()}_{model_class.__name__.lower()}"

    # Create a function with explicit parameters using types.FunctionType
    # Build parameter list for function creation
    all_params = required_params + optional_params

    def convert_field_value(field_name: str, value: object) -> object:
        """Convert field value to the appropriate type based on field info."""
        if value is None:
            return None

        # Handle string to boolean conversion
        if isinstance(value, str):
            if value.lower() in ["true", "1", "yes", "on"]:
                return True
            elif value.lower() in ["false", "0", "no", "off"]:
                return False

        # Try to convert to int if it looks like a number
        if isinstance(value, str) and value.isdigit():
            try:
                return int(value)
            except ValueError:
                pass

        # Try to convert to float
        if isinstance(value, str):
            try:
                float_val = float(value)
                # Only return float if it's not a whole number
                if float_val != int(float_val):
                    return float_val
                else:
                    return int(float_val)
            except ValueError:
                pass

        # Try to convert hex strings to integers for numeric fields
        if (
            isinstance(value, str)
            and field_name.endswith(("_id", "_hash", "_sequence"))
            and value.startswith("0x")
        ):
            try:
                return int(value, 16)
            except ValueError:
                pass

        return value

    def create_function_with_params():
        # Build the actual implementation
        def implementation(*args, **kwargs) -> Dict[str, object]:  # type: ignore
            # Map positional args to parameter names
            param_values = {}
            for i, value in enumerate(args):
                if i < len(all_params):
                    param_values[all_params[i]] = value

            # Add keyword arguments
            param_values.update(kwargs)

            # Convert and filter parameters
            filtered_kwargs = {}
            for field_name, value in param_values.items():
                if field_name in [
                    "_meta"
                ]:  # Skip metadata fields that aren't model fields
                    continue
                if value is not None or field_name in required_params:
                    converted_value = convert_field_value(field_name, value)
                    if converted_value is not None:
                        filtered_kwargs[field_name] = converted_value

            try:
                # Validate required fields
                missing_required = [
                    field
                    for field in required_params
                    if field not in filtered_kwargs
                ]
                if missing_required:
                    return {
                        "success": False,
                        "error": f"Missing required fields: {missing_required}",
                        "model_class": model_class.__name__,
                        "required_fields": required_params,
                        "optional_fields": optional_params,
                        "provided_fields": list(filtered_kwargs.keys()),
                        "field_schemas": {
                            name: {
                                "required": info["required"],
                                "type": info["type_info"]["python_type"],
                                "enum_values": (
                                    info["type_info"]["enum_info"]["values"]
                                    if info["type_info"]["enum_info"]
                                    else None
                                ),
                                "description": info["description"],
                            }
                            for name, info in fields.items()
                        },
                    }

                # Validate enum values
                validation_errors = []
                for field_name, value in filtered_kwargs.items():
                    if field_name in fields:
                        field_info = fields[field_name]
                        enum_info = field_info["type_info"]["enum_info"]
                        if enum_info and value is not None:
                            valid_values = list(enum_info["values"].keys())
                            if (
                                value not in valid_values
                                and str(value) not in valid_values
                            ):
                                # Try to match by enum value
                                valid_enum_values = [
                                    info["value"]
                                    for info in enum_info["values"].values()
                                ]
                                if value not in valid_enum_values:
                                    validation_errors.append(
                                        f"{field_name}: '{value}' is not valid. "
                                        f"Valid values: {valid_values}"
                                    )

                if validation_errors:
                    return {
                        "success": False,
                        "error": "Enum validation failed",
                        "validation_errors": validation_errors,
                        "model_class": model_class.__name__,
                    }

                # Create the model instance
                model_instance = model_class(**filtered_kwargs)

                # Return just 
                #the model dictionary as requested
                if hasattr(model_instance, 'to_xrpl'):
                    return model_instance.to_xrpl()
                else:
                    return model_instance.to_dict()

            except Exception as e:
                return str(e)
                # return {
                #     "success": False,
                #     "error": str(e),
                #     "model_class": model_class.__name__,
                #     "category": category,
                #     "provided_fields": list(param_values.keys()),
                #     "required_fields": required_params,
                #     "optional_fields": optional_params,
                #     "type_conversion_attempted": True,
                # }

        # Create a new function with the right signature
        import inspect
        
        # Build parameter list
        parameters = []
        for param_name in required_params:
            parameters.append(inspect.Parameter(param_name, inspect.Parameter.POSITIONAL_OR_KEYWORD))
        for param_name in optional_params:
            parameters.append(inspect.Parameter(param_name, inspect.Parameter.POSITIONAL_OR_KEYWORD, default=None))
        
        # Create signature
        sig = inspect.Signature(parameters)
        
        # Set the signature on the implementation
        implementation.__signature__ = sig
        
        # Set docstring
        doc_lines = [
            f"Create a {model_class.__name__} model and return its dictionary representation.",
            "",
            model_info['description'],
            "",
            "Parameters:",
        ]
        doc_lines.extend(param_docs)
        doc_lines.extend([
            "",
            f"Returns:",
            f"    Dictionary representation of the {model_class.__name__} model with validation",
            "",
            "Note: String values are automatically converted to appropriate types (int, float, bool) when possible."
        ])
        
        implementation.__doc__ = "\n".join(doc_lines)
        implementation.__name__ = f"{tool_name}_impl"
        
        return implementation

    # Create and register the tool function
    func_impl = create_function_with_params()
    mcp.tool(name=tool_name)(func_impl)


def get_model_classes(module: ModuleType) -> Dict[str, Type[BaseModel]]:
    """Extract all BaseModel classes from a module."""
    model_classes = {}

    for name in dir(module):
        obj = getattr(module, name)
        if (
            inspect.isclass(obj)
            and issubclass(obj, BaseModel)
            and obj != BaseModel
            and not name.endswith("Interface")
            and not name.endswith("Flag")
            and not name.startswith("_")
        ):
            model_classes[name] = obj

    return model_classes


# Register all models with enhanced tools
print("Registering XRPL model tools with proper schemas...")

# Transaction models
transaction_models = get_model_classes(transactions)
print(f"Found {len(transaction_models)} transaction models")
for name, model_class in transaction_models.items():
    try:
        create_dynamic_model_tool(model_class, "Transaction")
    except Exception as e:
        print(f"Warning: Could not create tool for transaction {name}: {e}")

# Request models
request_models = get_model_classes(requests)
print(f"Found {len(request_models)} request models")
for name, model_class in request_models.items():
    try:
        create_dynamic_model_tool(model_class, "Request")
    except Exception as e:
        print(f"Warning: Could not create tool for request {name}: {e}")

# Amount models
amount_models = get_model_classes(amounts)
print(f"Found {len(amount_models)} amount models")
for name, model_class in amount_models.items():
    try:
        create_dynamic_model_tool(model_class, "Amount")
    except Exception as e:
        print(f"Warning: Could not create tool for amount {name}: {e}")

# Currency models
currency_models = get_model_classes(currencies)
print(f"Found {len(currency_models)} currency models")
for name, model_class in currency_models.items():
    try:
        create_dynamic_model_tool(model_class, "Currency")
    except Exception as e:
        print(f"Warning: Could not create tool for currency {name}: {e}")

# Other models
other_models = {
    "AuthAccount": AuthAccount,
    "Path": Path,
    "PathStep": PathStep,
    "Response": Response,
    "XChainBridge": XChainBridge,
}

print(f"Found {len(other_models)} other models")
for name, model_class in other_models.items():
    try:
        create_dynamic_model_tool(model_class, "Other")
    except Exception as e:
        print(f"Warning: Could not create tool for other {name}: {e}")


@mcp.tool()
def list_available_model_tools() -> Dict[str, object]:
    """
    List all available XRPL model creation tools with detailed schemas.

    Returns:
        Dictionary containing categorized lists of available model tools with schemas
    """

    def get_model_summaries(models_dict: Dict[str, Type[BaseModel]]) -> Dict[str, object]:
        return {
            name: {
                "tool_name": f"create_{name.lower()}",
                "description": model_class.__doc__ or "",
                "field_count": len(
                    getattr(model_class, "__dataclass_fields__", {})
                ),
            }
            for name, model_class in models_dict.items()
        }

    return {
        "transactions": {
            "count": len(transaction_models),
            "models": get_model_summaries(transaction_models),
        },
        "requests": {
            "count": len(request_models),
            "models": get_model_summaries(request_models),
        },
        "amounts": {
            "count": len(amount_models),
            "models": get_model_summaries(amount_models),
        },
        "currencies": {
            "count": len(currency_models),
            "models": get_model_summaries(currency_models),
        },
        "other": {
            "count": len(other_models),
            "models": get_model_summaries(other_models),
        },
        "total_tools": (
            len(transaction_models)
            + len(request_models)
            + len(amount_models)
            + len(currency_models)
            + len(other_models)
        ),
    }


@mcp.tool()
def get_model_schema(model_name: str) -> Dict[str, object]:
    """
    Get detailed schema information for a specific XRPL model.

    Args:
        model_name: Name of the model to get schema for

    Returns:
        Detailed schema information including all fields, types, and enum values
    """
    # Find the model class
    all_models = {
        **transaction_models,
        **request_models,
        **amount_models,
        **currency_models,
        **other_models,
    }

    if model_name not in all_models:
        return {
            "error": f"Model '{model_name}' not found",
            "available_models": list(all_models.keys()),
        }

    model_class = all_models[model_name]
    model_info = get_comprehensive_model_info(model_class)

    return {
        "model_name": model_name,
        "description": model_info["description"],
        "tool_name": f"create_{model_name.lower()}",
        "fields": {
            name: {
                "required": info["required"],
                "type": info["type_info"]["python_type"],
                "is_optional": info["type_info"]["is_optional"],
                "is_list": info["type_info"]["is_list"],
                "enum_info": info["type_info"]["enum_info"],
                "description": info["description"],
                "default": info["default"],
            }
            for name, info in model_info["fields"].items()
        },
    }


print("XRPL model tools registration complete!") 