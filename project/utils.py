from datetime import datetime, timezone


def time() -> datetime:
    return datetime.now(timezone.utc)


def timestamp():
    return time().timestamp()
