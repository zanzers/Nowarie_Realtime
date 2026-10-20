
print("TEST FILE STARTED", flush=True)

try:
    print("Importing SQLAlchemy...", flush=True)
    from sqlalchemy import text

    print("Importing database engine...", flush=True)
    from app.db.database import engine

    print("Testing PostgreSQL connection...", flush=True)

    with engine.connect() as connection:
        result = connection.execute(text("SELECT version()"))
        print(f"SUCCESS: {result.scalar_one()}", flush=True)

except Exception as error:

    print(f"FAILED: {type(error).__name__}: {error}", flush=True)



print("TEST FILE FINISHED", flush=True)
