import os

import pytest
from weaviate import Client
from fastapi.testclient import TestClient

from brainlet.app import app
from brainlet.core import create_schema, import_data

WEAVIATE_CLIENT_URL = os.getenv("WEAVIATE_CLIENT_URL", "http://127.0.0.1:8080")

test_client = TestClient(app)

test_data = [
    {
        "url": "https://en.wikipedia.org/wiki?curid=12",
        "title": "Anarchism",
        "paragraphs": [
            "Anarchism is a political philosophy and movement that is skeptical of all justifications for authority "
            "and seeks to abolish the institutions it claims maintain unnecessary coercion and hierarchy, typically "
            "including, though not necessarily limited to, governments, nation states, and capitalism.",
            "Anarchism advocates for the replacement of the state with stateless societies or other forms of free "
            "associations.",
            "As a historically left-wing movement, this reading of anarchism is placed on the farthest left of the "
            "political spectrum, it is usually described as the libertarian wing of the socialist movement ("
            "libertarian socialism).",
        ],
    },
    {
        "url": "https://en.wikipedia.org/wiki?curid=39",
        "title": "Albedo",
        "paragraphs": [
            "Albedo  is the measure of the diffuse reflection of solar radiation out of the total solar radiation and "
            "measured on a scale from 0, corresponding to a black body that absorbs all incident radiation, to 1, "
            "corresponding to a body that reflects all incident radiation.",
            'Surface albedo is defined as the ratio of radiosity "J"e to the irradiance "E"e (flux per unit area) '
            "received by a surface.",
        ],
    },
]


@pytest.fixture(scope="session")
def weaviate_client():
    return Client(WEAVIATE_CLIENT_URL, startup_period=60)


@pytest.fixture(scope="session")
def weaviate_client_with_data(weaviate_client: Client):
    weaviate_client.schema.delete_all()
    create_schema(weaviate_client)
    import_data(weaviate_client, test_data)
    yield weaviate_client
    weaviate_client.schema.delete_all()


def test_ask(weaviate_client_with_data: Client):
    response = test_client.get("/", params={"question": "what is anarchism?"})
    assert response.status_code == 200
    assert response.json()["has_answer"]
    assert response.json()["answer"] == "a political philosophy and movement"
