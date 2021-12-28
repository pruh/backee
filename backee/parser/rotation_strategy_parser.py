from typing import Dict

from backee.model.rotation_strategy import RotationStrategy


def parse_rotation_strategy(data: Dict[str, int]) -> RotationStrategy:
    return RotationStrategy(
        daily=data["daily"], monthly=data["monthly"], yearly=data["yearly"]
    )
