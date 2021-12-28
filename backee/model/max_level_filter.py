class MaxLevelFilter(object):
    def __init__(self, max_level):
        self.__max_level = max_level

    def __eq__(self, other):
        return (
            isinstance(other, MaxLevelFilter) and self.__max_level == other.__max_level
        )

    def filter(self, record):
        return record.levelno <= self.__max_level
