import datetime

from fastapi import HTTPException
from sqlalchemy import select, asc, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.DB.models import Contact, User
from src.schemas.Contacts_Schemas import ContactCreate, ContactUpdate


async def get_specific_contact_belongs_to_user(id: int, user: User, db: AsyncSession):
    """
    Отримати конкретний контакт, який належить користувачеві.

    Ця функція отримує конкретний контакт з бази даних, який належить користувачеві,
    із вказаним ідентифікатором.

    Args:
        id (int): Ідентифікатор контакту, який потрібно отримати.
        user (User): Об'єкт користувача, якому належить контакт.
        db (AsyncSession): Сесія бази даних для взаємодії з нею.

    Returns:
        Contact: Об'єкт контакту, який належить користувачеві, або None, якщо контакт не знайдено.

    Raises:
        HTTPException(401): Виникає, якщо користувач не має дійсної аутентифікації
                            або доступу до даного контакту.
        HTTPException(404): Виникає, якщо контакт з вказаним ідентифікатором не знайдено.
    """

    stmt = select(Contact).where(Contact.user_id == user.id).filter(Contact.id == id)
    contact_data = await db.execute(stmt)
    contact = contact_data.scalar()
    return contact


# OK
async def repo_get_contacts(db: AsyncSession, user: User, limit: int, offset: int) -> list[Contact]:
    """
        Отримати список контактів користувача.

        Ця функція отримує список контактів з бази даних, які належать користувачеві.

        Args:
            db (AsyncSession): Асинхронна сесія бази даних для взаємодії з нею.
            user (User): Об'єкт користувача, для якого отримуємо контакти.
            limit (int): Максимальна кількість контактів, які будуть отримані.
            offset (int): Кількість контактів, які будуть пропущені з початку результатів.

        Returns:
            List[Contact]: Список об'єктів контактів, які належать користувачеві.

        Raises:
            HTTPException(401): Виникає, якщо користувач не має дійсної аутентифікації
                                або доступу до контактів.
    """

    contacts_data = (select(Contact)
                     .where(Contact.user_id == user.id)
                     .offset(offset)
                     .limit(limit)
                     .order_by(asc(Contact.id))
                     )
    result = await db.execute(contacts_data)
    return result.scalars().all()


# OK
async def repo_get_contact_by_id(id: int, user: User, db: AsyncSession):
    """
        Отримати контакт за ідентифікатором, який належить користувачеві.

        Ця функція використовує як основу функцію get_specific_contact_belongs_to_user(), та доповнює її необхідними
        розширеннями.

        Args:
            id (int): Ідентифікатор контакту, який потрібно отримати.
            user (User): Об'єкт користувача, для якого отримуємо контакт.
            db (AsyncSession): Асинхронна сесія бази даних для взаємодії з нею.

        Returns:
            Contact: Об'єкт контакту, який належить користувачеві.

        Raises:
            HTTPException(401): Виникає, якщо користувач не має дійсної аутентифікації
                                або доступу до контактів.
            HTTPException(404): Виникає, якщо контакт з вказаним ідентифікатором не знайдено.
    """

    contact = await get_specific_contact_belongs_to_user(id, user, db)

    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


# OK
async def repo_create_new_contact(user: User, body: ContactCreate, db: AsyncSession):
    """
        Створити новий контакт для користувача.

        Ця функція створює новий контакт в базі даних для користувача з вказаними даними.

        Args:
            user (User): Об'єкт користувача, для якого створюємо контакт.
            body (ContactCreate): Об'єкт ContactCreate, що містить дані для створення контакту.
            db (AsyncSession): Асинхронна сесія бази даних для взаємодії з нею.

        Returns:
            Contact: Об'єкт контакту, що було створено.

        Raises:
            HTTPException(401): Виникає, якщо користувач не має дійсної аутентифікації
                                або доступу для створення контакту.
            ValueError: Виникає при спробі створення контакту з не валідним форматом дати. Або майбутньою датою народження.
    """

    contact = Contact(**body.dict(), user_id=user.id)
    db.add(contact)
    await db.flush()
    await db.refresh(contact)
    await db.commit()
    return contact


