"""
usage: python3 get_json.py in_csv.csv out_json.json
"""
from explorer import Explorer
from reporter import JSONReporter
import sys

in_csv = sys.argv[1]
out_json = sys.argv[2]

exp = Explorer(in_csv, verbose=False)
json_reporter = JSONReporter(exp)
json_reporter.save(out_json)
