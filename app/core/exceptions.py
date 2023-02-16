import re

import humps
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from httpx import Response as httpxResponse
from sentry_sdk import capture_exception
from starlette.exceptions import HTTPException


class ApiException(Exception):
    name: str

    def __init__(
        self,
        message: str = "",
        status_code: int = 400,
        app: str | None = None,
        code: str | None = None,
    ) -> None:
        super().__init__(message)
        if not app:
            class_name = str(self.__class__.__name__)
            app = re.sub(r"([A-Z])", r" \1", class_name).split()[0].lower()

        self.message = message
        self.status_code = status_code
        self.app = app
        if code:
            self.name = code

    @property
    def error_code(self) -> str:
        return f"{self.app}_{getattr(self, 'name', '')}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ApiException):
            return False

        return (
            self.error_code == other.error_code
            and self.message == other.message
            and self.status_code == other.status_code
        )

    def __str__(self) -> str:
        return f"{self.error_code}: {self.message} ({self.status_code})"

    def to_response(self) -> ORJSONResponse:
        return ORJSONResponse(
            humps.camelize({"error_code": self.error_code, "message": self.message}),
            status_code=self.status_code,
        )

    @classmethod
    def from_response(cls, response: httpxResponse) -> "ApiException":
        content_json = humps.decamelize(response.json())
        app, code = content_json["error_code"].split("_", 1)
        return cls(
            message=content_json["message"],
            status_code=response.status_code,
            app=app,
            code=code,
        )


def api_exception_handler(request: Request, exc: ApiException) -> Response:
    return exc.to_response()


def http_exception_handler(request: Request, exc: HTTPException) -> Response:
    return ApiException(str(exc), 400, "app", "http").to_response()


def validation_error_handler(request: Request, exc: RequestValidationError) -> Response:
    return ApiException(str(exc), 400, "app", "validation").to_response()


def exception_handler(request: Request, exc: Exception) -> Response:
    capture_exception(exc)
    return ApiException(str(exc), 500, "app", "generic").to_response()


def setup_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiException, api_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, exception_handler)
