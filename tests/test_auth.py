"""Offline tests for auth.py: PBKDF2-SHA256 hashing."""
from auth import hash_password, verify_password
from chat_storage import VALID_ROLES


def test_hash_verify_roundtrip():
    stored = hash_password("MySecurePass123")
    assert stored.count("$") == 2  # <iterations>$<salt_hex>$<hash_hex>
    assert verify_password("MySecurePass123", stored)


def test_wrong_password_rejected():
    stored = hash_password("MySecurePass123")
    assert not verify_password("WrongPassword", stored)


def test_salt_makes_hashes_unique():
    a = hash_password("same-password")
    b = hash_password("same-password")
    assert a != b
    assert verify_password("same-password", a)
    assert verify_password("same-password", b)


def test_malformed_stored_hash_returns_false():
    assert not verify_password("x", "not-a-hash")
    assert not verify_password("x", "1$zz")  # only two parts
    assert not verify_password("x", "")      # empty


def test_valid_roles():
    assert set(VALID_ROLES) == {"staff", "supervisor", "manager"}