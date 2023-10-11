from fastapi import FastAPI
import uvicorn

from . routers import user
from . import models


models.Base.metadata.create_all(bind=models.engine)

app = FastAPI()
app.include_router(user.router)

# if __name__ == "__main__":
#     uvicorn.run(app,host='127.0.0.1',port=8000)