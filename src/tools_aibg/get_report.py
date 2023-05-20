import argparse
from .explorer import Explorer
from .reporters.json_reporter import JSONReporter
from .reporters.raw_reporter import RawReporter
from .reporters.pdf_reporter import PDFReporter


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
    exp = Explorer(verbose=args.verbose)

    if args.format == "json":
        reporter = JSONReporter(exp)
    elif args.format == "raw":
        reporter = RawReporter(exp)
    elif args.format == "pdf":
        reporter = PDFReporter(exp)

    reporter.report()
