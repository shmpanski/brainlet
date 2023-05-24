import argparse
import json
import os.path
from typing import Iterator, Iterable, Optional


def save_jsonl(data: Iterable[dict], filename: str):
    with open(filename, "w") as file:
        for sample in data:
            dumps = json.dumps(sample, ensure_ascii=False)
            print(dumps, file=file)


def convert_to_import_format(data: list[dict]) -> Iterator[dict]:
    for i, sample in enumerate(data):
        yield {
            "url": str(i),
            "title": sample["title"],
            "paragraphs": [p["context"] for p in sample["paragraphs"]],
        }


def fetch_questions(data: list[dict]) -> Iterator[dict]:
    for sample in data:
        for paragraph in sample["paragraphs"]:
            for qas in paragraph["qas"]:
                yield {"id": qas["id"], "question": qas["question"]}


def main(
    input_filename: str,
    output_directory: str,
    max_samples: Optional[int] = None,
    **kwargs
):
    with open(input_filename) as file:
        original_file_dump = json.load(file)
        data: list[dict] = original_file_dump["data"]

    if max_samples is not None:
        data = data[:max_samples]

    os.makedirs(output_directory, exist_ok=True)
    knowledge_base_filename = os.path.join(output_directory, "knowledge-base.jsonl")
    questions_filename = os.path.join(output_directory, "questions.jsonl")

    knowledge_base = convert_to_import_format(data)
    save_jsonl(knowledge_base, knowledge_base_filename)

    questions = fetch_questions(data)
    save_jsonl(questions, questions_filename)

    dev_set_filename = os.path.join(output_directory, "squad-2.0-dev.json")
    original_file_dump["data"] = data
    with open(dev_set_filename, "w") as file:
        json.dump(original_file_dump, file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-filename", type=str, required=True)
    parser.add_argument("-o", "--output-directory", type=str, required=True)
    parser.add_argument(
        "--max-samples",
        type=int,
        help="limit for questions exporting. Useful for slow hardware. Use it for testing a part of data.",
    )

    args = parser.parse_args()
    main(**vars(args))
