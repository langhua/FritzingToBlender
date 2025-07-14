from dataclasses import dataclass

@dataclass
class PCBImportData:
    filenames: dict
    svgLayers: dict
    total: int
    current: int
    error_msg: str | None
    current_file: str | None
    step_name: str | None
