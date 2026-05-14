"""Command-line interface for sqlsift."""

import argparse
import sys
from pathlib import Path

from sqlsift.parser import parse_log
from sqlsift.analyzer import analyze_entries
from sqlsift.reporter import build_report, format_report


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sqlsift",
        description="Detect slow queries and generate optimization suggestions.",
    )
    parser.add_argument(
        "logfile",
        type=Path,
        help="Path to the query log file to analyze.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=1000.0,
        metavar="MS",
        help="Duration threshold in milliseconds (default: 1000).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show per-query suggestions in the report.",
    )
    return parser


def _read_log_file(log_path: Path) -> str | None:
    """Read the log file and return its contents, or None on failure.

    Prints an error message to stderr and returns None if the file does not
    exist or cannot be read.
    """
    if not log_path.exists():
        print(f"Error: file not found: {log_path}", file=sys.stderr)
        return None
    try:
        return log_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Error reading file: {exc}", file=sys.stderr)
        return None


def run(argv=None) -> int:
    """Entry point for the CLI. Returns an exit code."""
    arg_parser = create_parser()
    args = arg_parser.parse_args(argv)

    raw_text = _read_log_file(args.logfile)
    if raw_text is None:
        return 1

    entries = parse_log(raw_text)
    if not entries:
        print("No valid query entries found in log.", file=sys.stderr)
        return 1

    results = analyze_entries(entries, threshold_ms=args.threshold)
    report = build_report(results)
    print(format_report(report, verbose=args.verbose))
    return 0


def main():
    sys.exit(run())


if __name__ == "__main__":
    main()
