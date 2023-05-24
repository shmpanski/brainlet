import argparse
import json
import sys
from typing import Iterator

import weaviate
from tqdm import tqdm

from brainlet.core import create_schema, import_data, ask_question


def iter_jsonl(filename: str) -> Iterator[dict]:
    with open(filename) as file:
        yield from map(json.loads, file)


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


def inference(
    client: weaviate.Client,
    questions_file: str,
    output_file: str,
    progress: bool = False,
    **kwargs
):
    questions = iter_jsonl(questions_file)
    result: dict[str, str] = {}

    if progress:
        questions = tqdm(list(questions), smoothing=0.0)

    for question in questions:
        answer = ask_question(client, question["question"])
        result[question["id"]] = answer.answer if answer.has_answer else ""

    with open(output_file, "w") as file:
        json.dump(result, file, ensure_ascii=False)


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

    inference_parser = subparsers.add_parser(
        "inference", help="inference for QA squad-2.0-like datasets"
    )
    inference_parser.add_argument(
        "--questions-file",
        required=True,
        type=str,
        help="jsonl file with questions. Each sample have to has `id` and `question` properties",
    )
    inference_parser.add_argument(
        "--output-file",
        required=True,
        type=str,
        help="file to output answers in squad-2.0 format",
    )
    inference_parser.add_argument("-p", "--progress", action="store_true")
    inference_parser.set_defaults(func=inference)

    args = parser.parse_args()
    client = weaviate.Client(args.weaviate_client)

    args.func(client=client, **vars(args))
