from src.experiment import FEATURES

def ordered_feature_values(values: dict) -> dict:
    missing = [feature for feature in FEATURES if feature not in values]
    if missing: raise ValueError(f"missing_features:{','.join(missing)}")
    return {feature: values[feature] for feature in FEATURES}
