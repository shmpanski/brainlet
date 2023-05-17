# 🧠 brainlet 

[![CI](https://github.com/shmpanski/brainlet/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/shmpanski/brainlet/actions/workflows/main.yml)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

_let's search_

## Installation
Local installation:
```shell
pip install git+https://github.com/shmpanski/brainlet
```

## Running
Prepare some data. For example, wiki dump:
```shell
# Download dump:
curl -O --output-dir data --create-dirs https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles-multistream1.xml-p1p41242.bz2
# Export wiki dump to json:
wikiextractor ./data/enwiki-latest-pages-articles-multistream1.xml-p1p41242.bz2 \
    --json --no-templates -output - \
    > ./data/enwiki-latest-pages-articles-multistream1.p1p41242.jsonl
# Preprocess data for suitable format:
python scripts/preprocess_wiki_data.py \
   --input ./data/enwiki-latest-pages-articles-multistream1.p1p41242.jsonl \
   --output ./data/enwiki.jsonl
```

Run all services with docker-compose:
```shell
docker-compose up --build
```

Create schema and import your data:
```shell
brainlet init && brainlet index --source data/enwiki.jsonl --progress
```

## Testing

```shell
pip install ".[dev]"
docker-compose up -d weaviate
pytest tests
```