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
    "fg_pct_matchup_diff": "fg_pct",
    "opp_fg_pct_matchup_diff": "opp_fg_pct",
    "fg3_pct_matchup_diff": "fg3_pct",
    "opp_fg3_pct_matchup_diff": "opp_fg3_pct",
    "ft_pct_matchup_diff": "ft_pct",
    "reb_matchup_diff": "reb",
    "ast_matchup_diff": "ast",
    "stl_matchup_diff": "stl",
    "blk_matchup_diff": "blk",
    "tov_matchup_diff": "tov",
    "assist_turnover_ratio_matchup_diff":
        "assist_turnover_ratio",
    "reb_diff_matchup_diff": "reb_diff",
    "ast_diff_matchup_diff": "ast_diff",
    "tov_diff_matchup_diff": "tov_diff",
    "pace_matchup_diff": "pace",
    "ortg_matchup_diff": "ortg",
    "drtg_matchup_diff": "drtg",
    "efg_pct_matchup_diff": "efg_pct",
    "ts_pct_matchup_diff": "ts_pct"
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

    return {
        "team_a": team_a_name,
        "team_b": team_b_name,
        "team_a_win_probability": float(prob),
        "team_b_win_probability": float(1 - prob)
    }