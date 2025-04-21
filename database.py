from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os
from dotenv import load_dotenv   
# Load environment variables from .env
load_dotenv()

# Fetch from environment
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"
engine = create_engine(DATABASE_URL)


Base = declarative_base()

class Attendee(Base):
    __tablename__ = 'attendees'
    id       = Column(Integer, primary_key=True)
    badge_id = Column(String, unique=True, nullable=False)
    name     = Column(String, nullable=False)
    email    = Column(String, nullable=False)
    scan1    = Column(DateTime, nullable=True)
    scan2    = Column(DateTime, nullable=True)
    scan3    = Column(DateTime, nullable=True)
    scan4    = Column(DateTime, nullable=True)
    scan5    = Column(DateTime, nullable=True)
    scan6    = Column(DateTime, nullable=True)
    scan7    = Column(DateTime, nullable=True)
    scan8    = Column(DateTime, nullable=True)
    scan9    = Column(DateTime, nullable=True)
    scan10   = Column(DateTime, nullable=True)

class ScanLog(Base):
    __tablename__ = 'scanlog'
    id        = Column(Integer, primary_key=True)
    badge_id  = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

engine  = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)
session = Session()

# Always create tables (picks up new columns on fresh DB)
Base.metadata.create_all(engine)

def register_attendee(badge_id, name, email):
    try:
        attendee = Attendee(badge_id=badge_id, name=name, email=email)
        session.add(attendee)
        session.commit()
    except:
        session.rollback()
        raise

def get_all_attendees():
    return session.query(Attendee).all()

def log_scan(badge_id):
    # 1) record the raw log entry
    session.add(ScanLog(badge_id=badge_id))
    session.commit()

    # 2) fill the next empty scan slot on Attendee
    attendee = session.query(Attendee).filter_by(badge_id=badge_id).first()
    if not attendee:
        return

    now = datetime.datetime.now()
    for i in range(1, 11):
        attr = f"scan{i}"
        if getattr(attendee, attr) is None:
            setattr(attendee, attr, now)
            session.commit()
            break

def get_scan_log():
    return (
        session.query(
            ScanLog.badge_id,
            Attendee.name,
            Attendee.email,
            ScanLog.timestamp
        )
        .join(Attendee, Attendee.badge_id == ScanLog.badge_id)
        .order_by(ScanLog.timestamp.desc())
        .all()
    )
