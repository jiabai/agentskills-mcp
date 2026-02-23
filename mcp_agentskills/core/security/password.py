import hashlib
import hmac
import secrets


ITERATIONS = 260000


def _encode(password: str, salt: str, iterations: int) -> str:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations)
    return dk.hex()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        scheme, iterations_str, salt, digest = hashed_password.split("$", 3)
    except ValueError:
        return False
    if scheme != "pbkdf2_sha256":
        return False
    try:
        iterations = int(iterations_str)
    except ValueError:
        return False
    calculated = _encode(plain_password, salt, iterations)
    return hmac.compare_digest(calculated, digest)


def get_password_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = _encode(password, salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${salt}${digest}"
