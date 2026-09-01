PROFILE_NAMES = ["Premium value", "Frequent loyalists", "Budget starters"]

def build_profiles(rows: list[dict], features: list[str]) -> list[dict]:
    profiles = []
    for cluster in sorted({row["cluster"] for row in rows}):
        group = [row for row in rows if row["cluster"] == cluster]
        profiles.append({"cluster": cluster, "count": len(group), "means": {feature: sum(row[feature] for row in group) / len(group) for feature in features}})
    ranked = sorted(profiles, key=lambda profile: (-profile["means"]["avg_order_value"], -profile["means"]["purchase_frequency"], profile["cluster"]))
    for index, profile in enumerate(ranked):
        profile["name"] = PROFILE_NAMES[index] if index < len(PROFILE_NAMES) else f"Cluster {profile['cluster']}"
        profile["guidance"] = "Hypothesis only · validate on observed outcomes."
        profile["name_basis"] = {"ranked_by": ["avg_order_value", "purchase_frequency", "cluster"], "rank": index + 1}
    return profiles
