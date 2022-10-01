import argparse
import csv
import logging
import os
import pathlib
from typing import IO

from .config import Config, get_config, print_config, set_config
from .constant import OutputFormat, VERSION
from .lyjournal import SimpleLYJournal
from .log import get_logger


def config(args: argparse.Namespace) -> int:
    conf: Config = get_config()

    if not args.field:
        print_config()
    elif not args.value:
        print(getattr(conf, args.field))
    else:
        setattr(conf, args.field, args.value)
        set_config()

    return 0


def output_search_results(results: dict[str, list[dict[str, str]]], keyword: str, format: OutputFormat = None) -> None:
    if format is None:
        format = OutputFormat.CSV

    if format is OutputFormat.CSV:
        res_type: str
        for res_type in results:
            fields: list[str] = list()
            field_set: set[str] = set()

            result: dict[str, str]
            for result in results[res_type]:
                k: str
                for k in result:
                    if k in field_set:
                        continue
                    fields.append(k)
                    field_set.add(k)

            c: str
            file: pathlib.Path = pathlib.Path(
                f"{''.join(c if c.isalpha() or c.isdigit() else '-' for c in keyword).strip()}-{res_type}.csv")
            while file.exists():
                file = pathlib.Path(f"{file.stem}-new{file.suffix}")
            f: IO
            with open(file, 'w', encoding="utf-8-sig", newline='\n') as f:
                writer: csv.DictWriter = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                writer.writerows(results[res_type])


def scrape(args: argparse.Namespace) -> int:
    simple_lyjournal: SimpleLYJournal = SimpleLYJournal(get_config())
    results: dict[str, list[dict[str, str]]] = simple_lyjournal.search(args.keyword)
    simple_lyjournal.quit()
    get_logger().debug(results)
    output_search_results(results, args.keyword)
    return 0


def get_arg_parser() -> argparse.ArgumentParser:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="lyjournal-scraper" + ".exe" if os.name == 'nt' else "")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--version", action="store_true")

    subparsers: argparse._SubParsersAction = parser.add_subparsers()

    subparser_config: argparse.ArgumentParser = subparsers.add_parser("config", help="read and write config")
    subparser_config.add_argument("field", nargs='?', choices=["browser", "gh_token"])
    subparser_config.add_argument("value", nargs='?')
    subparser_config.set_defaults(func=config)

    subparser_scrape: argparse.ArgumentParser = subparsers.add_parser("scrape", help="scrape the search result")
    subparser_scrape.add_argument("keyword")
    subparser_scrape.set_defaults(func=scrape)

    return parser


def main() -> int:
    arg_parser: argparse.ArgumentParser = get_arg_parser()
    args: argparse.Namespace = arg_parser.parse_args()

    if args.verbose:
        get_logger().setLevel(logging.DEBUG)

    if args.version:
        print(f"lyjournal-scraper{'.exe' if os.name == 'nt' else ''} {VERSION}")
        return 0

    if not hasattr(args, 'func'):
        arg_parser.print_help()
        return 1

    if get_config().gh_token:
        os.environ['GH_TOKEN'] = get_config().gh_token

    return args.func(args)
