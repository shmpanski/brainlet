import json
from dataclasses import dataclass
from typing import Iterator, Iterable, Union, Optional

import weaviate
from tqdm import tqdm
from weaviate.util import generate_uuid5

# This schema describes data storage, index and ann-search setting.
DEFAULT_SCHEMA = {
    "classes": [
        {
            "class": "Document",
            "properties": [
                {
                    "name": "url",
                    "dataType": ["string"],
                    "indexInverted": False,
                    "moduleConfig": {"text2vec-transformers": {"skip": True}},
                },
                {
                    "name": "title",
                    "dataType": ["text"],
                    "indexInverted": True,
                    "moduleConfig": {
                        "text2vec-transformers": {
                            "skip": False,
                            "vectorizePropertyName": False,
                        }
                    },
                },
                {
                    "name": "text",
                    "dataType": ["text"],
                    "indexInverted": True,
                    "moduleConfig": {
                        "text2vec-transformers": {
                            "skip": False,
                            "vectorizePropertyName": False,
                        }
                    },
                },
                {"name": "hasParagraphs", "dataType": ["Paragraph"]},
            ],
            "vectorizer": "text2vec-transformers",
            "vectorIndexConfig": {
                "ef": -1,
                "efConstruction": 512,
                "maxConnections": 128,
            },
            "moduleConfig": {"text2vec-transformers": {"vectorizeClassName": False}},
        },
        {
            "class": "Paragraph",
            "properties": [
                {
                    "name": "text",
                    "dataType": ["text"],
                    "indexInverted": True,
                    "moduleConfig": {
                        "text2vec-transformers": {
                            "skip": False,
                            "vectorizePropertyName": False,
                        }
                    },
                },
                {
                    "name": "order",
                    "dataType": ["int"],
                    "moduleConfig": {"text2vec-transformers": {"skip": True}},
                },
                {"name": "inDocument", "dataType": ["Document"]},
            ],
            "vectorizer": "text2vec-transformers",
            "vectorIndexConfig": {
                "ef": -1,
                "efConstruction": 512,
                "maxConnections": 128,
            },
            "moduleConfig": {"text2vec-transformers": {"vectorizeClassName": False}},
        },
    ]
}


def iter_data(jsonl_filename: str) -> Iterator[dict]:
    with open(jsonl_filename) as file:
        for line in file:
            yield json.loads(line)


def create_schema(
    client: weaviate.Client, schema: Optional[dict] = None, overwrite: bool = False
):
    """
    Create weaviate data schema.

    Args:
        client: weaviate client.
        schema: data and index schema. If None, use `DEFAULT_SCHEMA`.
        overwrite: whether to force overwrite schema if one already exists.
    """
    if overwrite:
        client.schema.delete_all()

    schema = DEFAULT_SCHEMA if schema is None else schema

    for object_class in schema["classes"]:
        class_name = object_class["class"]
        if client.schema.exists(class_name):
            raise RuntimeError(
                f"Class {class_name} already exists. Remove all required classes before recreating schema"
            )

    client.schema.create(schema)


def import_data(
    client: weaviate.Client,
    source: Union[str, Iterable[dict]],
    batch_size: int = 8,
    progress: bool = False,
):
    """
    Import data into storage and index.

    Args:
        client: weaviate client.
        source: source of data. Can be a string path to jsonl file OR iterable of dict with specified format.
        batch_size: batch size. The most common value with CPU accelerator: batch_size=1.
        progress: whether to show progress during importing.
    """
    data = iter_data(source) if isinstance(source, str) else source

    if progress:
        # TODO: sorry for list, i'm too lasy to call `wc -l`.
        data = tqdm(list(data))

    with client.batch(batch_size=batch_size) as batch:
        for document in data:
            doc_uuid = generate_uuid5(document["url"])
            doc_object = {
                "title": document["title"],
                "text": "\n".join(document["paragraphs"]),
                "url": document["url"],
            }
            batch.add_data_object(doc_object, "Document", doc_uuid)

            for order, paragraph in enumerate(document["paragraphs"]):
                par_uuid = generate_uuid5(f'{document["url"]}#{order}')
                paragraph_object = {"text": paragraph, "order": order}
                batch.add_data_object(paragraph_object, "Paragraph", par_uuid)
                batch.add_reference(
                    doc_uuid, "Document", "hasParagraphs", par_uuid, "Paragraph"
                )
                batch.add_reference(
                    par_uuid, "Paragraph", "inDocument", doc_uuid, "Document"
                )


@dataclass
class Source:
    title: str
    url: str


@dataclass
class Answer:
    has_answer: bool
    source: Optional[Source] = None
    support_text: Optional[str] = None
    answer: Optional[str] = None
    certainty: Optional[float] = None


def ask_question(client: weaviate.Client, question: str) -> Answer:
    """
    Ask question.

    Args:
        client: weaviate client.
        question: string question.

    Returns: answer object. If answer is found, then :attr:`has_answer` has value `True`.

    """
    # Escape quotes, unfortunately, weaviate doesn't escape it.
    question = question.replace('"', '\\"')

    # Retrieve most relevant document using hybrid search
    relevant_documents = (
        client.query.get("Document", ["_additional {id}"])
        .with_hybrid(question)
        .with_limit(1)
        .do()
    )["data"]["Get"]["Document"]

    if not relevant_documents:
        return Answer(False)

    # Retrive most relevant paragraph and try to extract answer.
    relevant_article_id = relevant_documents[0]["_additional"]["id"]
    requested_properties = [
        "text",
        "inDocument {... on Document {title, url }}",
        "_additional {answer {hasAnswer certainty result startPosition endPosition} }",
    ]

    response = (
        client.query.get("Paragraph", requested_properties)
        .with_where(
            {
                "path": ["inDocument", "Document", "id"],
                "operator": "Equal",
                "valueString": relevant_article_id,
            }
        )
        .with_ask({"question": question, "properties": ["text"]})
        .with_limit(1)
        .do()
    )

    # Fetch answer result. What a mess... Working with graphql has never been so convenient.
    source_info = response["data"]["Get"]["Paragraph"][0]["inDocument"][0]
    support_text = response["data"]["Get"]["Paragraph"][0]["text"]
    answer = response["data"]["Get"]["Paragraph"][0]["_additional"]["answer"]

    if not answer["hasAnswer"]:
        return Answer(False)
    else:
        return Answer(
            True,
            Source(source_info["title"], source_info["url"]),
            support_text,
            answer["result"],
            answer["certainty"],
        )
