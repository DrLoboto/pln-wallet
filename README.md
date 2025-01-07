# Test project: Wallet

REST API in Python that allows users to track the current Polish złoty (PLN) value of their money held in different foreign currencies.

## Features
* **Wallet Management**: Users can define how much money they have in various foreign currencies.
* **Real-Time Currency Conversion**: The system will convert these amounts into their PLN equivalent using current exchange.
* **PLN Value Calculation**: For each currency in the user’s wallet, the system will return its PLN value and the total PLN amount of all currencies combined.

## Development environment

Recommended development setup is Python managed by [pyenv](https://github.com/pyenv/pyenv), globally installed [Poetry](https://python-poetry.org/) and package manager and [Docker Compose](https://docs.docker.com/compose/) for development environment setup.

### Installation

Assuming that Docker Compose is already installed project setup from scratch will be:

```bash
curl -fsSL https://pyenv.run | bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init - bash)"' >> ~/.bashrc
pyenv install 3.11.7
pyenv shell 3.11
curl -sSL https://install.python-poetry.org | python3 -
poetry env use 3.11
poetry install
```

Please refer to the respective tools installation instructions in case of any errors.

### Startup

Installed service could be started in a development docker container and in a
production-like docker container.

Development start:
```console
docker-compose up
```

API will be available as http://127.0.0.1:8080/ together with interactive documentation
at http://127.0.0.1:8080/docs. Authorization token could be aquired via running command
in a local installation or inside started container:

```console
poetry run token 123 write --ttl=15
```

This command will create auth token for user with ID `123`, write permissions and 15
minutes TTL. Provide this token via "Authorize" button on interactive docs page. All
options description is available via help: `poetry run token --help`.

Start as production-like docker container:
```console
docker-compose --profile=deployment up
```

In this case the API will be available as http://127.0.0.1:8000/ (note port **8000**),
interactive documentation won't be available and internal errors won't be returned in
responses. The token issue command won't be available as well since production container
does not posess private key.

> [!IMPORTANT]
> Both development and production containers use single database since production
> startup is implemented as a demostration only. So changes you done via one app are
> visible in the other.

> [!TIP]
> Both containers and a development environment expect tokens to be signed by the single
> key, so you can issue auth token via installed code or development container and use
> it with production API.

### Development

For the development process support there are several tools installed:
* [Ruff](https://docs.astral.sh/ruff/) as linter and formatter
* [MyPy](https://mypy-lang.org/) as static type checker
* [pytest](https://docs.pytest.org/en/stable/) as testing framework

To run everything at once:
```console
poetry run ruff check --fix ; poetry run ruff format && poetry run mypy . && poetry run pytest
```

> [!NOTE]
> PyTest starts docker dev environment plus separate DB instance for tests only. First
> start will take time since all images must be downloaded and app container built. But
> subsequent test starts would be immediate.

## Production deployment

It is assumed that for non-local deployments the Docker image will be built as simple as
`docker build .` and deployed to the target environment providing environment variables
on container start. This way only default (and mostly static) settings are built inside
an image so it can be promoted between environment after testing.

## Implementation

Below are some details on implementation decisions.

### Web framework

The [FastAPI](https://fastapi.tiangolo.com/) is chosen for web framework as is the most
popular one nowdays and its usage was marked as preferred.

### Configuration

Configuration is managed by [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/).
This tool is chosen to keep same dataclasses/models lib for everything in the app. Plus
it give fast start when there are just couple of settings needed.

Supported configuration keys and their default values are listed in [Settings](/wallet/config.py)
model. Dev environment uses [.env](/.env) file to setup required and overrided values.
On deployment (see `prod-app` service in [docker-compose.yaml](/docker-compose.yaml))
these values are provided by environment variables instead of `.env` file.

### Authorization

It is assumed that this service is only a part of bigger application and there is some
authetication service providing users with OAuth tokens to access sub-services. These
tokens are signed and public part of signing key is shared with Wallet API service. Also
it is assumed that users management system assigns them integer IDs.

In this implementation Wallet API checks performs only basic token validation. Token
must:
* be parsable;
* contain `iat` and `exp` claims;
* be not expired;
* contain `sub` claim with an integer inside;
* contain `aud` claim with audience matching configured one (tokens with multiply audiences are allowed);
* contain `scopes` claim with "read" or "write" (or both) depending on endpoint requested.

All endpoinds are secured except documentation and OpenAPI file ones.

### Currencies operations

Available operations:
* view whole wallet: `GET /wallet`
* view one currency: `GET /wallet/{currency}`
* add amount to the currency: `POST /wallet/{currency}/add/{amount}`
* substract amount from the currency: `POST /wallet/{currency}/sub/{amount}`
* remove currency from the wallet: `DELETE /wallet/{currency}`

Only currencies having exchange rates provided by Narodowy Bank Polski are supported. It
is not required to have today exchange rate, the last one available is used. In case
some currency was added to the wallet and then NBP terminated its exchange support, this
currency will be displayed without PLN amount, rate and rate date. It could be removed
from wallet, but not updated.

### Data storage

[PostrgeSQL](https://www.postgresql.org/) is chosen for the data storage as the most
popular SQL database currently. The ORM of choice is [SQLModel](https://sqlmodel.tiangolo.com/)
being an [SQLAlchemy](https://docs.sqlalchemy.org/) (most popular ORM) adapted specially
for [FastAPI](https://fastapi.tiangolo.com/) and [Pydantic](https://docs.pydantic.dev/)
models.
