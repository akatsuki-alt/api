from fastapi import FastAPI, HTTPException

from common.database.objects import *
from common.app import database
from datetime import date

from .query import build_query

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
async def user_stats_all(server: str, id: int, mode: int, relax: int, date: date = date.today()):
    with database.session as session:
        if (stats := session.query(DBStats.date).filter(
            DBStats.user_id == id,
            DBStats.server == server,
            DBStats.mode == mode,
            DBStats.relax == relax,
        ).all()):
            return [date[0].isoformat() for date in stats]
        raise HTTPException(status_code=404, detail="Item not found")

@app.get("/score")
async def score(server: str, id: int):
    with database.session as session:
        if (score := session.get(DBScore, (id, server))):
            return score
        raise HTTPException(status_code=404, detail="Item not found")

@app.get("/score/search")
async def query_scores(query: str, page: int = 1, length: int = 100):
    length = min(1000, length)
    with database.session as session:
        q = build_query(session.query(DBScore), DBScore, query.split(","))
        if (scores := q.offset((page - 1) * length).limit(length).all()):
            return [item for item in scores]
        return []

@app.get("/leaderboard/{type}")
async def leaderboard(type: str, server: str, mode: int, relax: int, query: str = "", page: int = 1, length: int = 100):
    length = min(1000, length)
    with database.session as session:
        q = session.query(DBStatsCompact).filter(
            DBStatsCompact.server == server,
            DBStatsCompact.mode == mode,
            DBStatsCompact.relax == relax,
            DBStatsCompact.leaderboard_type == type,
        ).order_by(DBStatsCompact.global_rank)
        if query:
            q = build_query(q, DBStatsCompact, query.split(","))
        if (leaderboard := q.offset((page - 1) * length).limit(length).all()):
            return [item for item in leaderboard]
        return []
