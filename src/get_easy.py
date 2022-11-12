"""usage: python3 get_json.py < in_csv.csv > out_csv.csv"""
from explorer import Explorer
from easy_reporter import EasyReporter

exp = Explorer(verbose=False)
easy_reporter = EasyReporter(exp)
easy_reporter.report()
