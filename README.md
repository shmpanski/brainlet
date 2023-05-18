# 🧠 brainlet 

[![CI](https://github.com/shmpanski/brainlet/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/shmpanski/brainlet/actions/workflows/main.yml)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

_let's search_

## Installation
Local installation via pip:
```shell
git clone https://github.com/shmpanski/brainlet.git && cd brainlet
pip install .
```

## How it works
The service is based on the [weaviate](https://weaviate.io/) framework.
The inference of semantic encoders and extractive QA is implemented via weaviate modules [`text2vec-transformers`](https://weaviate.io/developers/weaviate/modules/retriever-vectorizer-modules/text2vec-transformers) and [`qna-transformers`](https://weaviate.io/developers/weaviate/modules/reader-generator-modules/qna-transformers).
The web service API is implemented using FastAPI.

### Data
The service requires text knowledge base.
For the project, we assume that it follows the next `jsonl` format:
```json
{
  "url": "https://any-link-to-your-original-knowledge",
  "title": "title of document",
  "paragraphs": [
    "text paragraph #1",
    "text paragraph #2",
    "..."
  ]
}
```

### Initialization
First, you need to run the inference, index, storage, and API services:
```shell
docker-compose up --build
```

Second, you need to initialize the data schema and start data indexing.
There is a CLI interface for this (a list of all commands is available in `brainlet --help`):
```shell
# Initialize the data schema
brainlet init
# Import data
brainlet index --source data/enwiki.jsonl --progress
```

There is no third step. 
You can go to http://0.0.0.0/docs (default) and look how the client works.

### Under the hood

Question Answering based on the text knowledge base is done in several steps:
1. Search for the most relevant document from the knowledge base using hybrid search. Hybrid search includes ranking based on BM25 and `mutli-qa-MiniLM-L6` semantic encoding.
2. Find the most relevant paragraph of the document using the same semantic encoder `mutli-qa-MiniLM-L6`.
3. Use `bert-large-finetuned-squad` to find spans of the most likely answer.

## end-to-end wikipedia example:

Install additional requirements:
```shell
pip install ".[dev]"
# OR
pip install wikiextractor~=3.0.6
```

Prepare data:
```shell
# Download dump:
curl -O --output-dir ./data --create-dirs https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles-multistream1.xml-p1p41242.bz2

# Export wiki dump to json:
wikiextractor ./data/enwiki-latest-pages-articles-multistream1.xml-p1p41242.bz2 \
    --json --no-templates --output - \
    > ./data/enwiki-latest-pages-articles-multistream1.p1p41242.jsonl

# Preprocess data for suitable format:
python ./scripts/preprocess_wiki_data.py \
   --input ./data/enwiki-latest-pages-articles-multistream1.p1p41242.jsonl \
   --output ./data/enwiki.jsonl
```

Run all services using docker-compose:
```shell
docker-compose up --build
```

Create schema and import your data:
```shell
brainlet init && brainlet index --source data/enwiki.jsonl --progress
```

After a while, you can make a request (it is not necessary to wait for the end of indexing, it is done in the background):
```shell
curl -X 'GET' \
  'http://0.0.0.0/?question=what%20is%20anarchism%3F' \
  -H 'accept: application/json'
```

Fortunately, you will get an answer to the question:
```json
{
  "has_answer": true,
  "source": {
    "title": "Anarchism",
    "url": "https://en.wikipedia.org/wiki?curid=12"
  },
  "support_text": "Anarchism is a political philosophy and movement that is skeptical of all justifications for authority and seeks to abolish the institutions it claims maintain unnecessary coercion and hierarchy, typically including, though not necessarily limited to, governments, nation states, and capitalism. Anarchism advocates for the replacement of the state with stateless societies or other forms of free associations. As a historically left-wing movement, this reading of anarchism is placed on the farthest left of the political spectrum, it is usually described as the libertarian wing of the socialist movement (libertarian socialism).",
  "answer": "a political philosophy and movement that is skeptical of all justifications for authority",
  "certainty": 0.48392624855041505
}
```

## Testing

```shell
pip install ".[dev]"
docker-compose up -d weaviate
pytest tests
```