import asyncio
import sys
from sqlalchemy import select
from app.core.database import async_session_maker
from app.core.security import get_password_hash
from app.domains.auth.models import AdminSettings

async def main():
    password = sys.argv[1] if len(sys.argv) > 1 else "admin123"
    async with async_session_maker() as session:
        stmt = select(AdminSettings).limit(1)
        result = await session.execute(stmt)
        admin_record = result.scalar_one_or_none()

        new_hash = get_password_hash(password)
        if admin_record:
            admin_record.password_hash = new_hash
            print(f"Master password updated to: {password}")
        else:
            admin_record = AdminSettings(password_hash=new_hash)
            session.add(admin_record)
            print(f"Master password initialized to: {password}")
        await session.commit()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
