from typing import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.domains.auth.models import AdminSettings

# Import all models so SQLAlchemy metadata knows about all tables
import app.domains.sources.models  # noqa: F401
import app.domains.news.models  # noqa: F401
import app.domains.posts.models  # noqa: F401
import app.domains.keywords.models  # noqa: F401
import app.domains.auth.models  # noqa: F401

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Creates a fresh in-memory SQLite database session for each test function.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Clear data from all tables to ensure test isolation
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
        
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    
    async with session_factory() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())

    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    FastAPI AsyncClient configured with in-memory database session override.
    """
    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
        
    fastapi_app.dependency_overrides.clear()

@pytest.fixture
def auth_headers() -> dict[str, str]:
    """
    Returns valid admin authorization headers for protected endpoints.
    """
    token = create_access_token(subject="admin")
    return {"Authorization": f"Bearer {token}"}

@pytest_asyncio.fixture
async def seeded_admin(db_session: AsyncSession) -> AdminSettings:
    """
    Seeds an admin record with a known master password for login tests.
    """
    admin = AdminSettings(password_hash=get_password_hash("secret123"))
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin
