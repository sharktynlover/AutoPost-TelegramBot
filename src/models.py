from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Post:
    id: int
    text: str
    photo_file_id: str | None
    run_at: datetime
    send_to_tg: bool
    send_to_vk: bool
    status: str
