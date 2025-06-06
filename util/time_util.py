import datetime


def now_millis() -> int:
    return int(datetime.datetime.now().timestamp() * 1000)


def cal_duration(start: datetime.datetime, end: datetime.datetime) -> int:
    return int(end.timestamp() - start.timestamp() * 1000)
