import datetime

from fastapi import HTTPException
from sqlalchemy import select, asc, func, extract
from sqlalchemy.ext.asyncio import AsyncSession

from src.DB.models import Contact, User
from src.schemas.Contacts_Schemas import ContactCreate, ContactUpdate


async def get_specific_contact_belongs_to_user(id, user, db):
    stmt = select(Contact).where(Contact.user_id == user.id).filter(Contact.id == id)
    contact_data = await db.execute(stmt)
    contact = contact_data.scalar()
    return contact


# OK
async def repo_get_contacts(
        db: AsyncSession,
        user: User,
        limit: int,
        offset: int
):
    contacts_data = select(Contact). \
        where(Contact.user_id == user.id). \
        offset(offset). \
        limit(limit). \
        order_by(asc(Contact.id))
    result = await db.execute(contacts_data)
    return result.scalars().all()


# OK
async def repo_get_contact_by_id(id: int, user: User, db: AsyncSession):
    contact = await get_specific_contact_belongs_to_user(id, user, db)

    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


# OK
async def repo_create_new_contact(user: User, body: ContactCreate, db: AsyncSession):
    contact = Contact(**body.dict(), user_id=user.id)
    db.add(contact)
    await db.flush()
    await db.refresh(contact)
    await db.commit()
    return contact


# OK
async def repo_update_contact_db(id: int, user: User, body: ContactUpdate, db: AsyncSession):
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
    contact = await get_specific_contact_belongs_to_user(id, user, db)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")

    contact_name = f"{contact.first_name} {contact.last_name}"  # Отримуємо ім'я та прізвище контакту

    await db.delete(contact)
    await db.commit()

    return {
        "message": f"Contact '{contact_name}' successfully deleted"}  # Повертаємо повідомлення з ім'ям та прізвищем контакту


# OK
async def repo_get_contacts_query(
        user: User,
        query: str,
        limit: int,
        offset: int,
        db: AsyncSession
):
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
async def repo_get_upcoming_birthday_contacts(user: User, limit: int, db):
    today = datetime.datetime.now().date()
    end_date = today + datetime.timedelta(days=7)

    stmt = (
        select(Contact)
        .where(
            (Contact.user_id == user.id) &
            (
                    (extract('month', Contact.b_day) == today.month) &
                    (extract('day', Contact.b_day).between(today.day, end_date.day))
            )
        )
        .limit(limit)
        .order_by(asc(Contact.id))
    )

    result = await db.execute(stmt)
    return result.scalars().all()
