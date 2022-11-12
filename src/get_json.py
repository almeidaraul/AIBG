"""usage: python3 get_json.py < in_csv.csv > out_csv.csv"""
from explorer import Explorer
from json_reporter import JSONReporter
import sys

exp = Explorer(verbose=False)
json_reporter = JSONReporter(exp)
json_reporter.report()
