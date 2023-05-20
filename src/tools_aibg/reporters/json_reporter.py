import json
import sys
from .base_reporter import Reporter


class JSONReporter(Reporter):
    """Reporter for JSON files"""

    def __init__(self, explorer):
        super().__init__(explorer)

    def report(self, filename: str = ...):
        """Dump base report dict into JSON file"""
        report = super().get_values()
        f = sys.stdout
        if filename is not None:
            f = open(filename, 'w')
        json.dump(report, f)
