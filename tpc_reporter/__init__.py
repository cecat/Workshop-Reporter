"""
TPC Workshop Reporter - Generate track reports from conference data.
"""

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
    "Config",
    "ConfigurationError",
    "load_config",
    "LLMClient",
    "create_llm_client",
    "format_track_bundle",
    "generate_report",
    "generate_report_from_file",
    "load_prompt",
]
