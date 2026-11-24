import pandas as pd
import requests
import streamlit as st

TEAM = "Georgia Tech"
HEADERS = {"Authorization": f"Bearer {st.secrets['CFBD_API_KEY']}"}

st.title("Georgia Tech Football: Season Explorer")


# ---------- Functions that ask the CFBD API for data ----------
# @st.cache_data remembers the answers so we don't use up our request limit.

@st.cache_data
def get_games(year):
    """Get all of Georgia Tech's games in one season."""
    response = requests.get(
        "https://api.collegefootballdata.com/games",
        params={"year": year, "team": TEAM},
        headers=HEADERS,
    )
    response.raise_for_status()  # raises an error if the request failed
    return response.json()


@st.cache_data
def get_player_stats(year, category):
    """Get Georgia Tech player stats for one season and stat category."""
    response = requests.get(
        "https://api.collegefootballdata.com/stats/player/season",
        params={"year": year, "team": TEAM, "category": category},
        headers=HEADERS,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data
def get_matchup(opponent, start_year):
    """Get every game between Georgia Tech and one opponent."""
    response = requests.get(
        "https://api.collegefootballdata.com/teams/matchup",
        params={"team1": TEAM, "team2": opponent, "minYear": start_year},
        headers=HEADERS,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data
def get_win_probs(year):
    """Get CFBD's pregame win probabilities for Georgia Tech's games."""
    response = requests.get(
        "https://api.collegefootballdata.com/metrics/wp/pregame",
        params={"year": year, "team": TEAM},
        headers=HEADERS,
    )
    response.raise_for_status()
    return response.json()


# ---------- Season picker (used by most sections below) ----------
year = st.selectbox("Season", list(range(2026, 2009, -1)))

try:
    games = get_games(year)
except requests.RequestException:
    st.error("Couldn't load data. Check your CFBD key in secrets.toml.")
    st.stop()


# =============== SECTION 1: SEASON EXPLORER ===============
st.header("Season Explorer")
location = st.selectbox("Which games?", ["All", "Home", "Away"])

# YOUR OWN CODE: turn the raw API data into simple rows
rows = []
for game in sorted(games, key=lambda g: g["startDate"]):
    if game["homePoints"] is None:
        continue  # game hasn't been played yet
    if game["homeTeam"] == TEAM:
        rows.append({
            "Opponent": game["awayTeam"],
            "Location": "Home",
            "GT Points": game["homePoints"],
            "Opp Points": game["awayPoints"],
        })
    else:
        rows.append({
            "Opponent": game["homeTeam"],
            "Location": "Away",
            "GT Points": game["awayPoints"],
            "Opp Points": game["homePoints"],
        })

if len(rows) == 0:
    st.info("No finished games found for this season.")
else:
    df = pd.DataFrame(rows)
    if location != "All":
        df = df[df["Location"] == location]
    df = df.reset_index(drop=True)
    df["Game #"] = df.index + 1
    df["Margin"] = df["GT Points"] - df["Opp Points"]

    wins = int((df["Margin"] > 0).sum())
    losses = len(df) - wins
    st.metric("Record (for the games shown)", f"{wins}-{losses}")

    st.subheader("Points scored vs. points allowed")
    st.line_chart(df, x="Game #", y=["GT Points", "Opp Points"])

    st.subheader("Margin of victory (above 0 = win)")
    st.bar_chart(df, x="Game #", y="Margin")

    st.dataframe(df[["Game #", "Opponent", "Location", "GT Points", "Opp Points", "Margin"]])


# =============== SECTION 2: PLAYER STATS ===============
st.header("Player Stats")
category = st.selectbox("Stat category", ["passing", "rushing", "receiving"])

try:
    player_data = get_player_stats(year, category)
except requests.RequestException:
    st.error("Couldn't load player stats.")
    player_data = []

if len(player_data) == 0:
    st.info("No player stats found for this season and category.")
else:
    stats_df = pd.DataFrame(player_data)
    stats_df["stat"] = pd.to_numeric(stats_df["stat"], errors="coerce")

    player = st.selectbox("Player", sorted(stats_df["player"].unique()))
    stat_type = st.selectbox("Stat to compare across players", sorted(stats_df["statType"].unique()))

    st.subheader(f"{player}: {category} stats")
    st.dataframe(stats_df[stats_df["player"] == player][["statType", "stat"]])

    st.subheader(f"Top Georgia Tech players by {stat_type}")
    leaders = stats_df[stats_df["statType"] == stat_type]
    leaders = leaders.sort_values("stat", ascending=False).head(10)
    st.bar_chart(leaders, x="player", y="stat")


# =============== SECTION 3: OPPONENT HISTORY ===============
st.header("Opponent History")

opponent = st.selectbox("Opponent", [
    "Georgia", "Clemson", "Duke", "Virginia Tech", "Miami", "North Carolina",
    "NC State", "Florida State", "Notre Dame", "Auburn", "Alabama", "Tennessee",
    "Wake Forest", "Boston College", "Pittsburgh", "Virginia", "Syracuse",
    "Louisville", "Vanderbilt",
])
start_year = st.slider("Look at games since", 1950, 2025, 1950)

try:
    matchup = get_matchup(opponent, start_year)
except requests.RequestException:
    st.error("Couldn't load matchup data.")
    matchup = None

history = []
if matchup is not None:
    # YOUR OWN CODE: work out each game from Georgia Tech's point of view
    for game in matchup["games"]:
        if game["homeTeam"] == TEAM:
            tech_pts, opp_pts = game["homeScore"], game["awayScore"]
        else:
            tech_pts, opp_pts = game["awayScore"], game["homeScore"]
        if tech_pts is None or opp_pts is None:
            continue
        history.append({
            "Season": game["season"],
            "GT Points": tech_pts,
            "Opp Points": opp_pts,
            "Margin": tech_pts - opp_pts,
        })

if len(history) == 0:
    st.info("No games found for this opponent and year range.")
else:
    hist_df = pd.DataFrame(history)
    h_wins = int((hist_df["Margin"] > 0).sum())
    h_losses = int((hist_df["Margin"] < 0).sum())
    h_ties = int((hist_df["Margin"] == 0).sum())
    win_pct = h_wins / len(hist_df) * 100  # my own win percentage calculation

    col1, col2 = st.columns(2)
    col1.metric("Record vs. " + opponent, f"{h_wins}-{h_losses}-{h_ties}")
    col2.metric("Win percentage", f"{win_pct:.1f}%")

    st.subheader("All-time results")
    results = pd.DataFrame(
        {"Games": [h_wins, h_losses, h_ties]},
        index=["Tech wins", "Opponent wins", "Ties"],
    )
    st.bar_chart(results)

    st.subheader("Margin by season (above 0 = Tech win)")
    st.line_chart(hist_df, x="Season", y="Margin")


# =============== SECTION 4: WIN PROBABILITY TRACKER ===============
st.header("Win Probability Tracker")
cutoff = st.slider("Count it as an upset if the winner had under this chance (%)", 5, 50, 30)

try:
    wp_data = get_win_probs(year)
except requests.RequestException:
    st.error("Couldn't load win probability data.")
    wp_data = []

# A lookup table: game id -> that game's probability info
wp_by_id = {w["gameId"]: w for w in wp_data}

# YOUR OWN CODE: match each probability to the real result
wp_rows = []
for game in sorted(games, key=lambda g: g["startDate"]):
    wp = wp_by_id.get(game["id"])
    if game["homePoints"] is None or wp is None or wp["homeWinProbability"] is None:
        continue  # not played yet, or no probability available
    if game["homeTeam"] == TEAM:
        opp_name = game["awayTeam"]
        tech_prob = wp["homeWinProbability"]
        game_margin = game["homePoints"] - game["awayPoints"]
    else:
        opp_name = game["homeTeam"]
        tech_prob = 1 - wp["homeWinProbability"]
        game_margin = game["awayPoints"] - game["homePoints"]
    wp_rows.append({
        "Opponent": opp_name,
        "GT Win Probability (%)": round(tech_prob * 100, 1),
        "Result": "Win" if game_margin > 0 else "Loss",
    })

if len(wp_rows) == 0:
    st.info("No win probability data for this season.")
else:
    wp_df = pd.DataFrame(wp_rows)
    wp_df["Game #"] = wp_df.index + 1

    expected_wins = wp_df["GT Win Probability (%)"].sum() / 100
    actual_wins = int((wp_df["Result"] == "Win").sum())

    c1, c2 = st.columns(2)
    c1.metric("Expected wins (from probabilities)", round(expected_wins, 1))
    c2.metric("Actual wins", actual_wins)

    st.subheader("Georgia Tech's win probability by game")
    st.bar_chart(wp_df, x="Game #", y="GT Win Probability (%)")

    st.subheader("Upsets")
    found_upset = False
    for _, row in wp_df.iterrows():
        prob = row["GT Win Probability (%)"]
        if row["Result"] == "Win" and prob < cutoff:
            st.write(f"Tech beat {row['Opponent']} with only a {prob}% chance.")
            found_upset = True
        elif row["Result"] == "Loss" and prob > 100 - cutoff:
            st.write(f"Tech lost to {row['Opponent']} with a {prob}% chance.")
            found_upset = True
    if not found_upset:
        st.write("No upsets at this cutoff.")

    st.dataframe(wp_df[["Game #", "Opponent", "GT Win Probability (%)", "Result"]])
