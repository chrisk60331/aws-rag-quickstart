# Define custom function directory
ARG FUNCTION_DIR="/function"

FROM python:3.12.7-slim-bullseye as build-image
# Include global arg in this stage of the build
ARG FUNCTION_DIR
# Set working directory to function root directory
WORKDIR ${FUNCTION_DIR}

# Copy function code
RUN mkdir -p ${FUNCTION_DIR}
COPY requirements.txt .
RUN pip install -r requirements.txt

FROM build-image as bedrock

# Include global arg in this stage of the build
ARG FUNCTION_DIR
RUN pip install awslambdaric

# Copy in the built dependencies
COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}
ADD src ${FUNCTION_DIR}/src

# Set runtime interface client as default command for the container runtime
ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]
# Pass the name of the function handler as an argument to the runtime
CMD [ "AgentLambda.main" ]

FROM build-image as opensearch

# Include global arg in this stage of the build
ARG FUNCTION_DIR
RUN pip install awslambdaric

RUN apt-get update -y
RUN apt-get install -y poppler-utils
# Copy in the built dependencies
COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}
ADD src ${FUNCTION_DIR}/src

# Set runtime interface client as default command for the container runtime
ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]
# Pass the name of the function handler as an argument to the runtime
CMD [ "IngestionLambda.main" ]

FROM build-image as ecsopensearch

# Include global arg in this stage of the build
ARG FUNCTION_DIR

# Copy in the built dependencies
COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}
RUN apt-get update -y
RUN apt-get install -y poppler-utils
RUN pip install "uvicorn[standard]" "fastapi[standard]"

ADD src ${FUNCTION_DIR}/src

# Pass the name of the function handler as an argument to the runtime
CMD [ "uvicorn", "src.fast_api_wrapper:app", "--host", "0.0.0.0", "--port", "80", "--workers", "20" ]

FROM build-image as ollamallm
RUN apt-get update -y
RUN apt-get install -y curl
RUN curl -L https://ollama.com/download/ollama-linux-arm64.tgz -o ollama-linux-arm64.tgz
RUN tar -C /usr -xzf ollama-linux-arm64.tgz
RUN pip install "huggingface_hub[cli]"
CMD ollama serve
