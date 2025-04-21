from database import Base, engine

# Create all tables
Base.metadata.create_all(engine)

print("✅ Tables created!")
