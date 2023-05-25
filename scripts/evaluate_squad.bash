#!/bin/bash

data_directory=${1:-"./data"}

set -x -e

# Download dev data
curl https://rajpurkar.github.io/SQuAD-explorer/dataset/dev-v2.0.json --output "${data_directory}"/squad-2.0-dev.json

# Run data preprocessing scripts
python ./scripts/preprocess_squad_data.py \
    --input "${data_directory}"/squad-2.0-dev.json \
    --output "${data_directory}"/squad

docker-compose up --build -d

# Initialize service and add knowledge data
brainlet init --overwrite
brainlet index --source "${data_directory}"/squad/knowledge-base.jsonl --progress

# Find questions and store them into answers file
brainlet inference \
    --questions-file "${data_directory}"/squad/questions.jsonl \
    --output-file "${data_directory}"/squad/answers.jsonl \
    --progress

docker-compose down

# Calculate metrics
python ./scripts/evaluate_squad.py \
    "${data_directory}"/squad/squad-2.0-dev.json \
    "${data_directory}"/squad/answers.jsonl