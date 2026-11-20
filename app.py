import json
import math
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ==============================================================================
# CAREER VENTURE LAB - STAGE 1 DETERMINISTIC ENGINE & STREAMLIT SIMULATOR
# Team: team 3 | Course: Precalculus | Pathway: NUR-2 | Level: Advanced
# Business: Nurse-led Health Education Simulation (Fictional Nonclinical Education)
# ==============================================================================

st.set_page_config(
    page_title="Career Venture Lab | NUR-2 (team 3)",
    page_icon="🩺",
    layout="wide"
)

def to_money(val) -> Decimal:
    return Decimal(str(val)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def default_state():
    return {
        "team_id": "team 3",
        "course": "Precalculus",
        "pathway_id": "NUR-2",
        "selected_level": "Advanced",
        "teacher_approved_skills": [
            "Rational Average Cost Functions",
            "Function Composition & Piecewise Profit",
            "Sinusoidal Seasonal Demand Modeling"
        ],
        "snapshot_id": "SNAP-NUR2-V1",
        "state_version": 1,
        "simulation_date": "2027-01-01",
        "base_period": "Monthly",
        "working_days": 20,
        "currency": "USD",
        "offerings": [
            {
                "offering_id": "OFF-NUR-01",
                "name": "General wellness education workshop",
                "unit": "workshop seat",
                "price": 25.00,
                "demand_rule": "D0=80 at p0=$25; q(p)=max(0, 160 - 3.2p)",
                "capacity_rule": "min(requested, floor(staff_hours / hours_per_unit), venue_seats)"
            }
        ],
        "funding": [
            {"item": "Owner Contribution", "amount": 6000.00, "type": "Equity"},
            {"item": "Equipment Assets (Demonstration & Accessibility)", "amount": 1500.00, "type": "Capital Asset"},
            {"item": "Pre-Opening Setup Expense", "amount": 500.00, "type": "Pre-Opening Expense"},
            {"item": "Post-Startup Opening Cash", "amount": 4000.00, "type": "Cash Reserve"}
        ],
        "params": {
            "base_price": 25.00,
            "D0": 80,
            "staff_hours": 30.0,
            "hours_per_unit": 0.5,
            "opening_cash": 4000.00,
            "current_cash": 4000.00,
            "venue_seats": 60,
            "no_show_rate": 0.0,
            "satisfaction_mean": 4.0,
            "refund_amount": 0.0,
            "loan_principal": 0.0,
            "interest": 0.0,
            "additional_capex": 0.0,
            "new_owner_cash": 0.0,
            "loan_cash": 0.0
        },
        "variable_cost_lines": {
            "educator_delivery": 2.00,
            "materials": 2.00,
            "cleaning_consumables": 1.00
        },
        "fixed_cost_lines": {
            "venue": 250.00,
            "scheduling_software": 100.00,
            "accessibility_support": 200.00,
            "admin_insurance_assumption": 150.00
        },
        "ledger": [],
        "executed_run_ids": [],
        "recommendations": [],
        "decisions": []
    }

if "sim_state" not in st.session_state:
    st.session_state.sim_state = default_state()

state = st.session_state.sim_state

# ==============================================================================
# DETERMINISTIC NUR ENGINE FUNCTIONS
# ==============================================================================

def compute_nur_month(
    requested: int,
    price: float,
    staff_hours: float,
    hours_per_unit: float,
    venue_seats: int,
    no_show_rate: float,
    var_per_unit: float,
    fixed_monthly: float,
    ad_cost: float = 0.0,
    opening_cash: float = 4000.0,
    capacity_override: int | None = None,
    refund_amount: float = 0.0,
    interest: float = 0.0,
    principal: float = 0.0,
    additional_capex: float = 0.0,
    new_owner_cash: float = 0.0,
    loan_cash: float = 0.0
) -> dict:
    """
    Deterministic NUR-2 monthly calculation engine (Student Handbook pages 83-85).
    Separates Normal Mode (capacity derived from staff_hours & venue_seats)
    from Fixture-Test Mode (explicit capacity_override).
    """
    if capacity_override is not None:
        raw_capacity = int(capacity_override)
        mode_used = "Fixture-Test Mode (capacity_override)"
    else:
        staff_cap = math.floor(staff_hours / hours_per_unit) if hours_per_unit > 0 else 0
        raw_capacity = min(staff_cap, int(venue_seats))
        mode_used = "Normal Mode (resource-derived)"

    booked = min(int(requested), raw_capacity)
    attended = math.floor(booked * (1.0 - float(no_show_rate)))
    sold = int(attended)
    unserved_demand = max(0, int(requested) - booked)
    no_shows = max(0, booked - attended)

    d_price = to_money(price)
    d_var_unit = to_money(var_per_unit)
    d_fixed = to_money(fixed_monthly)
    d_ad = to_money(ad_cost)
    d_refund = to_money(refund_amount)
    d_interest = to_money(interest)
    d_principal = to_money(principal)
    d_capex = to_money(additional_capex)
    d_new_owner = to_money(new_owner_cash)
    d_loan_cash = to_money(loan_cash)
    d_open_cash = to_money(opening_cash)

    gross_revenue = (d_price * Decimal(sold)).quantize(Decimal("0.01"))
    net_revenue = (gross_revenue - d_refund).quantize(Decimal("0.01"))
    variable_expense = (d_var_unit * Decimal(sold)).quantize(Decimal("0.01"))
    total_operating_expense = (variable_expense + d_fixed + d_ad).quantize(Decimal("0.01"))
    operating_profit = (net_revenue - total_operating_expense).quantize(Decimal("0.01"))
    net_profit = (operating_profit - d_interest).quantize(Decimal("0.01"))

    closing_cash = (
        d_open_cash
        + net_revenue
        - variable_expense
        - d_fixed
        - d_ad
        - d_interest
        - d_principal
        - d_capex
        + d_new_owner
        + d_loan_cash
    ).quantize(Decimal("0.01"))

    return {
        "mode": mode_used,
        "requested": int(requested),
        "capacity": int(raw_capacity),
        "booked": int(booked),
        "no_shows": int(no_shows),
        "attended": int(attended),
        "sold": int(sold),
        "unserved_demand": int(unserved_demand),
        "gross_revenue": float(gross_revenue),
        "net_revenue": float(net_revenue),
        "variable_expense": float(variable_expense),
        "fixed_expense": float(d_fixed),
        "ad_cost": float(d_ad),
        "total_expense": float(total_operating_expense),
        "operating_profit": float(operating_profit),
        "net_profit": float(net_profit),
        "opening_cash": float(d_open_cash),
        "closing_cash": float(closing_cash)
    }

def run_fixture_suite(reset_first: bool = True) -> pd.DataFrame:
    """
    Replays the exact NUR monthly_fixture.csv (Handbook page 85):
    2027-01: requested=80, capacity_override=60, ad_cost=0 -> Sold 60, Rev $1,500, Exp $1,000, Profit $500, Cash $4,500
    2027-02: requested=88, capacity_override=60, ad_cost=100 -> Sold 60, Rev $1,500, Exp $1,100, Profit $400, Cash $4,900
    2027-03: requested=72, capacity_override=45, ad_cost=0 -> Sold 45, Rev $1,125, Exp $925, Profit $200, Cash $5,100
    """
    fixture_rows = [
        {"run_id": "FIX-NUR-2027-01", "month": "2027-01", "requested": 80, "capacity_override": 60, "ad_cost": 0.0},
        {"run_id": "FIX-NUR-2027-02", "month": "2027-02", "requested": 88, "capacity_override": 60, "ad_cost": 100.0},
        {"run_id": "FIX-NUR-2027-03", "month": "2027-03", "requested": 72, "capacity_override": 45, "ad_cost": 0.0},
    ]
    if reset_first:
        state["params"]["current_cash"] = 4000.00
        state["ledger"] = []
        state["executed_run_ids"] = []

    var_unit = sum(state["variable_cost_lines"].values())
    fixed_mo = sum(state["fixed_cost_lines"].values())
    price = state["params"]["base_price"]

    results = []
    for row in fixture_rows:
        if row["run_id"] in state["executed_run_ids"]:
            continue
        res = compute_nur_month(
            requested=row["requested"],
            price=price,
            staff_hours=state["params"]["staff_hours"],
            hours_per_unit=state["params"]["hours_per_unit"],
            venue_seats=state["params"]["venue_seats"],
            no_show_rate=0.0,
            var_per_unit=var_unit,
            fixed_monthly=fixed_mo,
            ad_cost=row["ad_cost"],
            opening_cash=state["params"]["current_cash"],
            capacity_override=row["capacity_override"]
        )
        state["params"]["current_cash"] = res["closing_cash"]
        state["executed_run_ids"].append(row["run_id"])
        state["state_version"] += 1
        state["ledger"].append({
            "transaction_id": f"TX-{row['run_id']}",
            "date": f"{row['month']}-28",
            "event_type": "Fixture Monthly Run",
            "category": "Workshop Operations",
            "amount": res["operating_profit"],
            "revenue": res["net_revenue"],
            "expense": res["total_expense"],
            "closing_cash": res["closing_cash"],
            "quantity": res["sold"],
            "unit_price": price,
            "offering_id": "OFF-NUR-01",
            "campaign_id": f"CAMP-{row['month']}" if row["ad_cost"] > 0 else None,
            "financing_type": "Operating",
            "state_version": state["state_version"]
        })
        res["month"] = row["month"]
        res["run_id"] = row["run_id"]
        results.append(res)
    return pd.DataFrame(results)

# ==============================================================================
# SIDEBAR: PERSISTENT IDENTITY, SAVE/LOAD JSON & STAGE STATUS
# ==============================================================================

with st.sidebar:
    st.title("🩺 Career Venture Lab")
    st.caption("Fictional Nurse-Led Health Education Simulation")
    st.markdown(f"**Team ID:** `{state['team_id']}`")
    st.markdown(f"**Course:** `{state['course']}` | **Pathway:** `{state['pathway_id']}`")
    st.markdown(f"**Approved Level:** `{state['selected_level']}`")
    st.markdown(f"**Snapshot:** `{state['snapshot_id']}` (v{state['state_version']})")

    st.divider()
    st.subheader("💾 Durable Save / Load JSON")
    snapshot_json = json.dumps(state, indent=2)
    st.download_button(
        label="Export Snapshot JSON",
        data=snapshot_json,
        file_name=f"team3_nur2_v{state['state_version']}.json",
        mime="application/json"
    )

    uploaded_json = st.file_uploader("Restore Saved Snapshot JSON", type=["json"])
    if uploaded_json is not None:
        try:
            loaded = json.load(uploaded_json)
            if loaded.get("team_id") != state["team_id"]:
                st.error(f"Rejected import: expected team_id '{state['team_id']}', got '{loaded.get('team_id')}'.")
            elif loaded.get("state_version", 0) < state["state_version"]:
                st.error(f"Rejected stale state_version v{loaded.get('state_version')} (current is v{state['state_version']}).")
            else:
                st.session_state.sim_state = loaded
                st.success(f"Restored snapshot {loaded.get('snapshot_id')} (v{loaded.get('state_version')}).")
                st.rerun()
        except Exception as exc:
            st.error(f"Invalid JSON file: {exc}")

    st.divider()
    st.subheader("📋 Build Stage Status")
    st.success("Stage 1: Inputs, Precalculus Math, Ledger, Save/Load & Fixture Tests — ACTIVE")
    st.info("Stage 2: Full Report Center, AI Recommendations Import & Marketing Studio — NOT YET IMPLEMENTED")
    st.info("Stage 3: Snapshot Assessment Generator & Cross-Course Panel — NOT YET IMPLEMENTED")
    st.info("Stage 4 (Optional): Demonstration Storefront — NOT YET IMPLEMENTED")

# ==============================================================================
# MAIN NAVIGATION TABS (STAGE 1 MODULES)
# ==============================================================================

st.title("Nurse-Led Health Education Simulation (`NUR-2`)")
st.caption("⚠️ Simulation only: fictional nonclinical health education workshops. No diagnosis, treatment, or real patient data.")

tabs = st.tabs([
    "1. Overview & Math Skills Panel",
    "2. Inputs & Funding",
    "3. Operations & Capacity",
    "4. Finance & Dated Ledger",
    "5. Stage 1 Acceptance & Fixture Tests"
])

# ------------------------------------------------------------------------------
# TAB 1: OVERVIEW & PERSISTENT PRECALCULUS MATH SKILLS PANEL
# ------------------------------------------------------------------------------
with tabs[0]:
    var_total = sum(state["variable_cost_lines"].values())
    fixed_total = sum(state["fixed_cost_lines"].values())
    normal_cap = min(
        math.floor(state["params"]["staff_hours"] / state["params"]["hours_per_unit"]),
        state["params"]["venue_seats"]
    )
    baseline_preview = compute_nur_month(
        requested=state["params"]["D0"],
        price=state["params"]["base_price"],
        staff_hours=state["params"]["staff_hours"],
        hours_per_unit=state["params"]["hours_per_unit"],
        venue_seats=state["params"]["venue_seats"],
        no_show_rate=state["params"]["no_show_rate"],
        var_per_unit=var_total,
        fixed_monthly=fixed_total,
        opening_cash=state["params"]["current_cash"]
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Spendable Cash on Hand", f"${state['params']['current_cash']:,.2f}")
    c2.metric("Normal Monthly Capacity", f"{normal_cap} seats")
    c3.metric("Baseline Monthly Operating Profit", f"${baseline_preview['operating_profit']:,.2f}")
    c4.metric("Ledger Transactions Recorded", len(state["ledger"]))

    st.divider()
    st.subheader("📐 Persistent Math Skills & Challenge Level Panel (Precalculus)")
    col_ctrl1, col_ctrl2 = st.columns([1, 2])
    with col_ctrl1:
        selected_mode = st.selectbox(
            "Select Precalculus Skill Mode",
            ["Foundation", "Applied", "Advanced"],
            index=["Foundation", "Applied", "Advanced"].index(state["selected_level"])
        )
        if selected_mode != state["selected_level"]:
            state["selected_level"] = selected_mode
            state["state_version"] += 1

        st.markdown(f"""
        - **Course:** Precalculus (`NUR-2`)
        - **Active Mode:** `{selected_mode}` (Teacher-Approved: `Advanced`)
        - **Fixed Cost ($F$):** `${fixed_total:,.2f}/month`
        - **Variable Cost ($v$):** `${var_total:,.2f}/seat`
        - **Base Price ($p_0$):** `${state['params']['base_price']:,.2f}/seat`
        - **Base Demand ($D_0$):** `{state['params']['D0']} seats/month`
        - **Capacity ($C_{{max}}$):** `{normal_cap} seats/month`
        """)

    with col_ctrl2:
        p0 = state["params"]["base_price"]
        D0 = state["params"]["D0"]

        if selected_mode == "Foundation":
            st.markdown("### Foundation: Average Cost Rational Function $A(s) = \frac{F}{s} + v$")
            st.info(f"**Domain:** $0 < s \le {normal_cap}$ seats | **Vertical Asymptote:** $s = 0$ ($A(0)$ is undefined) | **Horizontal Asymptote:** $y = {var_total:.2f}$")
            s_vals = np.linspace(1, max(normal_cap, 1), 100)
            a_vals = fixed_total / s_vals + var_total
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=s_vals, y=a_vals, mode="lines", name="Average Cost A(s) ($/seat)"))
            fig.add_hline(y=var_total, line_dash="dash", annotation_text=f"Horizontal Asymptote y = ${var_total:.2f}")
            fig.add_vline(x=normal_cap, line_dash="dot", annotation_text=f"Capacity Limit s = {normal_cap}")
            fig.update_layout(title="Average Cost per Workshop Seat A(s)", xaxis_title="Completed Seats (s)", yaxis_title="Average Cost ($/seat)")
            st.plotly_chart(fig, use_container_width=True)
            st.write(f"**Acceptance Check:** At $s = 0$, $A(0)$ is **undefined**. At full capacity $s = {normal_cap}$, $A({normal_cap}) = \frac{{{fixed_total:.0f}}}{{{normal_cap}}} + {var_total:.2f} = \mathbf{{\${fixed_total/normal_cap + var_total:.2f}/seat}}$.")

        elif selected_mode == "Applied":
            st.markdown("### Applied: Function Composition & Piecewise Constrained Profit")
            breakpoint_p = p0 * (2.0 - normal_cap / D0) if D0 > 0 else p0
            st.info(f"**Demand:** $q(p) = \max(0, {2*D0:.0f} - {D0/p0:.2f}p)$ | **Completed:** $s(p) = \min({normal_cap}, q(p))$ | **Capacity Breakpoint:** $p = \${breakpoint_p:.2f}$ on $0 \le p \le \${2*p0:.2f}$")
            p_vals = np.linspace(0, 2 * p0, 200)
            q_vals = np.maximum(0, 2 * D0 - (D0 / p0) * p_vals)
            s_vals = np.minimum(normal_cap, q_vals)
            r_vals = p_vals * s_vals
            c_vals = fixed_total + var_total * s_vals
            prof_vals = r_vals - c_vals

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=p_vals, y=r_vals, mode="lines", name="Revenue R(p)"))
            fig.add_trace(go.Scatter(x=p_vals, y=c_vals, mode="lines", name="Total Cost C(s(p))"))
            fig.add_trace(go.Scatter(x=p_vals, y=prof_vals, mode="lines", name="Profit P(p) = R - C"))
            fig.add_hline(y=0, line_dash="dash", annotation_text="Zero Profit Line ($0)")
            fig.add_vline(x=breakpoint_p, line_dash="dot", annotation_text=f"Capacity Corner p = ${breakpoint_p:.2f}")
            fig.update_layout(title="Composed Revenue, Cost & Profit vs. Price (Continuous Model)", xaxis_title="Workshop Seat Price p ($)", yaxis_title="Monthly USD ($)")
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Note: Continuous curves show mathematical model behavior; actual ledger transactions round completed seats to whole integers.")

        else:  # Advanced
            st.markdown("### Advanced: Sinusoidal Seasonal Demand Model $D(t) = D_0\left(1 + 0.20\sin\left(\frac{2\pi(t-1)}{12}\right)\right)$")
            st.info(f"**Period:** 12 months ($t = 1\dots 12$) | **Peak ($t=4$):** $1.20 \times {D0} = {1.2*D0:.0f}$ seats | **Minimum ($t=10$):** $0.80 \times {D0} = {0.8*D0:.0f}$ seats | **Capacity Cap:** {normal_cap} seats")
            t_vals = np.arange(1, 13)
            seasonal_demand = D0 * (1.0 + 0.20 * np.sin(2 * np.pi * (t_vals - 1) / 12.0))
            realized_sales = np.minimum(normal_cap, np.floor(seasonal_demand))

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=t_vals, y=seasonal_demand, mode="lines+markers", name="Assumed Seasonal Demand D(t)"))
            fig.add_trace(go.Bar(x=t_vals, y=realized_sales, name="Realized Sales (Clipped at Capacity)", opacity=0.65))
            fig.add_hline(y=normal_cap, line_dash="dash", annotation_text=f"Capacity Ceiling ({normal_cap} seats)")
            fig.update_layout(title="12-Month Assumed Seasonal Demand vs. Capacity-Clipped Sales", xaxis_title="Month Index (t)", yaxis_title="Workshop Seats")
            st.plotly_chart(fig, use_container_width=True)

            df_season = pd.DataFrame({
                "Month (t)": t_vals,
                "Assumed Demand D(t)": np.round(seasonal_demand, 2),
                "Capacity Limit": normal_cap,
                "Realized Sales (Integer)": realized_sales.astype(int),
                "Unserved Demand": np.maximum(0, np.floor(seasonal_demand) - realized_sales).astype(int)
            })
            st.dataframe(df_season, use_container_width=True, hide_index=True)

