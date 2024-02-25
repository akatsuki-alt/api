from fastapi import FastAPI, HTTPException

from common.database.objects import *
from common.app import database

app = FastAPI()

@app.get("/user")
async def user(server: str, user_id: int):
    with database.session as session:
        if (user := session.get(DBUser, (user_id, server))):
            return user
        raise HTTPException(status_code=404, detail="Item not found")

