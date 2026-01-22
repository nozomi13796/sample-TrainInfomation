import csv
from datetime import datetime, date, timedelta
from app import create_app
from app.extensions import db
from app.models import Reason, Event, Train, DelayInfo, Station, TimeTable

def jst_now():
    return datetime.utcnow() + timedelta(hours=9)

def load_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.reader(f))

def seed_reason():
    rows = load_csv("seed/reason.csv")
    for rid, name in rows:
        db.session.add(Reason(rid=int(rid), name=name))

def seed_event():
    rows = load_csv("seed/event.csv")
    for eid, rid, detail, _, _ in rows:
        db.session.add(Event(
            eid=int(eid),
            rid=int(rid),
            detail=detail,
            date=date.today(),  # ← CSV の値を無視して今日にする
            modified_at=jst_now()  # ← 現在時刻にする
        ))


def seed_station():
    rows = load_csv("seed/station.csv")
    for sid, name in rows:
        db.session.add(Station(sid=int(sid), name=name))

def seed_train():
    rows = load_csv("seed/train.csv")
    for tid, name, t_number in rows:
        db.session.add(Train(
            tid=int(tid),
            name=name,
            t_number=t_number
        ))

def seed_time_table():
    rows = load_csv("seed/time_table.csv")
    for sid, tid, arr, dep in rows:
        db.session.add(TimeTable(
            sid=int(sid),
            tid=int(tid),
            arrival_time=datetime.strptime(arr, "%H:%M:%S.%f").time(),
            departure_time=datetime.strptime(dep, "%H:%M:%S.%f").time()
        ))

def seed_delay_info():
    rows = load_csv("seed/delay_info.csv")
    for iid, tid, eid, _, delay, is_cancel, is_change in rows:
        db.session.add(DelayInfo(
            iid=int(iid),
            tid=int(tid),
            eid=int(eid),
            modified_at=jst_now(),  # ← 現在時刻にする
            delay_minutes=int(delay),
            is_cancel=bool(int(is_cancel)),
            is_change=bool(int(is_change))
        ))


def run_seed():
    seed_reason()
    seed_event()
    seed_station()
    seed_train()
    seed_time_table()
    seed_delay_info()

    db.session.commit()
    print("Seed completed!")
