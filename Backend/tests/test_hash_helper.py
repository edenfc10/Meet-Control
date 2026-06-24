from app.security.hashHelper import HashHelp


def test_hash_and_verify_password_success():
    plain = "StrongPass123!"
    hashed = HashHelp.get_password_hash(plain)

    assert hashed != plain
    assert HashHelp.verify_password(plain, hashed) is True


def test_hash_and_verify_password_failure():
    hashed = HashHelp.get_password_hash("StrongPass123!")

    assert HashHelp.verify_password("WrongPass123!", hashed) is False
