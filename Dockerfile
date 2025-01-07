FROM python:3.11-slim

WORKDIR /wallet

COPY ./pyproject.toml ./poetry.lock ./README.md /wallet/

RUN apt-get update && apt-get upgrade -y && \
    apt install curl -y && \
    pip install -U pip && \
    pip install poetry==1.8.4 && \
    poetry install --only main --no-root --no-directory && \
    poetry cache clear --all -n pypi && \
    apt autoremove -y && \
    apt clean -y && \
    find / -name "*.pyc" -or -name "*.whl" -delete

COPY ./wallet /wallet/wallet
RUN poetry install --only main

CMD [ "poetry", "run", "service" ]
