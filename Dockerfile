FROM python:3.8-slim
LABEL maintainer="Jimmy Zelinskie <jimmyzelinskie+git@gmail.com>"

WORKDIR /usr/src/app

RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-dev

ENTRYPOINT ["poetry", "run", "python", "-m", "reflexd.bin.reflexd"]
CMD ["watch"]

COPY . .

RUN poetry install --no-dev
