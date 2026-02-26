import streamlit as st

st.set_page_config(layout="wide")
st.title("⚾ Dynasty Trade Evaluator")

from data_model import (
    load_model,
    render_model_settings_sidebar,
    render_trade_settings_sidebar
)

# Render sidebars
render_model_settings_sidebar()
render_trade_settings_sidebar()

# Load model using shared state
fantrax = load_model(
    st.session_state.r,
    st.session_state.g_pre30,
    st.session_state.g_post30,
    st.session_state.salary_weight,
    st.session_state.control_weight
)

players = fantrax["Player_Salary_Team"].sort_values().unique()

# -----------------------------
# TEAM SELECTION
# -----------------------------
if "trade_partner" not in st.session_state:
    st.session_state.trade_partner = None

if "receive_players" not in st.session_state:
    st.session_state.receive_players = []

st.divider()
st.subheader("🤝 Trade Setup")

# Exclude FA and waiver placeholders
excluded_statuses = [
    "FA",
    "W <small>(Wed)</small>",
    "W <small>(Tue)</small>"
]

teams = sorted(
    fantrax.loc[
        ~fantrax["Status"].isin(excluded_statuses),
        "Status"
    ].unique()
)

col_team1, col_team2 = st.columns(2)

with col_team1:
    your_team = st.selectbox("Your Team", teams)

with col_team2:
    trade_partner = st.selectbox(
    "Trade Partner",
    [t for t in teams if t != your_team],
    index=(
        [t for t in teams if t != your_team].index(st.session_state.trade_partner)
        if st.session_state.trade_partner in teams
        else 0
    )
)

# -----------------------------
# RESET PLAYER SELECTIONS IF TEAMS CHANGE
# -----------------------------
if "previous_your_team" not in st.session_state:
    st.session_state.previous_your_team = your_team

if "previous_trade_partner" not in st.session_state:
    st.session_state.previous_trade_partner = trade_partner

# If your team changed → clear send players
if st.session_state.previous_your_team != your_team:
    st.session_state.send_players = []
    st.session_state.previous_your_team = your_team

# If trade partner changed → clear receive players
if st.session_state.previous_trade_partner != trade_partner:
    st.session_state.receive_players = []
    st.session_state.previous_trade_partner = trade_partner


# Always keep current partner stored
st.session_state.trade_partner = trade_partner

# -----------------------------
# TRADE INTERFACE
# -----------------------------
# Filter rosters
your_roster = fantrax[fantrax["Status"] == your_team]
partner_roster = fantrax[fantrax["Status"] == trade_partner]

col1, col2 = st.columns(2)

with col1:
    st.subheader(f"📤 Players You Send ({your_team})")
    send_players = st.multiselect(
        "Select players to trade away",
        sorted(your_roster["Player_Salary_Team"].tolist())
    )

with col2:
    st.subheader(f"📥 Players You Receive ({trade_partner})")
    receive_players = st.multiselect(
    "Select players to acquire",
    sorted(partner_roster["Player_Salary_Team"].tolist()),
    # key = "receive_players"
    default=st.session_state.receive_players
)

# -----------------------------
# TRADE CALCULATION
# -----------------------------
def trade_value(player_list):
    if not player_list:
        return 0, 0, 0, 0
    subset = fantrax[fantrax["Player_Salary_Team"].isin(player_list)]
    return (
        subset["Net_Value_Old"].sum(),
        subset["Salary"].sum(),
        subset["True_Value"].sum(),
        subset["Net_True_Value"].sum()
    )

def apply_package_discount(total_value, player_count, discount_pct):
    """
    Applies a discount to total trade value if more than one player
    is included on that side of the trade.
    """
    if player_count > 1:
        return total_value * (1 - discount_pct)
    return total_value

send_raw_old, send_salary, send_raw_true, send_raw_net_true = trade_value(send_players)
receive_raw_old, receive_salary, receive_raw_true, receive_raw_net_true = trade_value(receive_players)

