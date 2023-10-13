from pydantic import BaseModel, Field
from typing import List,Optional
from uuid import UUID
import uuid as uuid_pkg
import sqlalchemy
import datetime

class user_api(BaseModel):
    fc_uuid:str
    
    class Config():
        orm_mode = True  
        
    