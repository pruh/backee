from typing import Dict

from backee.model.rotation_strategy import RotationStrategy


def parse_rotation_strategy(data: Dict[str, int]) -> RotationStrategy:
    if data is None:
        data = {}

    return RotationStrategy(
        daily=data.get('daily', 1),
        monthly=data.get('monthly', 0),
        yearly=data.get('yearly', 0)
    )
