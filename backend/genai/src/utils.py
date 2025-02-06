import uuid
from datetime import UTC, datetime, timedelta, tzinfo


def new_id() -> str:
    """IDを生成する。必ずUUID v4を使う"""
    return str(uuid.uuid4())


def is_valid_uuid(value: str) -> bool:
    """文字列が有効なUUID v4かを判定する"""
    try:
        u = uuid.UUID(value)
    except ValueError:
        return False
    return u.version == 4


def get_now() -> datetime:
    """現在日時を取得する。必ずUTCを使う"""
    now = datetime.now(tz=UTC)
    return now


def is_valid_iso_format(value: str) -> bool:
    """ISO 8601 形式の文字列が有効かどうかを判定する"""
    try:
        # 'Z' を '+00:00' に変換して対応する
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        datetime.fromisoformat(value)
        return True
    except ValueError:
        return False


def get_tz(iso_format: str) -> tzinfo | None:
    """ISO 8601 形式の文字列から tzinfo を取得する
    末尾が 'Z' の場合は UTC として解釈する
    """
    if iso_format.endswith("Z"):
        iso_format = iso_format[:-1] + "+00:00"
    return datetime.fromisoformat(iso_format).tzinfo


def is_intraday(date_a: datetime, date_b: datetime) -> bool:
    """指定引数AはBと同じ日か"""
    return date_a.date() == date_b.date()


def is_consecutive_days(date_a: datetime, date_b: datetime) -> bool:
    """指定引数AはBの翌日か"""
    return date_a.date() == date_b.date() + timedelta(days=1)


def get_diff_days(date_a: datetime, date_b: datetime) -> int:
    """指定引数AはBの何日後か"""
    return (date_a.date() - date_b.date()).days
