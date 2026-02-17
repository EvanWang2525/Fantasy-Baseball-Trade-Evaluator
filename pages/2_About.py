import streamlit as st

st.title("ℹ️ About This Tool")

st.markdown("""
## Dynasty Trade Evaluator

This tool evaluates trades using:

- Net Present Value of projected fantasy production
- Salary surplus modeling
- Contract control adjustments
- Dynasty value integration

### How to Use

1. Select your team and trade partner.
2. Choose players to send and receive.
3. Review trade verdict.
4. Use the recommendation engine to find fair swaps.
5. Adjust model assumptions in the sidebar.

### Interpretation

- Strong edge: >5% value difference
- Slight edge: ≤5% difference
""")
