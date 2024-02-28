from fastapi import HTTPException

from common.database.objects import *
from common.app import database
from datetime import date

from .query import build_query
from . import app

@app.get("/")
async def root():
    return "Akatsuki Alt V4 API"

@app.get("/api/v1/user")
async def user(server: str, id: int):
    with database.managed_session() as session:
        if (user := session.get(DBUser, (id, server))):
            return user
        raise HTTPException(status_code=404, detail="Item not found")

@app.get("/api/v1/beatmap/{id}")
async def beatmap(id: int):
    with database.managed_session() as session:
        if (beatmap := session.get(DBBeatmap, id)):
            session.expunge(beatmap.beatmapset)
            return beatmap
        raise HTTPException(status_code=404, detail="Item not found")

@app.get("/api/v1/beatmapset/{id}")
async def beatmapset(id: int):
    with database.managed_session() as session:
        if (beatmapset := session.get(DBBeatmapset, id)):
            for beatmap in beatmapset.beatmaps:
                session.expunge(beatmap)
            return beatmapset
        raise HTTPException(status_code=404, detail="Item not found")

@app.get("/api/v1/beatmap/pack/{tag}")
async def beatmap_pack(tag: str):
    with database.managed_session() as session:
        if (pack := session.get(DBBeatmapPack, tag)):
            return pack
        raise HTTPException(status_code=404, detail="Item not found")

@app.get("/api/v1/beatmap/pack/{tag}/completion")
async def user_beatmap_pack_completion(tag: str, server: str, user_id: int, mode: int, relax: int):
    with database.managed_session() as session:
        sets = session.query(DBBeatmapset).filter(DBBeatmapset.pack_tags.any(tag)).all()
        result = {
            'completed': list(),
            'uncompleted': list()
        }
        for set in sets:
            for beatmap in set.beatmaps:
                if session.query(DBScore).filter(DBScore.server == server, DBScore.user_id == user_id, DBScore.mode == mode, DBScore.relax == relax, DBScore.beatmap_id == beatmap.id, DBScore.completed == 3).count():
                    result['completed'].append(beatmap.id)
                else:
                    result['uncompleted'].append(beatmap.id)
        return result

@app.get("/api/v1/user/stats")
async def user_stats(server: str, id: int, mode: int, relax: int, date: date = date.today()):
    with database.managed_session() as session:
        if (stats := session.query(DBStats).filter(
            DBStats.user_id == id,
            DBStats.server == server,
            DBStats.mode == mode,
            DBStats.relax == relax,
            DBStats.date == date
        ).first()):
            return stats
        raise HTTPException(status_code=404, detail="Item not found")

@app.get("/api/v1/user/stats/all")
async def user_stats_all(server: str, id: int, mode: int, relax: int, date: date = date.today()):
    with database.managed_session() as session:
        stats = session.query(DBStats.date).filter(
            DBStats.user_id == id,
            DBStats.server == server,
            DBStats.mode == mode,
            DBStats.relax == relax,
        )
        return {'total': stats.count(), 'stats': [date[0].isoformat() for date in stats]}

@app.get("/api/v1/score")
async def score(server: str, id: int):
    with database.managed_session() as session:
        if (score := session.get(DBScore, (id, server))):
            return score
        raise HTTPException(status_code=404, detail="Item not found")

@app.get("/api/v1/score/search")
async def query_scores(query: str, page: int = 1, length: int = 100):
    length = min(1000, length)
    with database.managed_session() as session:
        q = build_query(session.query(DBScore), DBScore, query.split(","))
        scores = q.offset((page - 1) * length).limit(length)
        return {'count': q.count(), 'scores': scores.all()}

@app.get("/api/v1/leaderboard/{type}")
async def leaderboard(type: str, server: str, mode: int, relax: int, query: str = "", page: int = 1, length: int = 100):
    length = min(1000, length)
    with database.managed_session() as session:
        q = session.query(DBStatsCompact).filter(
            DBStatsCompact.server == server,
            DBStatsCompact.mode == mode,
            DBStatsCompact.relax == relax,
            DBStatsCompact.leaderboard_type == type,
        ).order_by(DBStatsCompact.global_rank)
        if query:
            q = build_query(q, DBStatsCompact, query.split(","))
        return {'count': q.count(), 'stats': q.offset((page - 1) * length).limit(length).all()}
