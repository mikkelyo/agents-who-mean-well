"""User-facing strings, kept out of the code that emits them."""


class StaticMessages:
    """Messages returned to callers or written to logs."""

    HEALTH_OK: str = "OK"
    MISSING_CURRENT_USER: str = "No authenticated user is bound to this request."
    INVALID_API_KEY: str = "The supplied API key is not valid."
    INVALID_PAYLOAD: str = "The request payload is invalid."
    EMPTY_PROMPT: str = "The prompt must not be empty."
    COMPLETION_FAILED: str = "The language model did not return an answer."
    UNEXPECTED_ERROR: str = "An unexpected error occurred."
