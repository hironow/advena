from datetime import datetime
from pydantic import BaseModel


class FeedItem(BaseModel):
    title: str
    link: str
    description: str
    guid_url: str
    guid_isPermaLink: bool
    guid: str
    category: str
    pubDate: datetime
