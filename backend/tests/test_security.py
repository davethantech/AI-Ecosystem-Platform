from app.security import hash_password, verify_password

def test_password_hash_round_trip():
    hashed = hash_password("a long test password")
    assert hashed != "a long test password"
    assert verify_password("a long test password", hashed)
    assert not verify_password("wrong password", hashed)
