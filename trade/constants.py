from enum import Enum


class ChoiceEnum(Enum):

    @classmethod
    def choice(cls):
        return tuple(e.value for e in cls)

    def code(self):
        return self.value[0] if isinstance(self.value, tuple) else self.value

    def desc(self):
        return self.value[1] if isinstance(self.value, tuple) else self.value

    @classmethod
    def code_of(cls, code):
        for e in cls:
            if e.code() == code:
                return e
        return None


class Direction(ChoiceEnum):
    BUY = -1, "买"
    SELL = 1, "卖"


class Confidence(ChoiceEnum):
    HIGH = 1, "高"
    MIDDLE_HIGH = 0.75, "中高"
    MIDDLE = 0.5, "中"
    MIDDLE_LOW = 0.25, "中低"
    LOW = 0.1, "低"

class Trend(ChoiceEnum):
    UP = 1
    HORIZONTAL = 0
    DOWN = -1