import os
from sqlalchemy import create_engine, MetaData
from databases import Database
import pathlib

# Default database path will be /app/data/database.db inside the container
DEFAULT_DB_PATH = "./data/database.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{DEFAULT_DB_PATH}")

database = Database(DATABASE_URL)
metadata = MetaData()

# For SQLite, the engine URL needs to be slightly different if it's a relative path
# The 'databases' library handles this well, but for create_engine, ensure the path is absolute or correctly relative.
# If DATABASE_URL is the default, we construct the engine URL carefully.
is_sqlite_default = DATABASE_URL.startswith("sqlite+aiosqlite:///") and DEFAULT_DB_PATH in DATABASE_URL

if is_sqlite_default:
    # Ensure the path for create_engine is just 'sqlite:///./data/database.db'
    # or an absolute path if needed by SQLAlchemy for some drivers.
    # For aiosqlite, 'sqlite:///./data/database.db' (relative to CWD) is fine.
    # The CWD for the app when run in Docker is /app.
    engine_url = f"sqlite:///{DEFAULT_DB_PATH}"
else:
    engine_url = DATABASE_URL # For other DBs or if DATABASE_URL is fully specified

engine = create_engine(engine_url)


def create_db_and_tables():
    # Ensure the data directory exists for SQLite
    if is_sqlite_default:
        db_file_path = pathlib.Path(DEFAULT_DB_PATH)
        db_dir = db_file_path.parent
        os.makedirs(db_dir, exist_ok=True)
        print(f"Ensuring database directory exists at: {db_dir.resolve()}")

    # This is synchronous, so it's run once at startup
    # For SQLite, tables are created if they don't exist
    # For other DBs, you might need Alembic for migrations
    print(f"Creating database tables with engine: {engine_url}")
    metadata.create_all(bind=engine)
