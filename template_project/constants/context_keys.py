"""Keys used to store request-scoped values in the context registry."""


class ContextKeys:
    """Frozen key names for :class:`template_project.context.Context`."""

    CURRENT_USER: str = "current_user"
    REQUEST_ID: str = "request_id"
