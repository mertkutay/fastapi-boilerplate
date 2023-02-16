# FastAPI Boilerplate

## Commands

- docker-compose alias `./run`
- Building the project `./run build`
- Running the project `./run up -d`
- Observing the logs `./run logs api`
- Launching a bash shell `./run shell api`
- Launching an ipython shell `./run ipython api`
- Using aerich commands `./run aerich`
- Running unit tests `./run test`
- Formatting the codebase `./run format`
- Updating translation catalogs `./run update-messages`
- Compiling MJML templates `./run compile-emails`

## Stack

- API: FastAPI
- Serialization: Pydantic
- Database: Postgresql
- ORM: Tortoise, Aerich
- Cache: Redis
- Authentication: jose (JWT), passlib (argon2)
- Server: uvicorn, gunicorn
- Dependencies: Poetry
- Linting: ruff, mypy
- Formatting: black, isort
- Code quality: pre-commit
- HTTP: aiohttp
- Unit Tests: pytest, faker, factory-boy
- Error reporting: Sentry
- Email: emails (smtp)
- Localization: pybabel, gettext
- Mail templates: MJML
- Geolocation: GeoIP2

## References

Modified versions of some modules from below projects are included

- [Full Stack FastAPI and PostgreSQL](https://github.com/tiangolo/full-stack-fastapi-postgresql)
- [FastAPI Users](https://github.com/fastapi-users/fastapi-users)
- [FastAPI Cache](https://github.com/long2ice/fastapi-cache)
- [FastAPI Limiter](https://github.com/long2ice/fastapi-limiter)
