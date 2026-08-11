from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.admin import Admin


def create_admin():
    db = SessionLocal()

    try:
        email = input("Admin email: ").strip()
        password = input("Admin password: ").strip()

        existing = db.execute(
            select(Admin).where(Admin.email == email)
        ).scalar_one_or_none()

        if existing:
            print("An admin with that email already exists.")
            return

        admin = Admin(
            email=email,
            hashed_password=hash_password(password),
            role="super_admin",
            is_active=True,
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print(f"Admin created successfully: {admin.email}")

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()