class InsecureKeyringError(RuntimeError):
    pass


class AuthError(Exception):
    pass


class ConnectionFailure(Exception):
    pass


class ParseError(Exception):
    pass
