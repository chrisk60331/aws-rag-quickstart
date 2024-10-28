# AWS GenAI RAG Quick Start

This is the PDF Q&A repo, providing functionality for:
- Metadata augmentation
- Metadata storage via opensearch
- Document retrieval via an LLM agent

# Local Testing
## Prerequisites
- AWS access to account.
- Docker and docker-compose installed
## Local Unit Testing
Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```
To run unit tests
```bash
PYTHONPATH=. pytest tests/unit_tests.py
```
Run coverage
```bash
coverage erase && coverage run -m pytest tests/unit_tests.py && coverage report --show-missing
```
## Local Functional Testing Steps
1. Clone the repository
2. Run ```docker-compose up``` in the root directory of the repository
3. Navigate to http://0.0.0.0/docs
4. Test Each interface

## Index State
To check the index state  - go to the local OpenSearch dashboard - http://localhost:5601/app/home#/  - menu on the left -> Index management -> Indexes.

# Local and Remote End to End (E2E) Testing
To run end-to-end tests
```bash
ECS_HOST_IP=localhost CREATE=1 DELETE=1  python tests/LambdaE2E.py
ECS_HOST_IP=localhost DELETE=1 python tests/LambdaE2E_summarization.py
```
# Local and Remote Perf Testing
To run end-to-end tests
```bash
python tests/perf_test.py
```
## Linting
```bash
black -l79 src
isort -l79 --profile black src
pylama
```
## Pre-commit
```bash
pre-commit install
pre-commit run --all-files
```

# Deploy
## Terraform
1. run ```cd terraform/live/dev```
2. run ```terraform init```
3. run ```terraform plan -out out.plan```
4. run ```terraform apply out.plan```
## Docker Build
```bash
for i in bedrock opensearch; do \
  docker build --target $i -t $i":latest" . && \
  docker tag $i":latest" ".dkr.ecr.us-east-1.amazonaws.com/cvos/$i"":latest" && \
  docker push "\.dkr.ecr.us-east-1.amazonaws.com/cvos/$i"":latest" && \
  aws lambda update-function-code --function-name lambda-function-$i-aoss-qa-dev \
  --image-uri ".dkr.ecr.us-east-1.amazonaws.com/cvos/$i"":latest" \
  --profile default --no-cli-pager;done
for i in ecsopensearch; do \
  docker build --target $i -t $i":latest" . && \
  docker tag $i":latest" ".dkr.ecr.us-east-1.amazonaws.com/cvos/$i"":latest" && \
  docker push ".dkr.ecr.us-east-1.amazonaws.com/cvos/$i"":latest"; \
  done
```