# AWS GenAI RAG Quick Start
<img src="img/aws_rag.jpg" width="90%"/>

This is the PDF Q&A repo, providing functionality for:
- Metadata augmentation
- Metadata storage via opensearch
- Document retrieval via an LLM agent

# Local Testing
<img src="img/ragstart.jpg" width="90%"/>

This repo includes local LLM, localstack for aws, opensearch, and fastapi for local, E2E, functional testing!
## Prerequisites
- Docker and docker-compose installed
  - Be sure to max out resource allocation in docker preferences
- Clone this repo locally

**_NOTE:_** the local LLM is small and not multimodal, so it doesn't do well on image Q&A. 
## Testing
### Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```
[TFLint](https://github.com/terraform-linters/tflint) required for terraform_tflint hook
[Hadolint](https://github.com/hadolint/hadolint) required for hadolint hook

### To run unit tests
```bash
PYTHONPATH=. python -m pytest tests/unit_tests.py
```
### Run coverage
```bash
coverage erase && \
coverage run -m pytest tests/unit_tests.py && \
coverage report --show-missing
```
### Linting
```bash
black -l79 src tests
isort -l79 --profile black src tests
pylama src tests
tflint
terraform_fmt
```
### Pre-commit
```bash
pre-commit install
pre-commit run --all-files
```
### Local Functional Testing Steps
1. Run:
```bash
for i in local-stack-setup ollamallm ecsopensearch; do \
  docker build -q --target $i -t $i":latest" .; done && \
  docker-compose up -d --quiet-pull && \
  while (wget -q --spider localhost/docs||false); do break;done && \
  ECS_HOST_IP=localhost DELETE=0 python tests/LambdaE2E.py
```
2. Navigate to http://0.0.0.0/docs
3. Test Each interface

<img src="img/fastapi.png" width="30%"/>

### Index State
To check the index state  - go to the local OpenSearch dashboard - http://localhost:5601/app/home#/  - menu on the left -> Index management -> Indexes.

# Deploy
## Credentials
we use saml2aws
```bash
brew install saml2aws
saml2aws configure 
saml2aws login 
```
## Terraform Remote State
```bash
cd terraform/remote_state
terraform init
terraform apply
```
### Terraform Deploy
```bash
cd ../live/dev
terraform init
terraform apply --auto-approve
```
terraform.tfvars values
```bash
account_id="aws_account_id"
bedrock_image_uri="aws_account_id.dkr.ecr.region_name.amazonaws.com/aws-rag/bedrock:latest"
opensearch_image_uri="aws_account_id.dkr.ecr.us-east-1.amazonaws.com/aws-rag/opensearch:latest"
ecs_opensearch_image_uri="aws_account_id.dkr.ecr.region_name.amazonaws.com/aws-rag/ecsopensearch:latest"
region_name="us-east-1"
customer="Test" # for tagging
creator="cking" # for tagging
```

