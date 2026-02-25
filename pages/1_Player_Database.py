import streamlit as st

st.set_page_config(layout="wide")
st.title("📊 Player Database")

from data_model import load_model, render_model_settings_sidebar

render_model_settings_sidebar()

fantrax = load_model(
    st.session_state.r,
    st.session_state.g_pre30,
    st.session_state.g_post30,
    st.session_state.control_weight
)


# -----------------------------
# FILTER SECTION
# -----------------------------
st.sidebar.header("Filters")

# ---- Status Filter ----
status_options = sorted(fantrax["Status"].dropna().unique())

status_filter = st.sidebar.selectbox(
    "Filter by Status",
    options=["All"] + status_options,
    index=0
)

# ---- Player Filter ----
player_options = sorted(fantrax["Player"].dropna().unique())
player_filter = st.sidebar.multiselect(
    "Filter by Player",
    options=player_options
)

# ---- Position Filter ----
position_filter = st.multiselect(
    "Position",
    ["SP", "RP", "C", "1B", "2B", "3B", "SS", "OF", "UT"]
)

# ---- Contract Filter ----
contract_options = sorted(fantrax["Contract"].dropna().unique())
contract_filter = st.sidebar.multiselect(
    "Filter by Contract",
    options=contract_options
)

# ---- Salary Range Filter ----
min_salary = int(fantrax["Salary"].min())
max_salary = int(fantrax["Salary"].max())

salary_range = st.sidebar.slider(
    "Salary Range",
    min_value=min_salary,
    max_value=max_salary,
    value=(min_salary, max_salary)
)

# -----------------------------
# APPLY FILTERS
# -----------------------------
filtered_df = fantrax.copy()

# Apply Status
if status_filter != "All":
    filtered_df = filtered_df[
        filtered_df["Status"] == status_filter
    ]

# Apply Player
if player_filter:
    filtered_df = filtered_df[
        filtered_df["Player"].isin(player_filter)
    ]

# Apply Position
if position_filter:
    filtered_df = filtered_df[
        filtered_df["Position"].isin(position_filter)
    ]

# Apply Contract
if contract_filter:
    filtered_df = filtered_df[
        filtered_df["Contract"].isin(contract_filter)
    ]

# Apply Salary Range
filtered_df = filtered_df[
    (filtered_df["Salary"] >= salary_range[0]) &
    (filtered_df["Salary"] <= salary_range[1])
]

# -----------------------------
# DISPLAY TABLE
# -----------------------------
st.dataframe(
    filtered_df.sort_values("Net_True_Value", ascending=False),
    use_container_width=True
)
