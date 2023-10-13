from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Integer, String,ForeignKey,TIMESTAMP,TEXT
from sqlalchemy.orm import relationship
import uuid
import os
from dotenv import load_dotenv, dotenv_values
load_dotenv()

#//*---Database Connectivity--------*//
# sql_db_url = "postgresql://postgres:4658@localhost:5432/FWP"
sql_db_url = os.environ.get('DATABASE_URL')


engine = create_engine(sql_db_url)
sessionlocal = scoped_session(sessionmaker(bind=engine,autocommit=False,autoflush=False)) 
Base = declarative_base()

def get_db():
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()
        
def generate_uuid():
    return str(uuid.uuid4())

#//*---Model form api log---*//
class task_log(Base):
    __tablename__ = 'task_log'
    id = Column(Integer,primary_key=True,index= True)
    fc_uuid = Column(String)
    user_uuid = Column(String)
    name = Column(String)
    task_id = Column(String)
    created_time = Column(TIMESTAMP)
    updated_time = Column(TIMESTAMP)
    state=Column(String)
    status = Column(String)
    traceback = Column(TEXT)
    webhook_status = Column(String)
    
class create_fwp_log(Base):
    __tablename__ = 'api_log'
    id = Column(Integer,primary_key=True,index= True)
    fc_uuid = Column(String)
    status = Column(String)
    created_time = Column(TIMESTAMP)
    updated_time = Column(TIMESTAMP)
    traceback = Column(TEXT)
