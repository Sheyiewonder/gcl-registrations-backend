from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)

tables = [
    "admins",
    "admin_otps",
    "admin_invitations",
    "admin_password_resets",
    "events",
    "registrations",
]

with engine.connect() as connection:
    print("DATABASE:")
    print(connection.execute(text("SELECT current_database()")).fetchone())

    print("\nTABLE COUNTS:")

    for table in tables:
        result = connection.execute(
            text(f'SELECT COUNT(*) FROM "{table}"')
        ).scalar()

        print(f"{table}: {result}")