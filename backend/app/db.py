from sqlalchemy import create_engine, text 
from sqlalchemy.orm import declarative_base, sessionmaker
from pathlib import Path 
import os

# DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

BASE_DIR = Path(__file__).resolve().parent
# DATABASE_URL = f"sqlite:///{BASE_DIR / 'app.db'}"  # anchored path
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'app.db'}")  # anchored path


engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})

## just creating a textual object
# with engine.connect() as connection:
    # res = connection.execute(text("select 'hello world'"))
    # print(res.fetchall())


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

## commiting is only possible when we do connection.commit()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# @property
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()