send_old = apply_package_discount(
    send_raw_old,
    len(send_players),
    st.session_state.multi_player_discount
)

send_true = apply_package_discount(
    send_raw_true,
    len(send_players),
    st.session_state.multi_player_discount
)

send_net_true = apply_package_discount(
    send_raw_net_true,
    len(send_players),
    st.session_state.multi_player_discount
)

receive_old = apply_package_discount(
    receive_raw_old,
    len(receive_players),
    st.session_state.multi_player_discount
)

receive_true = apply_package_discount(
    receive_raw_true,
    len(receive_players),
    st.session_state.multi_player_discount
)

receive_net_true = apply_package_discount(
    receive_raw_net_true,
    len(receive_players),
    st.session_state.multi_player_discount
)

net_value_old = receive_old - send_old
net_salary = receive_salary - send_salary
net_value_true = receive_net_true - send_net_true

st.write(f"Send Value (Raw): {send_raw_net_true:.2f}")
st.write(f"Receive Value (Raw): {receive_raw_net_true:.2f}")

if len(send_players) > 1:
    st.write(f"Package discount applied to send side ({st.session_state.multi_player_discount:.0%})")

if len(receive_players) > 1:
    st.write(f"Package discount applied to receive side ({st.session_state.multi_player_discount:.0%})")

st.write(f"Net Value After Discount: {net_value_true:.2f}")

# -----------------------------
# TRADE Graph and TRADE VERDICT
# -----------------------------

total = send_net_true + receive_net_true

if total == 0:
    position = 0.5
else:
    position = receive_net_true / total  # value between 0 and 1

st.divider()
st.subheader("📊 Trade Results")

import matplotlib.pyplot as plt

# Fair bounds (adjust tolerance here)
fair_lower = 0.5 - (st.session_state.trade_margin / 2)
fair_upper = 0.5 + (st.session_state.trade_margin / 2)

fig, ax = plt.subplots(figsize=(8, 1))

# Background bar (light red)
ax.barh(0, 1, color="#ee6b6e", height=0.3)

# Filled portion (blue)
ax.barh(0, position, color="#1f77b4", height=0.3)

# Fair bound markers
ax.axvline(fair_lower, ymin=0.25, ymax=0.75, linewidth=3, color = 'white')
ax.axvline(fair_upper, ymin=0.25, ymax=0.75, linewidth=3, color = 'white')

# Remove axes
ax.set_xlim(0, 1)
ax.set_ylim(-0.5, 0.5)
ax.axis("off")

ax.scatter(position, 0, s=300, edgecolors = '#FFFFFF')

# Dynamic centers
left_center = position / 2
right_center = position + (1 - position) / 2

# Labels inside bar
ax.text(
    left_center, 0,
    f"{your_team}",
    ha="center",
    va="center",
    color="white",
    fontsize=12,
    fontweight="bold"
)

ax.text(
    right_center, 0,
    f"{trade_partner}",
    ha="center",
    va="center",
    color="white",
    fontsize=12,
    fontweight="bold"
)

st.pyplot(fig)


colA, colB, colC = st.columns(3)

with colA:
    st.metric("Value Sent", round(send_net_true, 2))
    st.metric("Salary Sent", round(send_salary, 2))
    st.metric("Value Sent (Old)", round(send_old, 2))

with colB:
    st.metric("Value Received", round(receive_net_true, 2))
    st.metric("Salary Received", round(receive_salary, 2))
    st.metric("Value Received (Old)", round(receive_old, 2))

with colC:
    st.metric("Net Value", round(net_value_true, 2))
    st.metric("Net Salary Change", round(net_salary, 2))
    st.metric("Net Value (Old)", round(net_value_old, 2))

# ----- Improved Verdict Logic -----

if position > 0.5 + (st.session_state.trade_margin / 2):
    st.success("✅ Favors Your Team")
