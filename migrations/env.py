from logging.config import fileConfig
from pathlib import Path
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

# ------------------------------------------------------------------
# Add /src to the Python path
# ------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"

sys.path.insert(0, str(SRC_DIR))

# ------------------------------------------------------------------
# Import application
# ------------------------------------------------------------------

from app.core.config import settings
from app.db.base import Base

# IMPORTANT:
# Import every SQLAlchemy model so Alembic can detect them.

from app.models.admin import Admin
from app.models.admin_otp import AdminOTP
from app.models.admin_password_reset import AdminPasswordReset
from app.models.event import Event
from app.models.registration import Registration

# ------------------------------------------------------------------
# Alembic configuration
# ------------------------------------------------------------------

config = context.config

print("=== ALEMBIC DEBUG ===")
print("DATABASE URL:", settings.DATABASE_URL)
print("TARGET METADATA TABLES:", list(Base.metadata.tables.keys()))
print("======================")

# Configure logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata for autogenerate
target_metadata = Base.metadata


# ------------------------------------------------------------------
# Offline migrations
# ------------------------------------------------------------------

def run_migrations_offline() -> None:
    """Run migrations in offline mode."""

    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ------------------------------------------------------------------
# Online migrations
# ------------------------------------------------------------------

def run_migrations_online() -> None:
    """Run migrations in online mode."""

    connectable = engine_from_config(
        {
            "sqlalchemy.url": settings.DATABASE_URL,
        },
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# ------------------------------------------------------------------
# Run migrations
# ------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()