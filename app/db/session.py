from sqlmodel import create_engine, Session, SQLModel
from app.core.config import settings

# The engine is the central connection point to your SQLite database
# 'check_same_thread=False' is required for SQLite to work with FastAPI's async nature
engine = create_engine(
    settings.DATABASE_URL, 
    echo=settings.DEBUG, 
    connect_args={"check_same_thread": False}
)

def init_db():
    """
    Creates the database file and all tables defined in your schemas.
    This is called when the application starts up.
    """
    # Import schemas here to ensure they are registered before creating tables.
    # We use a dummy reference to 'schemas' to satisfy Pylance/Ruff 'unused' warnings.
    from app.models import schemas 
    _ = schemas  # This line tells the linter the import is intentional
    
    SQLModel.metadata.create_all(engine)

def get_session():
    """
    A 'dependency' function for FastAPI.
    It opens a new database session for a request and ensures it is closed
    after the request is finished.
    """
    with Session(engine) as session:
        yield session