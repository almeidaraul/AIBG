import sys
import argparse
from tools_aibg import JSONReporter, PDFReporter


def get_args():
    parser = argparse.ArgumentParser(prog="get_report",
                                     description="Report over diaguard CSV")

    parser.add_argument("--format", type=str, help="Report format",
                        required=True, choices=["json", "raw", "pdf"])
    parser.add_argument("--verbose", action="store_true", help="Verbose")

    return parser.parse_args()


def get_report(args=None):
    if args is None:
        args = get_args()

    input = sys.stdin

    if args.format == "json":
        output = open("output.json", "w")
        reporter = JSONReporter(input)
    elif args.format == "pdf":
        output = open("output.pdf", "wb")
        reporter = PDFReporter(input)

    reporter.report(output)