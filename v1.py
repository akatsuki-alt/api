from fastapi import HTTPException

from common.database.objects import *
from common.app import database
from datetime import date
from sqlalchemy import asc, desc
from .query import build_query
from . import app

def _sort(column_name, _desc):
    if _desc:
        return desc(column_name)
    return asc(column_name)

@app.get("/")
async def root():
    return "Akatsuki Alt V4 API"

@app.get("/api/v1/beatmap")
async def beatmap(id: int):
    with database.managed_session() as session:
        if (beatmap := session.get(DBBeatmap, id)):
            session.expunge(beatmap.beatmapset)
            return beatmap
        raise HTTPException(status_code=404, detail="Item not found")

@app.get("/api/v1/beatmapset")
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

@app.get("/api/v1/user")
async def user(server: str, id: int):
    with database.managed_session() as session:
        if (user := session.get(DBUser, (id, server))):
            return user
        raise HTTPException(status_code=404, detail="Item not found")

@app.get("/api/v1/user/list")
async def user_list(server: str, page: int = 1, length: int = 100, query: str = "", sort: str = "", desc: bool = True):
    length = min(100, length)
    with database.managed_session() as session:
        q = session.query(DBUser).filter(DBUser.server == server)
        if query:
            q = build_query(q, DBUser, query.split(","))
        if sort:
            q = q.order_by(_sort(sort, desc))
        users = q.offset((page - 1) * length).limit(length)
        return {'count': q.count(), 'users': users.all()}

@app.get("/api/v1/user/first_places")
async def user_first_places(server: str, id: int, mode: int, relax: int, page: int = 1, length: int = 100, query: str = "", date: date = None):
    with database.managed_session() as session:
        q = session.query(DBFirstPlace).filter(
            DBFirstPlace.server == server, 
            DBFirstPlace.user_id == id,
            DBFirstPlace.mode == mode, 
            DBFirstPlace.relax == relax
        )
        if date:
            q = q.filter(DBFirstPlace.date == date)
        else:
            if (last_known := q.order_by(DBFirstPlace.date.desc()).first()):
                date = last_known.date
            else:
                return {'date': None, 'count': 0, 'scores': []}
        if query:
            q = q.join(DBScore)
            q = build_query(q, DBScore, query.split(","))
        length = min(100, length)
        q = q.offset((page - 1) * length).limit(length)
        return {'date': date, 'count': q.count(), 'scores': [first_place.score for first_place in q.all()]}        

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
async def user_stats_all(server: str, id: int, mode: int, relax: int):
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
async def query_scores(query: str, page: int = 1, length: int = 100, sort: str = "", desc: bool = True):
    length = min(1000, length)
    with database.managed_session() as session:
        q = build_query(session.query(DBScore), DBScore, query.split(","))
        scores = q.offset((page - 1) * length).limit(length)
        if sort:
            q = q.order_by(_sort(sort, desc))
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
