from dataclasses import dataclass


@dataclass
class RotationStrategy(object):
    daily: int
    monthly: int
    yearly: int
