from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.DB.models import User
from src.schemas.User_Schemas import UserCreate
from src.services import authservice as auth_service


async def repo_create_user(body: UserCreate, db: AsyncSession):
    """
    Створити нового користувача.

    Ця функція створює нового користувача з наданими даними та зберігає його в базі даних.
    Для присвоєння аватара використовується libgravatar, який автоматично присвоює аватар користувачу,
    відповідно до користувацього імейлу.

    Args:
        body (UserCreate): Об'єкт `UserCreate`, що містить дані для створення нового користувача.
        db (AsyncSession): Асинхронна сесія бази даних для взаємодії з нею.

    Returns:
        User: Об'єкт створеного користувача з бази даних.

    Raises:
        HTTPException(409): Виникає, якщо користувач з вказаною електронною адресою вже існує.
    """
    g = Gravatar(email=body.email)
    avatar_img_url = g.get_image()
    refresh_token = await auth_service.authservice.create_refresh_token({"sub": body.email})
    user = User(**body.dict(),
                created_at=datetime.utcnow(),
                avatar=avatar_img_url,
                refresh_token=refresh_token)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def repo_user_authentication_by_email(email: str, db: AsyncSession) -> User:
    """
    Здійснює аутентифікацію користувача за електронною поштою.

    Ця функція шукає користувача в базі даних за його електронною поштою
    та повертає об'єкт користувача, якщо такий користувач існує.

    Args:
        email (str): Електронна пошта користувача, якого потрібно знайти.
        db (AsyncSession): Асинхронна сесія бази даних для взаємодії з нею.

    Returns:
        User: Об'єкт користувача, якщо користувач з вказаною електронною адресою існує.
              Якщо користувача з такою електронною поштою не знайдено, повертається None.
    """
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    existing_user = result.scalar()
    return existing_user


async def repo_update_refresh_token(user: User, new_refresh_token: str, db: AsyncSession):
    """
    Оновлює токен оновлення (refresh token) для користувача.

    Ця функція оновлює токен оновлення (refresh token) для вказаного користувача в базі даних.
    Вона зберігає новий токен оновлення і зберігає зміни в базі даних.

    Args:
        user (User): Об'єкт користувача, для якого потрібно оновити токен оновлення.
        new_refresh_token (str): Новий токен оновлення, який потрібно зберегти.
        db (AsyncSession): Асинхронна сесія бази даних для взаємодії з нею.

    Returns:
        None
    """
    user.refresh_token = new_refresh_token
    await db.commit()


async def confirmed_email(email: str, db: AsyncSession):
    """
    Підтверджує електронну пошту користувача.

    Ця функція підтверджує електронну пошту користувача, оновлюючи статус активації.
    Вона встановлює значення поля `is_activated` користувача на True, вказуючи, що
    електронна пошта була успішно підтверджена.

    Args:
        email (str): Електронна пошта користувача, яку потрібно підтвердити.
        db (AsyncSession): Асинхронна сесія бази даних для взаємодії з нею.

    Returns:
        None
    """

    user = await repo_user_authentication_by_email(email=email, db=db)
    user.is_activated = True
    await db.commit()


async def update_avatar(email, src_url, db: AsyncSession):
    """
    Оновлює аватар користувача.

    Ця функція оновлює аватар (URL зображення) користувача в базі даних за вказаною електронною поштою.
    Вона знаходить користувача за його електронною поштою, оновлює поле `avatar` на новий URL аватару
    та зберігає зміни в базі даних.

    Args:
        email (str): Електронна пошта користувача, чий аватар потрібно оновити.
        src_url (str): URL нового аватару, який потрібно зберегти.
        db (AsyncSession): Асинхронна сесія бази даних для взаємодії з нею.

    Returns:
        User: Об'єкт користувача з оновленим аватаром.
    """

    user = await repo_user_authentication_by_email(email=email, db=db)
    user.avatar = src_url
    await db.commit()
    return user


async def add_reset_token_to_db(user, reset_token, db: AsyncSession):
    """
    Додає токен скидання пароля (reset token) до користувача.

    Ця функція додає токен скидання пароля (reset token) до вказаного користувача в базі даних.
    Вона зберігає новий токен скидання пароля у полі `reset_token` користувача та зберігає зміни в базі даних.

    Args:
        user: Об'єкт користувача, для якого потрібно додати токен скидання пароля.
        reset_token (str): Токен скидання пароля, який потрібно зберегти.
        db (AsyncSession): Асинхронна сесія бази даних для взаємодії з нею.

    Returns:
        None
    """

    user.reset_token = reset_token
    await db.commit()
