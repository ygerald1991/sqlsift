"""sqlsift — Detect slow queries and generate optimization suggestions from query logs."""

from sqlsift.parser import QueryEntry, parse_line, parse_log

__version__ = "0.1.0"
__all__ = ["QueryEntry", "parse_line", "parse_log"]
