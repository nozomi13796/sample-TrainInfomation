from flask import Blueprint, flash, jsonify, render_template, request, redirect, url_for
from ..extensions import db
from ..models import *
from datetime import date, timedelta, datetime
from ..forms.delay import *
from collections import defaultdict

delay_bp = Blueprint('delay', __name__, url_prefix='/delay')

def get_event_latest_date():
    latest_event_date = db.session.query(db.func.max(Event.date)).scalar()
    return latest_event_date

@delay_bp.route('/')
def list_event():
    events = db.session.query(Event).all()
    event_list = []

    for e in events:
        delays = []
        cancels = []
        changes = []
        for d in e.delay_infos:
            if d.is_cancel == True:
                cancels.append(d)
            elif d.is_change == True:
                changes.append(d)
            else:
                delays.append(d)

        event_list.append({
            'event': e,
            'delays': delays,
            'cancels': cancels,
            'changes': changes
        })

    return render_template('delay/list_event.html', event_list=event_list)


@delay_bp.route('/new_event', methods=['GET', 'POST'])
def new_event():
    form = EventForm()

    # 理由の選択肢をセット
    reasons = Reason.query.all()
    form.rid.choices = [(r.rid, r.name) for r in reasons]

    # 今日のイベント一覧
    today_events = Event.query.filter_by(date=date.today()).all()
    event_counts = {e.eid: len(e.delay_infos) for e in today_events}

    if form.validate_on_submit():
        event = Event(
            rid=form.rid.data,
            detail=form.detail.data,
            date=date.today()
        )
        db.session.add(event)
        db.session.commit()
        return redirect(url_for('delay.new_event'))

    return render_template(
        'delay/new_event.html',
        form=form,
        today_events=today_events,
        event_counts=event_counts,
        today = date.today()
    )

@delay_bp.route('/new_delay_info/<int:eid>',methods=['GET', 'POST'])
def new_delay_info(eid):
    event = Event.query.get_or_404(eid)
    alpha_choices = [("E", "E"), ("M", "M")]

    form = DelayInfoForm()
    form.alpha.choices = alpha_choices

    # POST
    if form.validate_on_submit():
        # 列車IDの構築
        t_number = f"{form.t_number.data}{form.alpha.data}"
        selected_train = Train.query.filter_by(t_number=t_number).first()
        if selected_train:
            new_info = DelayInfo(
                tid=selected_train.tid,
                eid=event.eid,
                delay_minutes=form.delay_minutes.data,
                is_cancel=bool(form.is_cancel.data),
                is_change=bool(form.is_change.data),
            )
            db.session.add(new_info)
            db.session.commit()
            return redirect(url_for('delay.list_event'))
        # train not found
        else:
            flash('指定された列車がかりません。番号を確認してください。', 'error')
            return redirect(url_for('delay.new_delay_info', eid=eid))
    # GET
    return render_template('delay/new_delay_info.html', event=event, form=form)

# 掲示板表示駅および日付の選択画面
@delay_bp.route("/board/select")
def board_select():
    stations = Station.query.order_by(Station.sid).all()
    today_str = date.today().strftime("%Y-%m-%d")
    return render_template("delay/select_board.html", stations=stations, today=today_str)

