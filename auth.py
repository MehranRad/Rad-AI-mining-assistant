"""
Password hashing utilities for user authentication.
Uses PBKDF2-HMAC-SHA256 via Python's built-in hashlib — no external
dependencies (avoids native-build issues like argon2-cffi on Windows).
"""
import hashlib
import os
import hmac

PBKDF2_ITERATIONS = 260_000  # OWASP-recommended minimum for PBKDF2-SHA256 as of 2023


def hash_password(password: str) -> str:
    """
    Returns a single string combining the algorithm parameters, salt, and
    hash, safe to store in one database column.
    Format: "<iterations>$<salt_hex>$<hash_hex>"
    """
    salt = os.urandom(16)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"{PBKDF2_ITERATIONS}${salt.hex()}${pw_hash.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """
    Verifies a password against a stored hash string produced by hash_password().
    Uses constant-time comparison (hmac.compare_digest) to avoid timing attacks.
    Returns False (never raises) if the stored string is malformed.
    """
    try:
        iterations_str, salt_hex, hash_hex = stored.split("$")
        iterations = int(iterations_str)
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
    except (ValueError, AttributeError):
        return False

    actual_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual_hash, expected_hash)


if __name__ == "__main__":
    # Standalone self-test — run with: python auth.py
    print("Testing password hashing...")

    test_password = "MySecurePass123"
    stored = hash_password(test_password)
    print(f"Stored hash string: {stored}")
    print(f"Stored hash length: {len(stored)} chars")

    result_correct = verify_password(test_password, stored)
    print(f"Correct password verifies: {result_correct} (expected: True)")

    result_wrong = verify_password("WrongPassword", stored)
    print(f"Wrong password verifies: {result_wrong} (expected: False)")

    stored2 = hash_password(test_password)
    print(f"Two hashes of same password are different: {stored != stored2} (expected: True)")
    print(f"But both still verify correctly: {verify_password(test_password, stored2)} (expected: True)")

    if result_correct and not result_wrong and stored != stored2:
        print("\nALL TESTS PASSED")
    else:
        print("\nSOME TESTS FAILED — see above")