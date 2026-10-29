from app.schemas import Register
from pydantic import ValidationError
import pytest

def test_short_password_rejected():
    with pytest.raises(ValidationError):
        Register(email="user@example.com", password="weak", organization="Team")

def test_weak_password_rejected():
    with pytest.raises(ValidationError):
        Register(email="user@example.com", password="alllowercase123", organization="Team")
