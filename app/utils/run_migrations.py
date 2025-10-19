import asyncio
import sqlite3
from pathlib import Path


async def run_migrations():
    db_path = Path("schedulee.db")

    if not db_path.exists():
        print("Database not found, creating new...")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Читаем и выполняем миграцию
        migration_file = Path("migrations/001_add_new_fields.sql")
        if migration_file.exists():
            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_sql = f.read()

            cursor.executescript(migration_sql)
            conn.commit()
            print("Migration completed successfully!")
        else:
            print("Migration file not found!")

    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(run_migrations())