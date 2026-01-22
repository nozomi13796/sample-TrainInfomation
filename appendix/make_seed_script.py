from datetime import time, date, timedelta
from ..app import create_app
from ..app.extensions import db
from ..app.models import Reason, Train, Station, TimeTable, Event, DelayInfo

app = create_app()


def add_minutes_to_time(t: time, minutes: int) -> time:
    base = timedelta(hours=t.hour, minutes=t.minute)
    base += timedelta(minutes=minutes)
    total_minutes = base.seconds // 60
    h = total_minutes // 60
    m = total_minutes % 60
    return time(h, m)


with app.app_context():
    # 既存データ削除（外部キー制約の順番に注意）
    DelayInfo.query.delete()
    Event.query.delete()
    TimeTable.query.delete()
    Train.query.delete()
    Station.query.delete()
    Reason.query.delete()

    #============================
    # Reason（遅延理由）
    #============================
    reasons = [
        Reason(name="天候不良"),
        Reason(name="大雪"),
        Reason(name="設備故障"),
        Reason(name="安全確認"),
        Reason(name="動物支障"),
    ]
    db.session.add_all(reasons)

    #============================
    # Station（駅マスタ）
    # 敦賀 → 越前たけふ → 福井 → 芦原温泉 → 金沢
    #============================
    stations = [
        Station(name="敦賀"),
        Station(name="越前たけふ"),
        Station(name="福井"),
        Station(name="芦原温泉"),
        Station(name="金沢"),
    ]
    db.session.add_all(stations)

    #============================
    # Train（列車マスタ）
    # かがやき3本 / はくたか5本 / つるぎ10本 / サンダーバード8本
    #============================
    trains = []

    # かがやき：500, 502, 504
    kagayaki_nums = [500, 502, 504]
    for num in kagayaki_nums:
        trains.append(Train(name=f"かがやき{num}", t_number=f"{num}E"))

    # はくたか：560〜568（偶数）
    hakutaka_nums = [560, 562, 564, 566, 568]
    for num in hakutaka_nums:
        trains.append(Train(name=f"はくたか{num}", t_number=f"{num}E"))

    # つるぎ：62, 64, 2〜10（偶数）→ 合計10本
    tsurugi_nums = [62, 64, 2, 4, 6, 8, 10, 12, 14, 16]
    for num in tsurugi_nums:
        trains.append(Train(name=f"つるぎ{num}", t_number=f"{num}E"))

    # サンダーバード：4002M〜4016M（偶数）
    thunder_nums = [4002, 4004, 4006, 4008, 4010, 4012, 4014, 4016]
    for num in thunder_nums:
        trains.append(Train(name=f"サンダーバード{num}", t_number=f"{num}M"))

    db.session.add_all(trains)
    db.session.flush()  # tid, sid を取得

    #============================
    # TimeTable（時刻表）
    # 敦賀 → 越前たけふ → 福井 → 芦原温泉 → 金沢
    # 駅間所要時間（分）：13 / 14 / 10 / 22
    #============================
    station_order = stations  # [敦賀, 越前たけふ, 福井, 芦原温泉, 金沢]
    travel_minutes = [13, 8, 9, 27]

    time_tables = []

    # 敦賀発の実ダイヤベース出発時刻（かがやき / つるぎ / はくたか）
    kagayaki_departures = [time(6, 11), time(7, 26), time(8, 15)]
    tsurugi_departures = [
        time(6, 47), time(7, 35), time(8, 6), time(8, 31),
        time(9, 11), time(9, 46), time(10, 18), time(10, 43),
        time(11, 15), time(11, 45),
    ]
    hakutaka_departures = [time(9, 58), time(10, 58), time(12, 0), time(14, 0), time(16, 0)]
    thunder_departures = [
        time(7, 10), time(8, 10), time(9, 10), time(10, 10),
        time(11, 10), time(12, 10), time(13, 10), time(14, 10),
    ]

    # 種別ごとに trains のインデックスを割り当て
    idx = 0
    kagayaki_trains = trains[idx:idx + len(kagayaki_nums)]
    idx += len(kagayaki_nums)
    hakutaka_trains = trains[idx:idx + len(hakutaka_nums)]
    idx += len(hakutaka_nums)
    tsurugi_trains = trains[idx:idx + len(tsurugi_nums)]
    idx += len(tsurugi_nums)
    thunder_trains = trains[idx:idx + len(thunder_nums)]

    def build_timetable_for_train(train_obj, depart_tsugara: time):
        current_arrival = depart_tsugara
        for i, station in enumerate(station_order):
            # 出発は到着＋1分（終点は出発なしでもよいが、ここでは一律設定）
            departure_time = add_minutes_to_time(current_arrival, 1)
            time_tables.append(
                TimeTable(
                    sid=station.sid,
                    tid=train_obj.tid,
                    arrival_time=current_arrival,
                    departure_time=departure_time
                )
            )
            if i < len(travel_minutes):
                current_arrival = add_minutes_to_time(departure_time, travel_minutes[i])

    # かがやき
    for train_obj, dep in zip(kagayaki_trains, kagayaki_departures):
        build_timetable_for_train(train_obj, dep)

    # はくたか
    for train_obj, dep in zip(hakutaka_trains, hakutaka_departures):
        build_timetable_for_train(train_obj, dep)

    # つるぎ
    for train_obj, dep in zip(tsurugi_trains, tsurugi_departures):
        build_timetable_for_train(train_obj, dep)

    # サンダーバード（敦賀→福井→金沢 のイメージで同じ駅順を使用）
    for train_obj, dep in zip(thunder_trains, thunder_departures):
        build_timetable_for_train(train_obj, dep)

    db.session.add_all(time_tables)

    #============================
    # Event（遅延イベント）
    #============================
    today = date.today()
    events = [
        Event(rid=reasons[1].rid, detail="大雪のため速度規制（福井〜芦原温泉間）", date=today),
        Event(rid=reasons[0].rid, detail="強風の影響で接続待ち合わせ", date=today),
        Event(rid=reasons[2].rid, detail="設備点検のため一時運転見合わせ", date=today),
    ]
    db.session.add_all(events)
    db.session.flush()  # eid を取得

    #============================
    # DelayInfo（遅延個別情報）※現実的な粒度で自動生成
    #============================
    delay_infos = []

    # 種別ごとに代表列車を1〜2本だけ選ぶ
    target_trains = [
        kagayaki_trains[0], kagayaki_trains[1], kagayaki_trains[2],
        hakutaka_trains[0], hakutaka_trains[1], hakutaka_trains[2],
        tsurugi_trains[0], tsurugi_trains[1], tsurugi_trains[2],
        thunder_trains[0], thunder_trains[1], thunder_trains[2],
    ]

    # 遅延パターン（軽い遅延中心）
    delay_minutes_pattern = [10,20,30,40]

    idx_event = 0
    idx_delay = 0

    for train_obj in target_trains:
        # 各種別に1
        for _ in range(1):
            event_obj = events[idx_event % len(events)]
            minutes = delay_minutes_pattern[idx_delay % len(delay_minutes_pattern)]

            # 現実的な判定
            is_cancel = (minutes >= 30 and idx_delay % 4 == 0)  # たまに運休
            is_change = (minutes >= 40 and not is_cancel)       # 40分超で経路変更扱い

            delay_infos.append(
                DelayInfo(
                    tid=train_obj.tid,
                    eid=event_obj.eid,
                    delay_minutes=minutes,
                    is_cancel=is_cancel,
                    is_change=is_change,
                )
            )

            idx_event += 1
            idx_delay += 1

    db.session.add_all(delay_infos)

    db.session.commit()

    print("Seed completed with realistic Hokuriku Shinkansen data!")
