FROM python:3.9

WORKDIR /brainlet

COPY src /brainlet/src
COPY setup.py /brainlet

RUN pip install ".[dev]"

ENTRYPOINT ["uvicorn", "brainlet.app:app"]