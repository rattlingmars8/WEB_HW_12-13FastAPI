import pytest
from unittest.mock import MagicMock

from src.schemas.User_Schemas import UserCreationResponse


# @pytest.mark.usefixtures("db")  # Використовуємо фікстуру db перед запуском тесту
@pytest.mark.asyncio
async def test_register_user(client, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.services.email.send_email", mock_send_email)
    response = client.post("/auth/register", json=user)
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload['email'] == user.get("email")


@pytest.mark.asyncio
async def test_register_user_existing_email(client, user, monkeypatch):
    # Мокуємо функцію, що повертає існуючого користувача
    async def mock_repo_user_authentication_by_email(email, db):
        return True

    monkeypatch.setattr("src.repository.users_repo.repo_user_authentication_by_email",
                        mock_repo_user_authentication_by_email)

    response = client.post("/auth/register", json=user)

    assert response.status_code == 409
    assert "Email already exists. Try to log in." in response.json()["detail"]


# @pytest.mark.asyncio
# async def test_register_user_new_email(client, user, monkeypatch):
#     # Мокуємо функцію, що повертає неіснуючого користувача
#     async def mock_repo_user_authentication_by_email(email, db):
#         return None
#
#     monkeypatch.setattr("src.repository.users_repo.repo_user_authentication_by_email",
#                         mock_repo_user_authentication_by_email)
#
#     # Мокуємо функцію, яка завжди успішно зберігає користувача
#     async def mock_repo_create_user(body, db):
#         return UserCreationResponse(**user,
#                                     message="Your account created successfully. Check your email to activate it.")
#
#     monkeypatch.setattr("src.repository.users_repo.repo_create_user", mock_repo_create_user)
#
#     response = client.post("/auth/register", json=user)
#
#     assert response.status_code == 201
#     assert response.json()["email"] == user["email"]
