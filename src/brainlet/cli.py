import argparse
import sys

import weaviate

from brainlet.core import create_schema, import_data, ask_question


def init(client: weaviate.Client, overwrite: bool = False, **kwargs):
    try:
        create_schema(client, overwrite=overwrite)
    except RuntimeError:
        msg = "Data Schema already exists. Use --overwrite flag to overwrite schema."
        sys.exit(msg)


def index(
    client: weaviate.Client,
    source: str,
    batch_size: int,
    progress: bool = False,
    **kwargs
):
    import_data(client, source, batch_size, progress)


def ask(client: weaviate.Client, question: str, **kwargs):
    print(ask_question(client, question))


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--weaviate-client", type=str, default="http://127.0.0.1:8080"
    )
    subparsers = parser.add_subparsers(required=True)

    init_parser = subparsers.add_parser("init", help="Initialize index schema")
    init_parser.add_argument(
        "--overwrite", action="store_true", help="whether to overwrite existing schema"
    )
    init_parser.set_defaults(func=init)

    index_parser = subparsers.add_parser(
        "index", help="Import data and perform indexing"
    )
    index_parser.add_argument(
        "-s", "--source", type=str, required=True, help="Source .jsonl file"
    )
    index_parser.add_argument("-b", "--batch-size", type=int, default=8)
    index_parser.add_argument("-p", "--progress", action="store_true")
    index_parser.set_defaults(func=index)

    ask_parser = subparsers.add_parser("ask", help="CLI interface for asking")
    ask_parser.add_argument("question", type=str)
    ask_parser.set_defaults(func=ask)

    args = parser.parse_args()
    client = weaviate.Client(args.weaviate_client)

    args.func(client=client, **vars(args))
