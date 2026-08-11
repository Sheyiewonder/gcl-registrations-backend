class AppException(Exception):
    """Base application exception."""


class NotFoundError(AppException):
    """Raised when a resource cannot be found."""


class EventNotFoundError(NotFoundError):
    """Raised when an event does not exist."""


class EventInactiveError(AppException):
    """Raised when an event is inactive."""


class DuplicateRegistrationError(AppException):
    """Raised when a duplicate registration is detected."""