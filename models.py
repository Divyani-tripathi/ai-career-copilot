from sqlalchemy import Column, Integer, String, Text, ForeignKey
from db import Base

class User(Base):              # ✅ Fix 1: user → User
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True)
    password = Column(String(100))

class Report(Base):            # ✅ Fix 2: Reports → Report
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    resume_text = Column(Text)
    results = Column(Text)     # ✅ Fix 3: result → results