# OK
async def repo_update_contact_db(id: int, user: User, body: ContactUpdate, db: AsyncSession):
    """
        Оновити контакт що існує для користувача.

        Ця функція оновлює контакт що існує в базі даних для користувача з вказаним ідентифікатором.
        У ній використовується функція для знаходження конкретного контакту get_specific_contact_belongs_to_user(),
        з розширеними можливостями для даного випадку - (оновлення інформації про контакт).

        Args:
            id (int): Ідентифікатор контакту, який потрібно оновити.
            user (User): Об'єкт користувача, для якого належить контакт.
            body (ContactUpdate): Об'єкт ContactUpdate, що містить дані для оновлення контакту.
            db (AsyncSession): Асинхронна сесія бази даних для взаємодії з нею.

        Returns:
            Contact: Об'єкт контакту, який було оновлено.

        Raises:
            HTTPException(401): Виникає, якщо користувач не має дійсної аутентифікації
                                або доступу для оновлення контакту.
            HTTPException(404): Виникає, якщо контакт з вказаним ідентифікатором не знайдено.
    """

    contact = await get_specific_contact_belongs_to_user(id, user, db)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")

    for field, value in body.dict(exclude_unset=True).items():
        setattr(contact, field, value)

    await db.commit()
    await db.refresh(contact)
    return contact


# OK
async def repo_delete_contact_db(id: int, user: User, db: AsyncSession):
    """
        Видалити існуючий контакт користувача.

        Ця функція видаляє існуючий контакт з бази даних для користувача з вказаним ідентифікатором.
        У ній використовується допоміжна функція get_specific_contact_belongs_to_user(), з розширеними можливостями
        для даного випадку - (видалення конкретного контакту)

        Args:
            id (int): Ідентифікатор контакту, який потрібно видалити.
            user (User): Об'єкт користувача, для якого належить контакт.
            db (AsyncSession): Асинхронна сесія бази даних для взаємодії з нею.

        Returns:
            dict: Об'єкт з повідомленням про успішне видалення контакту.

        Raises:
            HTTPException(401): Виникає, якщо користувач не має дійсної аутентифікації
                                або доступу для видалення контакту.
            HTTPException(404): Виникає, якщо контакт з вказаним ідентифікатором не знайдено.

        Example response:
            {
                "message": "Contact 'John Doe' successfully deleted"
            }
        """

    contact = await get_specific_contact_belongs_to_user(id, user, db)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")

    contact_name = f"{contact.first_name} {contact.last_name}"

    await db.delete(contact)
    await db.commit()

    return {
        "message": f"Contact '{contact_name}' successfully deleted"}


# OK
async def repo_get_contacts_query(
        user: User,
        query: str,
        limit: int,
        offset: int,
        db: AsyncSession
):
    """
        Отримати список контактів користувача за запитом пошуку.

        Ця функція отримує список контактів з бази даних, які належать користувачеві,
        і відповідають заданому пошуковому запиту.
        Пошук відбувається у полях `first_name`, `last_name`, `email`.

        Args:
            user (User): Об'єкт користувача, для якого отримуємо контакти.
            query (str): Пошуковий запит для фільтрації контактів.
            limit (int): Максимальна кількість контактів, які будуть отримані.
            offset (int): Кількість контактів, які будуть пропущені з початку результатів.
            db (AsyncSession): Асинхронна сесія бази даних для взаємодії з нею.

        Returns:
            List[Contact]: Список об'єктів контактів, які належать користувачеві та відповідають запиту.

        Raises:
            HTTPException(401): Виникає, якщо користувач не має дійсної аутентифікації
                                або доступу до контактів.
    """

    search_query = f"%{query}%"
    lower_search_query = search_query.lower()

    stmt = (
        select(Contact)
        .where(
            (Contact.user_id == user.id) &
            (
                    (func.lower(Contact.first_name).like(lower_search_query)) |
                    (func.lower(Contact.last_name).like(lower_search_query)) |
                    (func.lower(Contact.email).like(lower_search_query))
            )
        )
        .offset(offset)
        .limit(limit)
        .order_by(asc(Contact.id))
    )

    contacts_data = await db.execute(stmt)
    return contacts_data.scalars().all()


# OK

async def repo_get_upcoming_birthday_contacts(user: User, db: AsyncSession):
    """
        Отримати список контактів з наближаючимися днями народження користувача.

        Ця функція повертає список контактів, які мають день народження у найближчі 7 днів.

        Args:
            user (User): Об'єкт користувача, для якого отримуємо контакти з найближчими днями народження.
            db (AsyncSession): Асинхронна сесія бази даних для взаємодії з нею.

        Returns:
            List[Contact]: Список об'єктів контактів, у яких наближаються дні народження.

        Raises:
            HTTPException(401): Виникає, якщо користувач не має дійсної аутентифікації
                                або доступу до контактів.
    """

    today = datetime.datetime.now().date()
    end_date = today + datetime.timedelta(days=7)

    answer_contacts = []
    results = await db.execute(
        select(Contact)
        .filter(Contact.user_id == user.id)
    )
    contacts: list[Contact] = results.scalars().all()

    for contact in contacts:
        b_day = contact.b_day
        today_year_b_day = datetime.datetime(today.year, b_day.month, b_day.day).date()

        if today <= today_year_b_day <= end_date:
            answer_contacts.append(contact)

    return answer_contacts
