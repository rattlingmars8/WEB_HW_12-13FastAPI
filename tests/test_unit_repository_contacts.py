import unittest
from unittest.mock import MagicMock, AsyncMock

from sqlalchemy import select, asc
from sqlalchemy.ext.asyncio import AsyncSession
from src.DB.models import Contact, User
from src.repository.contacts_repo import repo_get_contacts, get_specific_contact_belongs_to_user


class TestContactRepository(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.user = User(id=1, email="user@example.com")
        self.async_session = AsyncMock(spec=AsyncSession)

    async def test_get_specific_contact_belongs_to_user(self):
        contact_id = 1
        contact = Contact(id=contact_id, first_name="John", last_name="Doe", user_id=self.user.id)

        # Налаштовуємо повернення з бази даних для запиту
        result_mock = MagicMock()
        result_mock.scalar.return_value = contact
        self.async_session.execute.return_value = result_mock

        # Тестуєму функцію
        result_fnc = await get_specific_contact_belongs_to_user(contact_id, self.user, self.async_session)

        # Перевіряємо результат
        self.assertEqual(result_fnc, contact)

        # Перевіряємо, чи викликали метод execute з очікуваними аргументами
        self.async_session.execute.assert_called_once()
        #
        # Перевіряємо, чи викликали метод scalar
        result_mock.scalar.assert_called_once()
        #
        # Перевіряємо, чи викликали метод filter з очікуваними аргументами
        self.async_session.execute.assert_called_once_with(
            select(Contact).where(Contact.user_id == self.user.id).filter(Contact.id == contact_id)
        )










    # async def test_get_specific_contact_belongs_to_user(self):
    #     contact_id = 1
    #     contact = Contact(id=contact_id, first_name="John", last_name="Doe", user_id=self.user.id)
    #
    #     # Налаштовуємо повернення з бази даних для запиту
    #     result_mock = MagicMock()
    #     result_mock.scalar.return_value = contact
    #     self.async_session.execute.return_value = result_mock
    #
    #     # Тестуєму функцію
    #     result_fnc = await get_specific_contact_belongs_to_user(contact_id, self.user, self.async_session)
    #     print(result_fnc)
    #     print(contact)
    #     # Перевіряємо результат
    #     self.assertEqual(result_fnc, contact)
    #
    #     # Перевіряємо, чи викликали метод execute з очікуваними аргументами
    #     self.async_session.execute.assert_called_once()
    #     #
    #     # Перевіряємо, чи викликали метод scalar
    #     result_mock.scalar.assert_called_once()
    #     #
    #     # Перевіряємо, чи викликали метод filter з очікуваними аргументами
    #     self.async_session.execute.assert_called_once_with(
    #         select(Contact).where(Contact.user_id == self.user.id).filter(Contact.id == contact_id)
    #     )
