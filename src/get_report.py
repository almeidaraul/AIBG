import sys
import argparse
from glikoz import JSONReportCreator, PDFReportCreator


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
        reporter = JSONReportCreator(input)
    elif args.format == "pdf":
        output = open("output.pdf", "wb")
        reporter = PDFReportCreator(input)

    reporter.fill_report()
    reporter.create_report(output)


if __name__ == "__main__":
    get_report()
