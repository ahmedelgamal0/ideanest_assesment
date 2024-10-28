from beanie import Document, Indexed
from passlib.context import CryptContext
from pydantic import EmailStr

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Document):
    """Represents the User Model in the database."""

    name: str
    email: Indexed(EmailStr, unique=True)  # type: ignore
    hashed_password: str
    refresh_token: str | None = None

    def verify_password(self, plain_password: str) -> bool:
        """Verify if the provided plain text password matches the stored hashed password.

        Args:
            plain_password: The plain text password to verify.

        Returns:
            True if the passwords match, False otherwise.
        """  # noqa: E501
        return pwd_context.verify(plain_password, self.hashed_password)

    class Settings:
        name = "users"
