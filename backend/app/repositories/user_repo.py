"""Data access for users. The only place that knows how users are stored."""

from sqlalchemy.orm import Session

from app.models.user import User, UserStatus


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_provider_id(self, provider: str, provider_user_id: str) -> User | None:
        return (
            self.db.query(User)
            .filter(User.provider == provider, User.provider_user_id == provider_user_id)
            .first()
        )

    def list(self, status: UserStatus | None = None) -> list[User]:
        query = self.db.query(User)
        if status is not None:
            query = query.filter(User.status == status)
        return query.order_by(User.created_at.desc()).all()

    def update_status(self, user_id: int, status: UserStatus) -> User | None:
        user = self.db.get(User, user_id)
        if user is None:
            return None
        user.status = status
        self.db.commit()
        self.db.refresh(user)
        return user

    def upsert_from_oauth(
        self,
        email: str,
        name: str,
        picture: str | None,
        provider: str,
        provider_user_id: str,
    ) -> User:
        user = self.get_by_provider_id(provider, provider_user_id)
        if user is None:
            user = self.get_by_email(email)

        if user is None:
            user = User(
                email=email,
                name=name,
                picture=picture,
                provider=provider,
                provider_user_id=provider_user_id,
            )
            self.db.add(user)
        else:
            user.email = email
            user.name = name
            user.picture = picture
            user.provider = provider
            user.provider_user_id = provider_user_id

        self.db.commit()
        self.db.refresh(user)
        return user
