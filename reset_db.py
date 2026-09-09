from models import engine, Base

print("🚨 WARNING: Dropping old tables...")
Base.metadata.drop_all(bind=engine)

print("🏗️ Creating new multi-tenant tables...")
Base.metadata.create_all(bind=engine)

print("✅ Database successfully reset and upgraded!")
