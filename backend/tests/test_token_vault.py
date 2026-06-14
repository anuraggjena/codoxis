from app.auth.token_vault import decrypt_token, encrypt_token


def test_token_vault_roundtrip():
    original = "gho_test_token_abc123"
    encrypted = encrypt_token(original)
    assert encrypted != original
    assert decrypt_token(encrypted) == original
