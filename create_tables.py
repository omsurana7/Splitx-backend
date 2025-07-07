from app.utils.db import Base, engine
from app.models.transaction import Transaction

# 🔄 Trigger the table creation
Base.metadata.create_all(bind=engine)

print("✅ Transaction table created successfully!")
