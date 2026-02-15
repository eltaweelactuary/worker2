# Actuarial Valuation Dashboard (UHI Egypt)
# Law No. 2 of 2018 Compliance
# v1.0.4 - System Sync Fix

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pricing_engine import UHISystemConfig, ActuarialValuationEngine, generate_dummy_population
from gcp_utils import get_gcp_credentials

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="UHI Actuarial Valuation",
    page_icon="🏛️",
    layout="wide"
)

st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E3A5F; text-align: center; }
    .metric-card { background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #1E3A5F; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# INITIALIZE STATE
# =============================================================================
if "audit_log" not in st.session_state:
    st.session_state.audit_log = []

def log_change(msg):
    import datetime
    st.session_state.audit_log.append({
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "action": msg
    })

# =============================================================================
# SIDEBAR - ACTUARIAL ASSUMPTIONS
# =============================================================================

with st.sidebar:
    # GCP Authentication Status
    credentials = None
    gcp_error = None
    try:
        credentials = get_gcp_credentials()
    except Exception as e:
        gcp_error = str(e)
        
    if credentials:
        st.sidebar.success("✅ GCP Cloud Authenticated")
    else:
        st.sidebar.info("💡 Running in Local/Public Mode")
        with st.sidebar.expander("🔍 GCP Diagnostic Tool"):
            from gcp_utils import get_gcp_diagnostics
            diag = get_gcp_diagnostics()
            if gcp_error:
                st.error(f"**GCP Error:** {gcp_error}")
            st.write(f"**Status:** {diag['status']}")
            for check in diag.get('checks', []):
                st.write(f"- {check}")
            st.caption("Common fix: Ensure the key is pasted exactly inside triple quotes \"\"\" in Secrets.")
        
        with st.sidebar.expander("🔑 Upload Service Account JSON"):
            uploaded_json = st.file_uploader("Drop service_account.json here", type="json")
            if uploaded_json:
                import json
                try:
                    st.session_state.uploaded_gcp_json = json.load(uploaded_json)
                    st.success("JSON Key Loaded! Restarting auth...")
                    st.rerun()
                except Exception as e:
                    st.error(f"Invalid JSON: {e}")

    st.header("⚙️ Actuarial Assumptions")
    
    # 1.5 Module H: Strategic Scenarios (Presets)
    st.subheader("🏁 Strategic Scenarios")
    scenario = st.selectbox(
        "Select Demo Scenario:",
        ["Current Baseline (Deficit)", "Balanced Sustainability (Surplus)", "High-Efficiency Growth (Elite Surplus)"],
        index=0
    )
    
    # Define Preset Values
    if scenario == "Balanced Sustainability (Surplus)":
        p_med_inf, p_wage_inf, p_inv_ret, p_admin = 9.0, 8.0, 12.0, 0.04
    elif scenario == "High-Efficiency Growth (Elite Surplus)":
        p_med_inf, p_wage_inf, p_inv_ret, p_admin = 7.0, 8.0, 15.0, 0.03
    else: # Baseline
        p_med_inf, p_wage_inf, p_inv_ret, p_admin = 12.0, 7.0, 12.0, 0.04

    # 2. Sales Tool: Crisis Mode
    if "crisis_mode" not in st.session_state:
        st.session_state.crisis_mode = False
        
    crisis_trigger = st.button("🔴 Simulate Crisis Scenario", use_container_width=True, type="secondary" if not st.session_state.crisis_mode else "primary")
    if crisis_trigger:
        st.session_state.crisis_mode = not st.session_state.crisis_mode
    
    if st.session_state.crisis_mode:
        st.warning("🚨 DEMO: Crisis Mode Active")
        med_inflation = 0.18  # 18%
        wage_inflation = 0.05  # 5%
        inv_return = 0.04      # 4%
        admin_expense_input = 0.07 # 7%
    else:
        st.subheader("📈 Economic Factors")
        med_inflation = st.slider("Medical Inflation (%)", 5.0, 25.0, p_med_inf, key="med_inf_slider", on_change=lambda: log_change(f"Updated Medical Inflation to {st.session_state.med_inf_slider}%")) / 100
        wage_inflation = st.slider("Wage Inflation (%)", 3.0, 15.0, p_wage_inf, key="wage_inf_slider", on_change=lambda: log_change(f"Updated Wage Inflation to {st.session_state.wage_inf_slider}%")) / 100
        inv_return = st.slider("Investment Return (%)", 5.0, 20.0, p_inv_ret, key="inv_ret_slider", on_change=lambda: log_change(f"Updated Investment Return to {st.session_state.inv_ret_slider}%")) / 100
        admin_expense_input = p_admin
    
    st.subheader("👥 Demographics")
    pop_size = st.number_input("Population Size (Sample)", 100, 100000, 1000)
    non_capable_pct = st.slider("% Non-capable (State Supported)", 0, 50, 20) / 100
    
    st.subheader("🗓️ Valuation Cycle")
    projection_years = st.slider("Projection Horizon (Years)", 5, 50, 20)
    
    st.markdown("---")
    with st.sidebar.expander("📥 Download Demo Data (Governorates)"):
        st.caption("Use these datasets to test the strategic scenarios:")
        
        with open("demo_port_said.csv", "rb") as f:
            st.download_button("🚢 Port Said (High Risk)", f, "port_said_baseline.csv", "text/csv", use_container_width=True)
            
        with open("demo_luxor.csv", "rb") as f:
            st.download_button("🏛️ Luxor (Balanced)", f, "luxor_balanced.csv", "text/csv", use_container_width=True)
            
        with open("demo_cairo_industrial.csv", "rb") as f:
            st.download_button("🏢 Cairo Industrial (Elite)", f, "cairo_elite.csv", "text/csv", use_container_width=True)

    with st.expander("🛡️ Immutable Audit Trail"):
        if not st.session_state.audit_log:
            st.write("No changes recorded.")
        else:
            for log in reversed(st.session_state.audit_log):
                st.caption(f"[{log['time']}] {log['action']}")
    
    st.info("Terminologies aligned with Egypt Law 2/2018")

# =============================================================================
# MAIN CONTENT
# =============================================================================

st.markdown('<h1 class="main-header">🏛️ UHI Actuarial Valuation Dashboard</h1>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Strategic multi-year solvency projection for the Universal Health Insurance Authority</p>", unsafe_allow_html=True)

# 1. Load Data
if 'population_df' not in st.session_state:
    st.session_state.population_df = generate_dummy_population(pop_size)

uploaded_file = st.file_uploader("Upload Population Structure (CSV)", type="csv")
if uploaded_file:
    st.session_state.population_df = pd.read_csv(uploaded_file)
    st.success("Custom population data loaded.")

# 2. Run Engine
config = UHISystemConfig(
    medical_inflation=med_inflation,
    wage_inflation=wage_inflation,
    investment_return_rate=inv_return,
    admin_expense_pct=admin_expense_input
)

engine = ActuarialValuationEngine(config)
df_proj = engine.project_solvency(st.session_state.population_df, years=projection_years)

# 3. High Level Metrics (Final Year)
last_year = df_proj.iloc[-1]
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Population", f"{len(st.session_state.population_df):,}")
with col2:
    st.metric(f"Reserve Fund (Year {projection_years})", f"{last_year['Reserve_Fund']/1e6:.1f}M")
with col3:
    st.metric("Solvency Status", "Solvent" if last_year['Reserve_Fund'] > 0 else "Deficit")
with col4:
    subsidy = last_year['Required_State_Subsidy']
    st.metric("Required State Subsidy", f"{subsidy/1e6:.1f}M", delta=f"{subsidy/1e6:.1f}M" if subsidy > 0 else None, delta_color="inverse")

# 4. EXECUTIVE RISK ALERT CENTER
st.markdown("### 🚨 Executive Risk Alerts")
all_flags = []
for idx, row in df_proj.iterrows():
    for flag in row['Risk_Flags']:
        flag['Year'] = row['Year']
        all_flags.append(flag)

if not all_flags:
    st.success("✅ System Stability: No critical risk thresholds exceeded.")
else:
    unique_types = {f['type']: f for f in all_flags}.values()
    cols = st.columns(len(unique_types))
    for i, flag in enumerate(unique_types):
        with cols[i % len(cols)]:
            if flag['level'] == "CRITICAL":
                st.error(f"**{flag['type']}**\n\n{flag['msg']}")
            else:
                st.warning(f"**{flag['type']}**\n\n{flag['msg']}")

# 5. STRATEGIC INTELLIGENCE HUB
st.markdown("---")
tab_ai, tab_agents, tab_xai = st.tabs(["💬 Gemini Actuary", "🤖 Agentic Oversight", "ℹ️ XAI Insights"])

with tab_ai:
    chat_input = st.text_input("Ask the AI Actuary about the current scenario:", key="main_chat")
    if chat_input:
        with st.spinner("🤖 Consulting Gemini 2.0..."):
            from gcp_utils import ask_gemini_actuary
            data_summary = f"- Scenario: {scenario}\n- Final Reserve: {last_year['Reserve_Fund']/1e6:.1f}M\n- Medical Inf: {med_inflation:.1%}"
            ai_response = ask_gemini_actuary(chat_input, data_summary)
            st.markdown(f"**🤖 Actuary Response:**\n\n{ai_response}")
            log_change(f"AI Consultation: {chat_input}")

with tab_agents:
    agent_audit = engine.perform_agentic_audit(df_proj)
    cols = st.columns(3)
    for i, audit in enumerate(agent_audit):
        with cols[i % 3]:
            st.info(f"**{audit['agent']}**\n\n*Analysis:* {audit['analysis']}")

with tab_xai:
    explanations = engine.explain_projection(df_proj)
    for exp in explanations:
        st.write(exp)
    avg_cost = df_proj['Total_Expenditure'].mean()
    st.info(engine.suggest_reinsurance(avg_cost))

# 4. Visualizations
tab1, tab2, tab3 = st.tabs(["📊 Solvency Projection", "💸 Revenue vs Cost", "🗄️ Reserve Accumulation"])

with tab1:
    st.subheader("Cash Flow Solvency (Revenue vs Expenditure)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df_proj['Year'], y=df_proj['Total_Revenue'], name='Total Revenue', line=dict(color='#1f77b4', width=3)))
    fig.add_trace(go.Scatter(x=df_proj['Year'], y=df_proj['Total_Expenditure'], name='Total Expenditure', line=dict(color='#d62728', width=3, dash='dash')))
    fig.update_layout(yaxis_title="Amount (EGP)", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Revenue vs Cost Delta")
    df_proj['Net_Position'] = df_proj['Total_Revenue'] - df_proj['Total_Expenditure']
    fig = px.bar(df_proj, x='Year', y='Net_Position', 
                 color='Net_Position', 
                 color_continuous_scale=['red', 'green'],
                 title="Annual Surplus/Deficit (Before Investment Income)")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Reserve Fund Accumulation")
    fig = px.area(df_proj, x='Year', y='Reserve_Fund', 
                  title="Accumulated Technical Reserves",
                  color_discrete_sequence=['#2ca02c'])
    # Thick Red Zero-Line for Danger Zone emphasis
    fig.add_hline(y=0, line_dash="solid", line_color="red", line_width=3)
    st.plotly_chart(fig, use_container_width=True)

    # Module B: Stochastic Fan Chart
    st.markdown("---")
    st.subheader("🎲 Solvency Risk Analysis (1,000 Scenarios)")
    if st.button("Run Monte Carlo Stress Test"):
        with st.spinner("Simulating 1,000 actuarial futures..."):
            mc = engine.run_monte_carlo_simulation(st.session_state.population_df, years=projection_years)
            
            fig_mc = go.Figure()
            # P5 to P95 Shading (Confidence Band)
            fig_mc.add_trace(go.Scatter(x=mc['years'], y=mc['p95'], mode='lines', line=dict(width=0), showlegend=False))
            fig_mc.add_trace(go.Scatter(x=mc['years'], y=mc['p5'], mode='lines', line=dict(width=0), fill='tonexty', fillcolor='rgba(44, 160, 44, 0.2)', name='90% Confidence Interval'))
            # Median
            fig_mc.add_trace(go.Scatter(x=mc['years'], y=mc['p50'], name='Median (P50)', line=dict(color='#2ca02c', width=3)))
            
            fig_mc.add_hline(y=0, line_dash="dash", line_color="red")
            fig_mc.update_layout(title="Stochastic Reserve Outlook", yaxis_title="Reserve Fund", hovermode="x unified")
            st.plotly_chart(fig_mc, use_container_width=True)
            
            st.metric("Probability of Insolvency", f"{mc['prob_insolvency']:.1f}%", 
                      delta=f"Risk: {mc['prob_insolvency']:.1f}%", delta_color="inverse")

# 5. Data Preview
with st.expander("👁️ View Projection Data Table"):
    # Display all columns except the raw Risk_Flags object to avoid formatting errors
    display_df = df_proj.drop(columns=['Risk_Flags'])
    st.dataframe(display_df.style.format("{:,.0f}"), use_container_width=True)

st.markdown("---")
st.caption("Legal Disclaimer: This model is for actuarial simulation based on the parameters of Law 2/2018. Investment income is assumed to be compounded annually.")
