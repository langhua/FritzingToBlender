from dataclasses import dataclass

@dataclass
class PnpImportData:
    filename: str | None
    total_lines: int
    current_line: int
    error_msg: str | None
    step_part: str | None
    successed: int
    failed: int
    skipped: int