# 駅掲示板表示
@delay_bp.route("/board")
def station_board():
    # 駅IDと日付の取得
    sid = request.args.get("sid" , type=int)
    date_str = request.args.get("date")

    if not sid or not date_str:
        return redirect(url_for("delay.board_select"))

    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    station = Station.query.get_or_404(sid)

    # 現在時刻
    now_dt = datetime.now()

    # Timetable JOIN → DelayInfo JOIN
    rows = (
        db.session.query(DelayInfo, Train, TimeTable, Event)
        .join(Train, DelayInfo.tid == Train.tid)
        .join(TimeTable, Train.tid == TimeTable.tid)
        .join(Event, DelayInfo.eid == Event.eid)
        .filter(TimeTable.sid == sid)
        .filter(Event.date == target_date)
        .all()
    )

    processed = []

    for d, train, tt, event in rows:
        dep_time = tt.departure_time
        if isinstance(dep_time, datetime):
            dep_time = dep_time.time()
        elif isinstance(dep_time, str):
            dep_time = datetime.strptime(dep_time, "%H:%M:%S").time()
        base_dt = datetime.combine(target_date, dep_time)
        predicted_dt = base_dt + timedelta(minutes=d.delay_minutes)

        # 遅延列車の出発済みは除外
        if not d.is_cancel and not d.is_change and (predicted_dt <= now_dt):
            continue

        processed.append({
            "delay": d,
            "train": train,
            "tt": tt,
            "predicted_time": predicted_dt.time()
        })

    # カテゴリ分類
    cancel_list = []
    change_list = []
    delay_list = []

    for p in processed:
        d = p["delay"]
        if d.is_cancel:
            cancel_list.append(p)
        elif d.is_change:
            change_list.append(p)
        elif d.delay_minutes > 0:
            delay_list.append(p)

    # イベント別グループ化
    def group_by_event(items):
        grouped = defaultdict(list)
        for p in items:
            event_name = p["delay"].event.detail
            grouped[event_name].append(p)
        return grouped

    cancel_grouped = group_by_event(cancel_list)
    change_grouped = group_by_event(change_list)
    delay_grouped = group_by_event(delay_list)

    # 初回表示（SSR）
    return render_template(
        "delay/board.html",
        station=station,
        cancel_grouped=cancel_grouped,
        change_grouped=change_grouped,
        delay_grouped=delay_grouped
    )

# 駅掲示板API
@delay_bp.route("/api/board")
def api_board():
    sid = request.args.get("sid", type=int)
    date_str = request.args.get("date")

    if not sid or not date_str:
        return jsonify({"error": "sid and date are required"}), 400

    target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    now_dt = datetime.now()

    station = Station.query.get_or_404(sid)

    rows = (
        db.session.query(DelayInfo, Train, TimeTable, Event)
            .join(Train, DelayInfo.tid == Train.tid)
            .join(TimeTable, Train.tid == TimeTable.tid)
            .join(Event, DelayInfo.eid == Event.eid)
            .filter(TimeTable.sid == sid)
            .filter(Event.date == target_date)
            .all()
    )

    processed = []

    for d, train, tt, event in rows:
        dep_time = tt.departure_time
        base_dt = datetime.combine(target_date, dep_time)
        predicted_dt = base_dt + timedelta(minutes=d.delay_minutes)
        is_cancel = d.is_cancel in (True, 1, "1")
        is_change = d.is_change in (True, 1, "1")


        if not is_cancel and not is_change and predicted_dt <= now_dt:
            continue

        processed.append({
            "event": event.detail,
            "train_name": train.name,
            "train_number": train.t_number,
            "departure_time": tt.departure_time.strftime("%H:%M"),
            "predicted_time": predicted_dt.time().strftime("%H:%M"),
            "delay_minutes": d.delay_minutes,
            "is_cancel": d.is_cancel,
            "is_change": d.is_change
        })

    def group(items):
        grouped = defaultdict(list)
        for p in items:
            grouped[p["event"]].append(p)
        return grouped

    cancel = group([p for p in processed if p["is_cancel"]])
    change = group([p for p in processed if p["is_change"]])
    delay = group([
        p for p in processed
        if not p["is_cancel"] and not p["is_change"] and p["delay_minutes"] > 0
    ])


    return jsonify({
        "station": station.name,
        "date": target_date.strftime("%Y-%m-%d"),
        "cancel": cancel,
        "change": change,
        "delay": delay
    })

# delay_info一覧表示
@delay_bp.route('/list_info')
def list_info():
    delay_infos = DelayInfo.query.order_by(DelayInfo.modified_at.desc()).all()

    items = []
    for d in delay_infos:
        title = "運休" if d.is_cancel else "経路変更" if d.is_change else "遅延"

        items.append({
            "id": d.iid,
            "train": d.train.name,
            "t_number": d.train.t_number,
            "event": d.event.detail,
            "delay_minutes": d.delay_minutes,
            "modified_at": d.modified_at,
            "title": title
        })
    return render_template('delay/list_info.html', items=items)

# delay_info削除
@delay_bp.route('/delete_info/<int:iid>', methods=['POST'])
def delete_info(iid):
    delay_info = DelayInfo.query.get_or_404(iid)
    db.session.delete(delay_info)
    db.session.commit()
    return redirect(url_for('delay.list_info'))
