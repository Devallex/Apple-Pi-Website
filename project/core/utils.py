from datetime import datetime, timezone


def time() -> datetime:
    return datetime.now(timezone.utc)


def timestamp():
    return time().timestamp()


def getDateText(
    date,
):  # TODO: Replace all instances of getDateText with this OR put it into a base DB class
    return str(datetime.fromtimestamp(date))
