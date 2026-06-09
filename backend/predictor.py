import joblib
import pandas as pd

# -----------------------------
# Load assets
# -----------------------------

bundle = joblib.load(
    "models/nba_historical_simulator.pkl"
)

model = bundle["model"]
feature_order = bundle["features"]

profiles = pd.read_csv(
    "data/team_profiles_v3.csv"
)

# -----------------------------
# Team lookup
# -----------------------------

profiles["DISPLAY_NAME"] = (
    profiles["SEASON_STR"]
    + " | "
    + profiles["TEAM_NAME"]
)


def get_team_profile(display_name):

    row = profiles[
        profiles["DISPLAY_NAME"] == display_name
    ]

    if len(row) == 0:
        raise ValueError(
            f"Team not found: {display_name}"
        )

    return row.iloc[0]


# -----------------------------
# Matchup creation
# -----------------------------

FEATURE_MAP = {
    "fg_pct_matchup_diff":              "fg_pct",
    "opp_fg_pct_matchup_diff":          "opp_fg_pct",
    "fg3_pct_matchup_diff":             "fg3_pct",
    "opp_fg3_pct_matchup_diff":         "opp_fg3_pct",
    "ft_pct_matchup_diff":              "ft_pct",
    "reb_matchup_diff":                 "reb",
    "ast_matchup_diff":                 "ast",
    "stl_matchup_diff":                 "stl",
    "blk_matchup_diff":                 "blk",
    "tov_matchup_diff":                 "tov",
    "assist_turnover_ratio_matchup_diff": "assist_turnover_ratio",
    "reb_diff_matchup_diff":            "reb_diff",
    "ast_diff_matchup_diff":            "ast_diff",
    "tov_diff_matchup_diff":            "tov_diff",
    "pace_matchup_diff":                "pace",
    "ortg_matchup_diff":                "ortg",
    "drtg_matchup_diff":                "drtg",
    "efg_pct_matchup_diff":             "efg_pct",
    "ts_pct_matchup_diff":              "ts_pct"
}

# Human-readable labels for each feature
FEATURE_DISPLAY_NAMES = {
    "fg_pct_matchup_diff":              "Field Goal %",
    "opp_fg_pct_matchup_diff":          "Opp. Field Goal % (Defense)",
    "fg3_pct_matchup_diff":             "3-Point %",
    "opp_fg3_pct_matchup_diff":         "Opp. 3-Point % (Defense)",
    "ft_pct_matchup_diff":              "Free Throw %",
    "reb_matchup_diff":                 "Rebounds",
    "ast_matchup_diff":                 "Assists",
    "stl_matchup_diff":                 "Steals",
    "blk_matchup_diff":                 "Blocks",
    "tov_matchup_diff":                 "Turnovers",
    "assist_turnover_ratio_matchup_diff": "Assist / Turnover Ratio",
    "reb_diff_matchup_diff":            "Rebound Margin",
    "ast_diff_matchup_diff":            "Assist Margin",
    "tov_diff_matchup_diff":            "Turnover Margin",
    "pace_matchup_diff":                "Pace",
    "ortg_matchup_diff":                "Offensive Rating",
    "drtg_matchup_diff":                "Defensive Rating",
    "efg_pct_matchup_diff":             "Effective FG %",
    "ts_pct_matchup_diff":              "True Shooting %"
}

# For these stats, lower is better —
# so a negative differential favours Team A
LOWER_IS_BETTER = {
    "drtg_matchup_diff",
    "tov_matchup_diff",
    "tov_diff_matchup_diff",
    "opp_fg_pct_matchup_diff",
    "opp_fg3_pct_matchup_diff"
}

# These are stored as decimals (e.g. 0.48);
# multiply ×100 to display as percentage points
PCT_FEATURES = {
    "fg_pct_matchup_diff",
    "opp_fg_pct_matchup_diff",
    "fg3_pct_matchup_diff",
    "opp_fg3_pct_matchup_diff",
    "ft_pct_matchup_diff",
    "efg_pct_matchup_diff",
    "ts_pct_matchup_diff"
}


def build_feature_vector(team_a, team_b):

    features = {}

    for matchup_feature, profile_col in FEATURE_MAP.items():

        features[matchup_feature] = (
            float(team_a[profile_col])
            -
            float(team_b[profile_col])
        )

    return features


# -----------------------------
# Top factors
# -----------------------------

def get_top_factors(
    feature_vector,
    team_a_name,
    team_b_name,
    winner,
    n=5
):
    """
    Return the n stats where the winning team holds the largest
    advantages over their opponent.
    """

    factors = []

    for feat, value in feature_vector.items():

        lower_is_better = feat in LOWER_IS_BETTER

        team_a_favored = (
            (value > 0 and not lower_is_better)
            or
            (value < 0 and lower_is_better)
        )

        if feat in PCT_FEATURES:
            display_value = f"{abs(value * 100):.1f} pp"
        else:
            display_value = f"{abs(value):.1f}"

        advantage = team_a_name if team_a_favored else team_b_name

        factors.append({
            "stat":      FEATURE_DISPLAY_NAMES.get(feat, feat),
            "value":     display_value,
            "advantage": advantage,
            "_abs":      abs(value)
        })

    # Sort by magnitude, then keep only the winning team's edges
    factors.sort(key=lambda x: x["_abs"], reverse=True)

    winning_factors = [
        f for f in factors
        if f["advantage"] == winner
    ]

    return [
        {k: v for k, v in f.items() if k != "_abs"}
        for f in winning_factors[:n]
    ]


# -----------------------------
# Prediction
# -----------------------------

def predict_matchup(team_a_name, team_b_name):

    team_a = get_team_profile(team_a_name)
    team_b = get_team_profile(team_b_name)

    feature_vector = build_feature_vector(
        team_a,
        team_b
    )

    X = pd.DataFrame([feature_vector])
    X = X[feature_order]

    prob = model.predict_proba(X)[0, 1]

    winner = team_a_name if prob >= 0.5 else team_b_name

    top_factors = get_top_factors(
        feature_vector,
        team_a_name,
        team_b_name,
        winner
    )

    return {
        "team_a":                   team_a_name,
        "team_b":                   team_b_name,
        "team_a_win_probability":   float(prob),
        "team_b_win_probability":   float(1 - prob),
        "winner":                   winner,
        "top_factors":              top_factors
    }