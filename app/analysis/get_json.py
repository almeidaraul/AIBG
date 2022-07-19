"""
usage: cat in_csv.csv > python3 get_json.py > out_csv.csv
"""
from explorer import Explorer
from reporter import JSONReporter
import sys

exp = Explorer(verbose=False)
json_reporter = JSONReporter(exp)
json_reporter.save()