# ------------------------------------------------------------------------------
# TAB 2: INPUTS & FUNDING
# ------------------------------------------------------------------------------
with tabs[1]:
    st.subheader("Startup Funding Mix & Opening Balances (Fictional Teaching Defaults)")
    st.dataframe(pd.DataFrame(state["funding"]), use_container_width=True, hide_index=True)
    st.caption("Accounting Rule: Owner contribution ($6,000) funds Equipment ($1,500), Pre-Opening Expense ($500), and Opening Cash ($4,000). Equipment is not expensed again.")

    st.divider()
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        st.subheader("Pricing, Demand & Operating Parameters")
        state["params"]["base_price"] = st.number_input("Workshop Seat Price ($)", min_value=1.0, value=float(state["params"]["base_price"]), step=1.0)
        state["params"]["D0"] = st.number_input("Baseline Monthly Requested Seats (D0)", min_value=0, value=int(state["params"]["D0"]), step=5)
        state["params"]["staff_hours"] = st.number_input("Nurse Educator Hours / Month", min_value=0.0, value=float(state["params"]["staff_hours"]), step=1.0)
        state["params"]["hours_per_unit"] = st.number_input("Educator Hours per Seat", min_value=0.1, value=float(state["params"]["hours_per_unit"]), step=0.1)
        state["params"]["venue_seats"] = st.number_input("Venue Seat Cap / Month", min_value=0, value=int(state["params"]["venue_seats"]), step=5)
        state["params"]["no_show_rate"] = st.slider("No-Show Rate (0.00 to 1.00)", min_value=0.0, max_value=1.0, value=float(state["params"]["no_show_rate"]), step=0.05)

    with col_in2:
        st.subheader("Editable Variable & Fixed Cost Lines")
        for k in list(state["variable_cost_lines"].keys()):
            state["variable_cost_lines"][k] = st.number_input(f"Variable: {k} ($/seat)", min_value=0.0, value=float(state["variable_cost_lines"][k]), step=0.5)
        st.write(f"**Total Variable Cost per Attended Seat:** `${sum(state['variable_cost_lines'].values()):,.2f}`")

        st.divider()
        for k in list(state["fixed_cost_lines"].keys()):
            state["fixed_cost_lines"][k] = st.number_input(f"Fixed: {k} ($/month)", min_value=0.0, value=float(state["fixed_cost_lines"][k]), step=10.0)
        st.write(f"**Total Monthly Fixed Expense:** `${sum(state['fixed_cost_lines'].values()):,.2f}`")

