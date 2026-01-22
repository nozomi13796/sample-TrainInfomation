from datetime import datetime
from .extensions import db

#============================
# Reason(遅延・運休理由マスタ)
#============================
class Reason(db.Model):
    __tablename__ = 'reason'

    rid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), unique=True, nullable=False)

    # relationships
    events = db.relationship('Event', back_populates='reason')

    def __repr__(self):
        return f"<Reason {self.name}>"

#============================
# DelayInfo(遅延・運休個別情報)
#============================
class DelayInfo(db.Model):
    __tablename__ = 'delay_info'

    iid = db.Column(db.Integer, primary_key=True)
    tid = db.Column(db.String(20), db.ForeignKey('train.tid'), nullable=False)
    eid = db.Column(db.Integer, db.ForeignKey('event.eid'), nullable=False)

    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    delay_minutes = db.Column(db.Integer, nullable=False, default=0)

    is_cancel = db.Column(db.Boolean, nullable=False, default=False)
    is_change = db.Column(db.Boolean, nullable=False, default=False)

    # relationships
    event = db.relationship('Event', back_populates='delay_infos')
    train = db.relationship('Train', back_populates='delay_infos')

#============================
# Train(列車マスタ)
#============================
class Train(db.Model):
    __tablename__ = 'train'

    tid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    t_number = db.Column(db.String(20), unique=True, nullable=False)

    # relationships
    delay_infos = db.relationship('DelayInfo', back_populates='train')
    time_tables = db.relationship('TimeTable', back_populates='train')

#============================
# Event(遅延・運休発生イベントマスタ)
#============================
class Event(db.Model):
    __tablename__ = 'event'

    eid = db.Column(db.Integer, primary_key=True)
    rid = db.Column(db.Integer, db.ForeignKey('reason.rid'), nullable=False)
    detail = db.Column(db.String(200), nullable=True)

    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    modified_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    reason = db.relationship('Reason', back_populates='events')
    delay_infos = db.relationship('DelayInfo', back_populates='event')

#============================
# TimeTable(時刻表マスタ)
#============================
class TimeTable(db.Model):
    __tablename__ = 'time_table'

    sid = db.Column(db.Integer, db.ForeignKey('station.sid'), primary_key=True)
    tid = db.Column(db.Integer, db.ForeignKey('train.tid'), primary_key=True)
    arrival_time = db.Column(db.Time, nullable=True)
    departure_time = db.Column(db.Time, nullable=True)

    # relationships
    train = db.relationship('Train', back_populates='time_tables')
    station = db.relationship('Station', back_populates='time_tables')

#============================
# Station(駅マスタ)
#============================
class Station(db.Model):
    __tablename__ = 'station'

    sid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    # relationships
    time_tables = db.relationship('TimeTable', back_populates='station')
