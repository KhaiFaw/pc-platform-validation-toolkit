"""Result states used consistently by tests, runs, reports, and exit codes."""

from enum import StrEnum


class ResultStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"
    ERROR = "ERROR"