# ------------------------------------------------------------------------------
# TAB 3: OPERATIONS & CAPACITY
# ------------------------------------------------------------------------------
with tabs[2]:
    st.subheader("Operations: Educator Time, Venue Capacity & Attendance")
    staff_cap = math.floor(state["params"]["staff_hours"] / state["params"]["hours_per_unit"]) if state["params"]["hours_per_unit"] > 0 else 0
    venue_cap = state["params"]["venue_seats"]
    total_cap = min(staff_cap, venue_cap)

    st.markdown(f"""
    - **Educator Hour Capacity:** `floor({state['params']['staff_hours']} / {state['params']['hours_per_unit']})` = **{staff_cap} seats**
    - **Venue Seat Limit:** **{venue_cap} seats**
    - **Effective Normal Capacity:** `min({staff_cap}, {venue_cap})` = **{total_cap} seats/month**
    """)

    test_req = st.number_input("Preview Requested Seats for Scenario Check", min_value=0, value=int(state["params"]["D0"]), step=5)
    preview_ops = compute_nur_month(
        requested=test_req,
        price=state["params"]["base_price"],
        staff_hours=state["params"]["staff_hours"],
        hours_per_unit=state["params"]["hours_per_unit"],
        venue_seats=state["params"]["venue_seats"],
        no_show_rate=state["params"]["no_show_rate"],
        var_per_unit=sum(state["variable_cost_lines"].values()),
        fixed_monthly=sum(state["fixed_cost_lines"].values()),
        opening_cash=state["params"]["current_cash"]
    )
    oc1, oc2, oc3, oc4 = st.columns(4)
    oc1.metric("Booked Seats", preview_ops["booked"])
    oc2.metric("No-Shows", preview_ops["no_shows"])
    oc3.metric("Attended / Sold", preview_ops["sold"])
    oc4.metric("Unserved Demand", preview_ops["unserved_demand"])