elif position < 0.5 - (st.session_state.trade_margin / 2):
    st.error("❌ Favors Trade Partner")
else:
    st.info("⚖️ Even Trade")

# -----------------------------
# 1-FOR-1 TRADE RECOMMENDATIONS
# -----------------------------
if send_players:

    st.divider()
    st.subheader("🤖 1-for-1 Trade Recommendations")

    # -------- FILTER CONTROLS --------
    colF1, colF2, colF3, colF4 = st.columns(4)

    with colF1:
        rec_team_filter = st.selectbox(
            "Filter by Fantasy Team",
            ["All"] + teams
        )

    with colF2:
            position_filter = st.multiselect(
                "Filter by Position", 
                ["SP", "RP", "C", "1B", "2B", "3B", "SS", "OF", "UT"]
            )

    with colF3:
        rec_limit = st.number_input(
            "Number of Recommendations",
            min_value=5,
            max_value=100,
            value=10,
            step=5
        )

    with colF4:
        rank_filter = st.segmented_control(
            "Ranking",
            ["Net True Value", "True Value"],
            default = "Net True Value"
        )

    # -------- BUILD FILTERED POOL --------
    pool = fantrax.copy()

    # Remove your own team
    pool = pool[pool["Status"] != your_team]
    pool = pool[~pool["Status"].isin(excluded_statuses)]

    # Apply team filter
    if rec_team_filter != "All":
        pool = pool[pool["Status"] == rec_team_filter]

    # Apply position filter
    if position_filter:
        pool = pool[
        pool["Position"].apply(
            lambda pos: any(p in pos for p in position_filter)
        )
    ]

    # -------- BUILD RECOMMENDATION TABLE --------
    rec_df = pool[[
        "Player_Salary_Team",
        "Status",
        "Position",
        "Total_Value_Old",
        "Net_Value_Old",
        "True_Value",
        "Net_True_Value"
    ]].copy()

    # Apply rank filter
    if rank_filter == "Net True Value":
        rec_df["Difference"] = rec_df["Net_True_Value"] - send_net_true
        rec_df["Abs_Diff"] = rec_df["Difference"].abs()
    else: 
        rec_df["Difference"] = rec_df["True_Value"] - send_true
        rec_df["Abs_Diff"] = rec_df["Difference"].abs()

    # Sort from smallest to largest difference
    rec_df = rec_df.sort_values("Abs_Diff").head(rec_limit)

    st.dataframe(
        rec_df[[
            "Player_Salary_Team",
            "Status",
            "Position",
            "Total_Value_Old",
            "Net_Value_Old",
            "True_Value",
            "Net_True_Value",
            "Difference"
        ]],
        use_container_width=True
    )

if send_players and not rec_df.empty:

    chosen_player = st.selectbox(
        "Select a Suggested Player to Load",
        rec_df["Player_Salary_Team"]
    )

    if st.button("Load Suggested Trade"):

        selected_team = rec_df.loc[
            rec_df["Player_Salary_Team"] == chosen_player,
            "Status"
        ].values[0]

        # Store in session state
        st.session_state.trade_partner = selected_team
        st.session_state.receive_players = [chosen_player]

        st.rerun()


# -----------------------------
# OPTIONAL DETAIL TABLE
# -----------------------------
if send_players or receive_players:
    st.divider()
    st.subheader("Player Breakdown")

    breakdown = fantrax[
        fantrax["Player_Salary_Team"].isin(send_players + receive_players)
    ][[
        "Player",
        "Age",
        "Salary",
        "Contract",
        "Score",
        "Score_NPV",
        "Fair_Salary",
        "Dynasty_Salary",
        "Control",
        "Total_Value_Old",
        "Net_Value_Old",
        "True_Value",
        "Net_True_Value"
    ]]

    st.dataframe(
        breakdown.sort_values("Net_True_Value", ascending=False),
        use_container_width=True
    )
