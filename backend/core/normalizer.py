def min_max_normalize(feature_dict: dict) -> dict:
    """
    Normalizes each feature across all nodes or edges to [0,1].
    """
    keys = list(feature_dict.keys())
    feature_names = feature_dict[keys[0]].keys()

    normalized = {k: {} for k in keys}

    for feature in feature_names:
        values = [feature_dict[k][feature] for k in keys]
        min_val = min(values)
        max_val = max(values)

        for k in keys:
            if max_val == min_val:
                normalized[k][feature] = 0.0
            else:
                normalized[k][feature] = (
                    feature_dict[k][feature] - min_val
                ) / (max_val - min_val)

    return normalized
