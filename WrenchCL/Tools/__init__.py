"""Utility tools with optional dependencies."""

# Always available core tools (depend only on core dependencies)
from .Coalesce import coalesce
from .FetchMetaData import get_metadata
from .FileTyper import get_file_type
from .Image2B64 import get_hash, image_to_base64, validate_base64
from .JsonParser import list_loader, parse_json, safe_json_loader, show_json_tree
from .JsonSerializer import RobustJSONEncoder, robust_serializer, single_quote_decoder
from .MaybeMonad import Maybe
from .StandardizeNone import standardize_none
from .TypeChecker import typechecker

# Logger with optional color/trace support (handles its own optional deps internally)

__all__ = [
    "coalesce",
    "get_file_type",
    "image_to_base64",
    "Maybe",
    "typechecker",
    "get_metadata",
    "robust_serializer",
    "validate_base64",
    "single_quote_decoder",
    "parse_json",
    "safe_json_loader",
    "list_loader",
    "show_json_tree",
    "get_hash",
    "standardize_none",
    "RobustJSONEncoder",
]
