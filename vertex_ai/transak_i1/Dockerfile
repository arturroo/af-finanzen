# Base Image
FROM us-docker.pkg.dev/deeplearning-platform-release/gcr.io/tf2-cpu.2-17.py310

WORKDIR /app

ENV PYTHONPATH="${PYTHONPATH}:/app"

COPY . .

RUN pip install uv

RUN uv pip install --system .[all]

# Entrypoint (Optional but good practice)
# For a Vertex AI custom component, the command to run is specified in the
# component definition itself, but setting an entrypoint is good practice
# for testing the container interactively.
ENTRYPOINT ["python"]
