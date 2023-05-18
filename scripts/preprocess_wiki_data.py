import argparse
import html
import json
import re
import unicodedata
from typing import Iterable, Iterator

RE_PARAGRAPH_SPLIT = re.compile(r"\n+")
RE_ABNORMAL_PARANTHESIS = re.compile(r"\([,;\s]*\)")
RE_WORD = re.compile(r"\w+")


def iter_jsonl(filename: str) -> Iterator[dict]:
    with open(filename) as file:
        for line in file:
            yield json.loads(line)


def save_jsonl(data: Iterable[dict], filename: str):
    with open(filename, "w") as file:
        for sample in data:
            dumps = json.dumps(sample, ensure_ascii=False)
            print(dumps, file=file)


def normalize_text(text: str) -> str:
    text = html.unescape(text)
    text = unicodedata.normalize("NFKC", text)
    text = RE_ABNORMAL_PARANTHESIS.sub("", text)
    text = text.strip()
    return text


def filter_paragraphs(
    paragraphs: Iterable[str], minimal_word_count: int = 5
) -> Iterator[str]:
    for paragraph in paragraphs:
        if len(RE_WORD.findall(paragraph)) >= minimal_word_count:
            yield paragraph


def filter_wiki_data(data: Iterable[dict]) -> Iterator[dict]:
    for article in data:
        if not article["text"] or ":" in article["title"]:
            continue
        text = normalize_text(article["text"])

        paragraphs = RE_PARAGRAPH_SPLIT.split(text)
        paragraphs = filter_paragraphs(paragraphs)

        yield {
            "url": article["url"],
            "title": article["title"],
            "paragraphs": list(paragraphs),
        }


def main(input_filename: str, output_filename: str):
    wiki_data = iter_jsonl(input_filename)
    filtered_data = filter_wiki_data(wiki_data)
    save_jsonl(filtered_data, output_filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input-filename",
        type=str,
        required=True,
        help="input jsonl file after wikiextractor processing",
    )
    parser.add_argument(
        "-o", "--output-filename", type=str, help="output jsonl filename"
    )

    main(**vars(parser.parse_args()))
