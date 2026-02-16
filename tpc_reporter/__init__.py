"""
TPC Workshop Reporter - Generate track reports from conference data.
"""

from tpc_reporter.assembler import (
    AssemblyResult,
    AssemblyWarning,
    assemble_all_tracks,
    assemble_track_bundle,
    load_attendees_csv,
    load_lightning_talks_csv,
    load_notes_file,
)
from tpc_reporter.checker import (
    VerificationResult,
    check_report,
    check_report_from_files,
    extract_flags,
    load_checker_prompt,
    parse_verification_summary,
)
from tpc_reporter.config_loader import Config, ConfigurationError, load_config
from tpc_reporter.gdrive import (
    DriveFile,
    collect_all_data,
    collect_track_data,
    download_doc,
    download_file,
    download_sheet,
    extract_file_id,
)
from tpc_reporter.generator import (
    format_track_bundle,
    generate_report,
    generate_report_from_file,
    load_prompt,
)
from tpc_reporter.llm_client import LLMClient, create_llm_client

__version__ = "0.1.0"

__all__ = [
    # Assembler
    "AssemblyResult",
    "AssemblyWarning",
    "assemble_all_tracks",
    "assemble_track_bundle",
    "load_attendees_csv",
    "load_lightning_talks_csv",
    "load_notes_file",
    # Checker
    "VerificationResult",
    "check_report",
    "check_report_from_files",
    "extract_flags",
    "load_checker_prompt",
    "parse_verification_summary",
    # Config
    "Config",
    "ConfigurationError",
    "load_config",
    # Google Drive
    "DriveFile",
    "collect_all_data",
    "collect_track_data",
    "download_doc",
    "download_file",
    "download_sheet",
    "extract_file_id",
    # Generator
    "format_track_bundle",
    "generate_report",
    "generate_report_from_file",
    "load_prompt",
    # LLM Client
    "LLMClient",
    "create_llm_client",
]
