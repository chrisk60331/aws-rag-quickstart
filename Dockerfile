# Define custom function directory
ARG FUNCTION_DIR="/function"

FROM python:3.12.7-slim-bullseye as build-image
# Include global arg in this stage of the build
ARG FUNCTION_DIR
# Set working directory to function root directory
WORKDIR ${FUNCTION_DIR}

# Copy function code
RUN mkdir -p ${FUNCTION_DIR}
# Install uv for package management
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml README.md ${FUNCTION_DIR}/
# Create directory structure and copy source files properly
RUN mkdir -p ${FUNCTION_DIR}/src/aws_rag_quickstart
COPY src/aws_rag_quickstart ${FUNCTION_DIR}/src/aws_rag_quickstart/

# Install dependencies using uv
RUN uv venv
RUN uv pip install -e .

FROM build-image as local-stack-setup

RUN apt-get update
RUN apt-get install -y curl unzip less
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip && ./aws/install
RUN uv pip install awscli-local
ENV AWS_ENDPOINT_URL=http://local-stack:4566
COPY data ${FUNCTION_DIR}/data
CMD awslocal s3api create-bucket --bucket aoss-qa-dev-data-bucket --region us-west-1 --profile localstack \
--create-bucket-configuration '{"LocationConstraint": "us-west-1"}' && \
for i in data/*; do awslocal s3 cp $i s3://aoss-qa-dev-data-bucket/ --profile localstack; done

FROM build-image as bedrock

# Include global arg in this stage of the build
ARG FUNCTION_DIR
RUN pip install awslambdaric

# Copy in the built dependencies
COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}

# Set runtime interface client as default command for the container runtime
ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]
# Pass the name of the function handler as an argument to the runtime
CMD [ "src.aws_rag_quickstart.AgentLambda.main" ]

FROM build-image as opensearch

# Include global arg in this stage of the build
ARG FUNCTION_DIR
RUN pip install awslambdaric

RUN apt-get update -y
RUN apt-get install -y poppler-utils
# Copy in the built dependencies
COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}

# Set runtime interface client as default command for the container runtime
ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]
# Pass the name of the function handler as an argument to the runtime
CMD [ "src.aws_rag_quickstart.IngestionLambda.main" ]

FROM build-image as ecsopensearch

# Include global arg in this stage of the build
ARG FUNCTION_DIR
RUN apt-get update -y
RUN apt-get install -y curl
# Copy in the built dependencies
COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}
RUN apt-get update -y
RUN apt-get install -y poppler-utils
# Install uvicorn and fastapi with regular pip to ensure proper PATH configuration
RUN uv pip install "uvicorn[standard]" "fastapi[standard]"

# Set PYTHONPATH to include the function directory
ENV PYTHONPATH=${FUNCTION_DIR}:${PYTHONPATH}

# Pass the name of the function handler as an argument to the runtime
CMD [ "uv", "run", "uvicorn", "aws_rag_quickstart.fast_api_wrapper:app", "--host", "0.0.0.0", "--port", "80", "--workers", "20" ]

FROM build-image as ollamallm
RUN apt-get update -y
RUN apt-get install --no-install-recommends -y curl
RUN curl -L https://ollama.com/download/ollama-linux-arm64.tgz -o ollama-linux-arm64.tgz
RUN tar -C /usr -xzf ollama-linux-arm64.tgz
RUN pip install --no-cache-dir "huggingface_hub[cli]==0.26.2"
CMD ["ollama", "serve"]
