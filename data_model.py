import pandas as pd
import numpy as np
import streamlit as st


# -----------------------------
# LOAD RAW DATA
# -----------------------------
def load_raw_data():
    dynasty = pd.read_csv("players_dynasty_values.csv")
    fantrax = pd.read_csv("players_30T.csv")
    return dynasty, fantrax


# -----------------------------
# NPV FUNCTION
# -----------------------------
def player_npv(score, age, r, g_pre30, g_post30):

    if age >= 38:
        return 0

    if age < 30:
        n1 = 30 - age

        grow_phase = score * (
            (1 - ((1 + g_pre30)/(1 + r))**n1) / (r - g_pre30)
        )

        score_at_30 = score * (1 + g_pre30)**n1

        n2 = 38 - 30

        decline_phase = score_at_30 * (
            (1 - ((1 + g_post30)/(1 + r))**n2) / (r - g_post30)
        ) * (1 / (1 + r)**n1)

        return grow_phase + decline_phase

    else:
        n = 38 - age

        return score * (
            (1 - ((1 + g_post30)/(1 + r))**n) / (r - g_post30)
        )


# -----------------------------
# Load FINAL FANTRAX MODEL
# -----------------------------
@st.cache_data
def load_model(
    r=0.13,
    g_pre30=0.03,
    g_post30=-0.05,
    salary_weight=0.7,
    control_weight=2.0
):

    dynasty, fantrax = load_raw_data()

    # Clean dynasty
    dynasty = dynasty.rename(columns={'Name': 'Player'})
    dynasty = dynasty.drop(['Rank', 'Age', 'Positions'], axis=1)

    team_map = {'AZ':'ARI', 'CWS':'CHW', 'FA':'(N/A)'}
    dynasty['Team'] = dynasty['Team'].replace(team_map)

    # Clean fantrax
    fantrax = fantrax.drop(['RkOv', 'Opponent', '+/-'], axis=1)

    # $ per point
    excluded_statuses = [
    "FA",
    "W <small>(Wed)</small>",
    "W <small>(Tue)</small>"
    ]
    
    total_pts = (
        fantrax
        .loc[~fantrax["Status"]
        .isin(excluded_statuses)]["Score"]
        .sum()
    )
    dollars_per_pt = (265 * 30) / total_pts

    # Merge
    fantrax = fantrax.merge(dynasty, how="left", on=["Player", "Team"])

    dynasty_pts = (
        fantrax
        .loc[~fantrax["Status"]
        .isin(excluded_statuses)]["Value"]
        .sum()
    )
    dynasty_dollars_per_pt = (265 * 30) / dynasty_pts

    # Apply NPV
    fantrax["Score_NPV"] = fantrax.apply(
        lambda x: player_npv(
            x["Score"],
            x["Age"],
            r,
            g_pre30,
            g_post30
        ),
        axis=1
    )

    # Salary math
    fantrax["Fair_Salary"] = fantrax["Score_NPV"] * dollars_per_pt

    fantrax["Dynasty_Salary"] = fantrax["Value"] * dynasty_dollars_per_pt

    fantrax["Control"] = (
        (5 - pd.to_numeric(fantrax["Contract"].str[:-2])) * control_weight
    )

    fantrax["Total_Value_Old"] = (
        fantrax["Fair_Salary"]
        + fantrax["Dynasty_Salary"]
        + fantrax["Control"]
    )

    fantrax["Net_Value_Old"] = fantrax["Total_Value"] - (fantrax["Salary"] * salary_weight)

    fantrax["True_Value"] = (
        fantrax["Score"] + 
        fantrax["Dynasty_Salary"] +
        fantrax["Control"]
    )

    fantrax["Net_True_Value"] = (
        fantrax["True_Value"] - (fantrax["Salary"] * salary_weight)
    )
    
    # Unique display field
    fantrax["Player_Salary_Team"] = (
        fantrax["Player"].astype(str)
        + " | $" + fantrax["Salary"].astype(str)
        + " | " + fantrax["Status"].astype(str)
    )

    return fantrax


# =====================================================
# MODEL SETTINGS (USED ON ALL PAGES)
# =====================================================

def render_model_settings_sidebar():
    """
    Renders global model sliders.
    These persist across pages via st.session_state.
    """

    defaults = {
        "r": 0.13,
        "g_pre30": 0.03,
        "g_post30": -0.05,
        "salary_weight": 0.7,
        "control_weight": 2.0
    }

    # Initialize once
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    st.sidebar.header("Model Settings")

    st.session_state.r = st.sidebar.slider(
        "Discount Rate (r)",
        0.0, 0.25,
        st.session_state.r,
        0.01
    )

    st.session_state.g_pre30 = st.sidebar.slider(
        "Growth Rate (<30)",
        0.0, 0.15,
        st.session_state.g_pre30,
        0.01
    )

    st.session_state.g_post30 = st.sidebar.slider(
        "Decline Rate (30+)",
        -0.25, 0.05,
        st.session_state.g_post30,
        0.01
    )

    st.session_state.salary_weight = st.sidebar.slider(
        "Salary Weight",
        0.0, 1.0,
        st.session_state.salary_weight,
        0.1
    )

    st.session_state.control_weight = st.sidebar.slider(
        "Control Bonus Weight",
        0.0, 5.0,
        st.session_state.control_weight,
        0.5
    )


# =====================================================
# TRADE SETTINGS (TRADE PAGE ONLY)
# =====================================================

def render_trade_settings_sidebar():
    """
    Renders trade-specific settings.
    Only call this inside Trade_Evaluator.py.
    """

    defaults = {
        "trade_margin": 0.05,          # 5%
        "multi_player_discount": 0.15  # 12%
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    st.sidebar.header("Trade Settings")

    st.session_state.trade_margin = st.sidebar.slider(
        "Trade Margin of Error (%)",
        0.0, 0.1,
        st.session_state.trade_margin,
        0.01
    )

    st.session_state.multi_player_discount = st.sidebar.slider(
        "Multi-Player Discount (%)",
        0.0, 0.30,
        st.session_state.multi_player_discount,
        0.03
    )
