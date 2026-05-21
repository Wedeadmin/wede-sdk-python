class WedeError(Exception):
    def __init__(self, message: str, code: str, status: int = None):
        super().__init__(message)
        self.code = code
        self.status = status

class WedeAuthError(WedeError):
    def __init__(self, message: str = "Invalid or missing API key"):
        super().__init__(message, "auth_error", 401)

class WedeNetworkError(WedeError):
    def __init__(self, message: str = "Network request failed"):
        super().__init__(message, "network_error")

class WedeValidationError(WedeError):
    def __init__(self, message: str):
        super().__init__(message, "validation_error", 400)
