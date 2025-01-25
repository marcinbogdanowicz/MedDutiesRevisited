FROM public.ecr.aws/docker/library/python:3.12
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN pip install poetry
RUN poetry config virtualenvs.create false
COPY pyproject.toml poetry.lock /app
RUN poetry install --without linters

COPY . /app
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
