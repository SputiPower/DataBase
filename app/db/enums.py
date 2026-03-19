from enum import Enum


class PassStatus(str, Enum):
    NEW = "new"
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
