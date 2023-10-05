from pydantic import BaseModel, Field
from typing import List,Optional
from uuid import UUID
import uuid as uuid_pkg
import sqlalchemy
import datetime

class webhook_check(BaseModel):
    name:str
    number: str
    
    class Config():
        orm_mode = True  