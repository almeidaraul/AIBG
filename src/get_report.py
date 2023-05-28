import sys
import argparse
import glikoz


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

    csv = sys.stdin
    df = glikoz.DiaguardCSVParser().parse_csv(csv)
    df_handler = glikoz.DataFrameHandler(df)

    if args.format == "json":
        output = open("output.json", "w")
        reporter = glikoz.JSONReportCreator(df_handler)
    elif args.format == "pdf":
        output = open("output.pdf", "wb")
        reporter = glikoz.PDFReportCreator(df_handler)

    reporter.fill_report()
    reporter.create_report(output)


if __name__ == "__main__":
    get_report()
