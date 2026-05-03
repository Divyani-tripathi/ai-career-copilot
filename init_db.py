# init_db.py
from db import Base, engine
from models import User, Report  # ✅ Fix 1 & 2: correct filename and class names

Base.metadata.create_all(bind=engine)
print("✅ Tables created successfully!")