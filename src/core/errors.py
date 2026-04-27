class NatureError(Exception):
    """Base error for structured application failures."""


class InvalidInput(NatureError):
    """Input data is missing, malformed, or unsupported."""


class InvalidConfig(NatureError):
    """Configuration is missing or invalid."""


class UnsafePath(NatureError):
    """A path escapes an allowed boundary."""
