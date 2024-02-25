from fastapi import FastAPI, HTTPException

from common.database.objects import *
from common.app import database
from datetime import date

app = FastAPI()

@app.get("/user")
async def user(server: str, id: int):
    with database.session as session:
        if (user := session.get(DBUser, (id, server))):
            return user
        raise HTTPException(status_code=404, detail="Item not found")

@app.get("/beatmap")
async def beatmap(id: int):
    with database.session as session:
        if (beatmap := session.get(DBBeatmap, id)):
            session.expunge(beatmap.beatmapset)
            return beatmap
        raise HTTPException(status_code=404, detail="Item not found")

@app.get("/beatmapset")
async def beatmapset(id: int):
    with database.session as session:
        if (beatmapset := session.get(DBBeatmapset, id)):
            for beatmap in beatmapset.beatmaps:
                session.expunge(beatmap)
            return beatmapset
        raise HTTPException(status_code=404, detail="Item not found")

@app.get("/user/stats")
async def user_stats(server: str, id: int, mode: int, relax: int, date: date = date.today()):
    with database.session as session:
        if (stats := session.query(DBStats).filter(
            DBStats.user_id == id,
            DBStats.server == server,
            DBStats.mode == mode,
            DBStats.relax == relax,
            DBStats.date == date
        ).first()):
            return stats
        raise HTTPException(status_code=404, detail="Item not found")

@app.get("/user/stats/all")
async def user_stats(server: str, id: int, mode: int, relax: int, date: date = date.today()):
    with database.session as session:
        if (stats := session.query(DBStats.date).filter(
            DBStats.user_id == id,
            DBStats.server == server,
            DBStats.mode == mode,
            DBStats.relax == relax,
        ).all()):
            return [date[0].isoformat() for date in stats]
        raise HTTPException(status_code=404, detail="Item not found")
