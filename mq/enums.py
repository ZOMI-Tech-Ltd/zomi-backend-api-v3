
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List


class MediaType(Enum):
    IMAGE = "IMAGE"
    VIDEO = "VIDEO"


class MediaSource(Enum):
    INTERNET = "INTERNET"
    USER_AVATAR = "USER_AVATAR"
    VOLCENGINE = "VOLCENGINE"


class CollectState(Enum):
    COLLECT = 1
    UNCOLLECT = 2


class RecommendState(Enum):
    DEFAULT = 0
    RECOMMEND = 1
    NOT_RECOMMEND = 2


# Queue names
class QueueName(Enum):
    MEDIA_CREATE = "media/create"
    DISH_COLLECT = "dish/collect"
    TASTE_CREATE = "taste/create"
    TASTE_ADD_DISH = "taste/addDish"


@dataclass
class MediaCreateMessage:
    mediaId: str
    type: str  # MediaType
    url: str
    source: str  # MediaSource
    width: Optional[int] = None
    height: Optional[int] = None


@dataclass
class DishCollectMessage:
    userId: str
    dishId: str
    state: int  # CollectState


@dataclass
class TasteCreateMessage:
    id: str
    userId: str
    dishId: str
    comment: str
    recommendState: int  # RecommendState
    mediaIds: Optional[List[str]] = None


@dataclass
class TasteAddDishMessage:
    id: str
    userId: str
    merchantID: str
    name: str
    price: Optional[int] = None
    mediaIds: Optional[List[str]] = None
    description: Optional[str] = None
    characteristic: Optional[str] = None

