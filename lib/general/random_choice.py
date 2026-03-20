import random


def weighted_random_choice(weights_dict: dict[str, float]):
    """Select a random key from a dictionary based on weighted probabilities."""
    if not weights_dict:
        raise ValueError("Weights dictionary cannot be empty")

    total_weight = sum(weights_dict.values())
    if total_weight <= 0:
        raise ValueError("Total weight must be positive")

    random_number = random.uniform(0, total_weight)
    cumulative_weight = 0

    for preference, weight in weights_dict.items():
        cumulative_weight += weight
        if random_number <= cumulative_weight:
            return preference

    return list(weights_dict.keys())[-1]
