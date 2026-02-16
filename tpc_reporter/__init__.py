"""
TPC Workshop Reporter - Generate track reports from conference data.
"""

from tpc_reporter.checker import (
    VerificationResult,
    check_report,
    check_report_from_files,
    extract_flags,
    load_checker_prompt,
    parse_verification_summary,
)
from tpc_reporter.config_loader import Config, ConfigurationError, load_config
from tpc_reporter.generator import (
    format_track_bundle,
    generate_report,
    generate_report_from_file,
    load_prompt,
)
from tpc_reporter.llm_client import LLMClient, create_llm_client

__version__ = "0.1.0"

__all__ = [
    # Config
    "Config",
    "ConfigurationError",
    "load_config",
    # LLM Client
    "LLMClient",
    "create_llm_client",
    # Generator
    "format_track_bundle",
    "generate_report",
    "generate_report_from_file",
    "load_prompt",
    # Checker
    "VerificationResult",
    "check_report",
    "check_report_from_files",
    "extract_flags",
    "load_checker_prompt",
    "parse_verification_summary",
]
