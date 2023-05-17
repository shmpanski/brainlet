import os

import pytest
from weaviate import Client

from brainlet.core import create_schema, import_data, ask_question

WEAVIATE_CLIENT_URL = os.getenv("WEAVIATE_CLIENT_URL", "http://127.0.0.1:8080")


@pytest.fixture(scope="session")
def weavite_client() -> Client:
    return Client(WEAVIATE_CLIENT_URL)


@pytest.fixture(scope="function")
def client(weavite_client):
    weavite_client.schema.delete_all()
    yield weavite_client
    weavite_client.schema.delete_all()


@pytest.fixture(scope="session")
def test_data():
    return [
        {
            "url": "https://en.wikipedia.org/wiki?curid=12",
            "title": "Anarchism",
            "paragraphs": [
                "Anarchism is a political philosophy and movement that is skeptical of all justifications for "
                "authority and seeks to abolish the institutions it claims maintain unnecessary coercion and "
                "hierarchy, typically including, though not necessarily limited to, governments, nation states, "
                "and capitalism.",
                "Anarchism advocates for the replacement of the state with stateless societies or other forms of free "
                "associations.",
                "As a historically left-wing movement, this reading of anarchism is placed on the farthest left of "
                "the political spectrum, it is usually described as the libertarian wing of the socialist movement ("
                "libertarian socialism).",
            ],
        }
    ]


def test_create_default_schema(client: Client):
    create_schema(client)
    assert client.schema.exists("Document")
    assert client.schema.exists("Paragraph")


def test_create_default_schema_overwrite(client: Client):
    create_schema(client)
    with pytest.raises(RuntimeError):
        create_schema(client)

    create_schema(client, overwrite=True)
    assert client.schema.exists("Document")
    assert client.schema.exists("Paragraph")


def test_import_data(client, test_data):
    create_schema(client)
    import_data(client, test_data)

    assert (
        len(client.query.get("Document", "title").do()["data"]["Get"]["Document"]) == 1
    )
    assert (
        len(client.query.get("Paragraph", "text").do()["data"]["Get"]["Paragraph"]) == 3
    )


def test_ask_question(client, test_data):
    create_schema(client)
    import_data(client, test_data)

    answer = ask_question(client, "What is an anarchism?")

    assert answer.has_answer
    assert answer.support_text
    assert answer.answer
    assert answer.certainty > 0


def test_ask_question_not_found(client, test_data):
    create_schema(client)
    import_data(client, test_data)

    answer = ask_question(client, "You shouldn't find any answers. Really.")

    assert not answer.has_answer
    assert answer.support_text is None
    assert answer.answer is None
    assert answer.certainty is None
