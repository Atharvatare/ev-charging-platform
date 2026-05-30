import traceback
try:
    from app.core.seed import seed_database
    print("Imported successfully, running seed_database...")
    seed_database()
    print("Seeding successful!")
except Exception as e:
    print(f"FAILED: {e}")
    traceback.print_exc()
