"""Command-line interface for cronaudit."""

import argparse
import sys
from typing import List

from cronaudit.collector import collect_local, collect_remote, collect_from_file
from cronaudit.multi import AuditResult
from cronaudit.formatter import to_text, to_json, to_csv


FORMATTERS = {
    "text": to_text,
    "json": to_json,
    "csv": to_csv,
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronaudit",
        description="Audit crontab entries across servers.",
    )
    p.add_argument(
        "--format",
        choices=list(FORMATTERS.keys()),
        default="text",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--local",
        action="store_true",
        help="Include the local machine's crontab",
    )
    p.add_argument(
        "--hosts",
        nargs="+",
        metavar="HOST",
        help="Remote hosts to audit via SSH",
    )
    p.add_argument(
        "--files",
        nargs="+",
        metavar="FILE",
        help="Crontab files to parse directly",
    )
    p.add_argument(
        "--output",
        metavar="FILE",
        help="Write report to FILE instead of stdout",
    )
    return p


def run(argv: List[str] = None) -> int:
    """Entry point; returns exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    server_crontabs = []

    if args.local:
        server_crontabs.append(collect_local())

    for host in args.hosts or []:
        server_crontabs.append(collect_remote(host))

    for filepath in args.files or []:
        server_crontabs.append(collect_from_file(filepath))

    if not server_crontabs:
        parser.error("Specify at least one of --local, --hosts, or --files.")
        return 1

    result = AuditResult(server_crontabs=server_crontabs)
    formatter = FORMATTERS[args.format]
    report = formatter(result)

    if args.output:
        with open(args.output, "w") as fh:
            fh.write(report)
    else:
        print(report)

    return 0 if result.failed() == 0 else 1


def main() -> None:  # pragma: no cover
    sys.exit(run())


if __name__ == "__main__":  # pragma: no cover
    main()
