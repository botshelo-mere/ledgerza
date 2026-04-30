import argparse
import sys
from .main import parse_and_summarize

def main() -> None:
    parser = argparse.ArgumentParser(
        description="ledgerZA — SA bank statement CSV parser and reporter"
    )
    parser.add_argument(
        "-f", "--file",
        required=True,
        help="Path to the CSV bank statement file",
    )
    args = parser.parse_args()

    try:
        parse_and_summarize(args.file)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
