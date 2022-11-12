import json
import sys
from reporter import Reporter


class JSONReporter(Reporter):
    def __init__(self, explorer):
        super().__init__(explorer)

    def report(self, filename=None):
        report = super().get_values()
        f = sys.stdout
        if filename is not None:
            f = open(filename, 'w')
        json.dump(report, f)