# ------------------------------------------------------------------------------
# TAB 4: FINANCE & DATED LEDGER
# ------------------------------------------------------------------------------
with tabs[3]:
    st.subheader("Finance: Profit vs. Cash & Single Dated Ledger")
    st.write("Separates actual operating profit from spendable cash. Reopening reports never duplicates transactions.")
    if state["ledger"]:
        st.dataframe(pd.DataFrame(state["ledger"]), use_container_width=True, hide_index=True)
    else:
        st.info("No ledger transactions recorded yet. Run the Stage 1 Fixture Suite in Tab 5 or record an approved round.")

# ------------------------------------------------------------------------------
# TAB 5: STAGE 1 ACCEPTANCE & FIXTURE TESTS
# ------------------------------------------------------------------------------
with tabs[4]:
    st.subheader("🧪 Stage 1 Automated Acceptance & Fixture Verification")
    st.warning("⚠️ FIXTURE-TEST MODE: Replaying monthly_fixture.csv uses explicit capacity_override values (60, 60, 45) to verify ledger math.")

    if st.button("Reset to Post-Startup Opening ($4,000) & Replay monthly_fixture.csv"):
        df_fix = run_fixture_suite(reset_first=True)
        st.success("Fixture replay completed and recorded in the dated ledger.")
        st.dataframe(df_fix[["month", "requested", "capacity", "sold", "net_revenue", "total_expense", "operating_profit", "closing_cash"]], use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Business-Specific & Edge-Case Verification")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("**1. No-Show Rate = 0.20 Check (Handbook p. 85)**")
        ns_res = compute_nur_month(
            requested=80, price=25.0, staff_hours=30.0, hours_per_unit=0.5,
            venue_seats=60, no_show_rate=0.20, var_per_unit=5.0, fixed_monthly=700.0, opening_cash=4000.0
        )
        st.json({
            "booked": ns_res["booked"],
            "attended_sold": ns_res["sold"],
            "revenue": ns_res["net_revenue"],
            "variable_expense": ns_res["variable_expense"],
            "operating_profit": ns_res["operating_profit"],
            "expected": "booked=60, attended=48, revenue=$1200, variable=$240, profit=$260"
        })
    with col_t2:
        st.markdown("**2. Zero-Sales Edge Check (Handbook p. 85)**")
        zs_res = compute_nur_month(
            requested=0, price=25.0, staff_hours=30.0, hours_per_unit=0.5,
            venue_seats=60, no_show_rate=0.0, var_per_unit=5.0, fixed_monthly=700.0, opening_cash=4000.0
        )
        st.json({
            "sold": zs_res["sold"],
            "revenue": zs_res["net_revenue"],
            "variable_expense": zs_res["variable_expense"],
            "operating_profit": zs_res["operating_profit"],
            "expected": "sold=0, revenue=$0, variable=$0, profit=-$700"
        })
