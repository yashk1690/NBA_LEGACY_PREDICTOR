import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

# ─────────────────────────────────────────
# Load cluster data
# ─────────────────────────────────────────

cluster_df = pd.read_csv("data/nba_team_clusters.csv")

cluster_df["DISPLAY_NAME"] = (
    cluster_df["SEASON_STR"]
    + " | "
    + cluster_df["TEAM_NAME"]
)

# ─────────────────────────────────────────
# Features used for distance calculation
# (same as your k-means clustering)
# ─────────────────────────────────────────

CLUSTER_FEATURES = [
    "pace",
    "ortg",
    "drtg",
    "net_rating",
    "efg_pct",
    "ts_pct",
    "fg_pct",
    "fg3_pct",
    "ft_pct",
    "reb",
    "ast",
    "stl",
    "blk",
    "tov",
    "assist_turnover_ratio",
    "reb_diff",
    "ast_diff",
    "tov_diff"
]

FEATURE_LABELS = {
    "pace":                  "Pace",
    "ortg":                  "Off. Rating",
    "drtg":                  "Def. Rating",
    "net_rating":            "Net Rating",
    "efg_pct":               "Eff. FG %",
    "ts_pct":                "True Shooting %",
    "fg_pct":                "FG %",
    "fg3_pct":               "3PT %",
    "ft_pct":                "FT %",
    "reb":                   "Rebounds",
    "ast":                   "Assists",
    "stl":                   "Steals",
    "blk":                   "Blocks",
    "tov":                   "Turnovers",
    "assist_turnover_ratio": "AST/TOV",
    "reb_diff":              "Reb. Margin",
    "ast_diff":              "Ast. Margin",
    "tov_diff":              "TOV Margin",
}

CLUSTER_COLORS = {
    "Offensive Dynasty":      "#C8102E",
    "Struggling Grindhouse":  "#555555",
    "Showtime Run-and-Gun":   "#FFC72C",
    "Average Contender":      "#1D428A",
    "Defensive Dynasty":      "#007A33",
}

# ─────────────────────────────────────────
# Pre-scale features once at load time
# ─────────────────────────────────────────

_feature_matrix = cluster_df[CLUSTER_FEATURES].values.astype(float)

scaler = StandardScaler()
_scaled_matrix = scaler.fit_transform(_feature_matrix)


# ─────────────────────────────────────────
# Lookup helpers
# ─────────────────────────────────────────

def get_cluster_teams():
    """All unique display names in the cluster dataset."""
    return sorted(cluster_df["DISPLAY_NAME"].unique().tolist())


def _get_row(display_name):
    row = cluster_df[cluster_df["DISPLAY_NAME"] == display_name]
    if len(row) == 0:
        raise ValueError(f"Team not found in cluster data: {display_name}")
    return row.iloc[0]


# ─────────────────────────────────────────
# Key stat differentials between two teams
# ─────────────────────────────────────────

DISPLAY_FEATURES = [
    "ortg", "drtg", "pace", "efg_pct", "ts_pct",
    "reb", "ast", "stl", "blk", "tov"
]

# For these, a lower value is better
LOWER_IS_BETTER_SIM = {"drtg", "tov"}


def _build_stat_comparison(query_row, match_row):
    """
    Return top 4 stats where the query team differs most
    from the match team, with direction arrows.
    """
    diffs = []
    for feat in DISPLAY_FEATURES:
        qv = float(query_row[feat])
        mv = float(match_row[feat])
        diff = qv - mv
        pct = feat in ("efg_pct", "ts_pct", "fg_pct", "fg3_pct", "ft_pct")
        abs_diff = abs(diff * 100 if pct else diff)
        diffs.append({
            "stat":    FEATURE_LABELS.get(feat, feat),
            "query":   round(qv * 100 if pct else qv, 1),
            "match":   round(mv * 100 if pct else mv, 1),
            "diff":    round(diff * 100 if pct else diff, 1),
            "_abs":    abs_diff,
        })
    diffs.sort(key=lambda x: x["_abs"], reverse=True)
    return [{k: v for k, v in d.items() if k != "_abs"} for d in diffs[:4]]


# ─────────────────────────────────────────
# Main similarity function
# ─────────────────────────────────────────

def find_similar_teams(display_name, n=10):

    query_row = _get_row(display_name)
    query_idx = cluster_df.index[
        cluster_df["DISPLAY_NAME"] == display_name
    ][0]

    # Scaled feature vector for the query team
    query_scaled = _scaled_matrix[
        cluster_df.index.get_loc(query_idx)
    ]

    # Euclidean distances to every team
    diffs      = _scaled_matrix - query_scaled
    distances  = np.sqrt((diffs ** 2).sum(axis=1))

    # Attach distances to dataframe rows and sort
    ranked = cluster_df.copy()
    ranked["_dist"] = distances
    ranked = ranked[
        ranked["DISPLAY_NAME"] != display_name
    ].sort_values("_dist")

    top = ranked.head(n)

    # ── Query team info ───────────────────────────────

    cluster_name  = query_row["cluster_name"]
    cluster_color = CLUSTER_COLORS.get(cluster_name, "#C8102E")

    query_stats = {
        feat: (
            round(float(query_row[feat]) * 100, 1)
            if feat in ("efg_pct","ts_pct","fg_pct","fg3_pct","ft_pct")
            else round(float(query_row[feat]), 1)
        )
        for feat in DISPLAY_FEATURES
    }

    # ── Build similar teams list ──────────────────────

    similar = []
    for _, match_row in top.iterrows():

        # Similarity score: 0–100 (100 = identical)
        max_dist = distances.max()
        score    = round((1 - match_row["_dist"] / max_dist) * 100, 1)

        mc = match_row["cluster_name"]

        similar.append({
            "display_name":    match_row["DISPLAY_NAME"],
            "team_name":       match_row["TEAM_NAME"],
            "season":          match_row["SEASON_STR"],
            "cluster":         mc,
            "cluster_color":   CLUSTER_COLORS.get(mc, "#C8102E"),
            "similarity":      score,
            "era":             match_row["ERA"],
            "win_pct":         round(float(match_row["win_pct"]) * 100, 1),
            "stat_comparison": _build_stat_comparison(query_row, match_row),
        })

    return {
        "query":         display_name,
        "team_name":     query_row["TEAM_NAME"],
        "season":        query_row["SEASON_STR"],
        "cluster":       cluster_name,
        "cluster_color": cluster_color,
        "era":           query_row["ERA"],
        "win_pct":       round(float(query_row["win_pct"]) * 100, 1),
        "ortg":          round(float(query_row["ortg"]), 1),
        "drtg":          round(float(query_row["drtg"]), 1),
        "pace":          round(float(query_row["pace"]), 1),
        "stats":         query_stats,
        "similar_teams": similar,
    }