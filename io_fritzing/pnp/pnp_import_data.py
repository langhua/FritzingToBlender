from dataclasses import dataclass

@dataclass
class PnpImportData:
    filename: str | None
    step_name: str | None
    total_lines: int
    current_line: int
    error_msg: str | None
    step_part: str | None
    successed: int
    failed: int
    skipped: int
    invalid: int
    failed_lines: list[int]
    invalid_lines: list[int]
    pcb_thickness: float      # PCB板厚度
