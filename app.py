# Actuarial Valuation Dashboard (UHI Egypt)
# Law No. 2 of 2018 Compliance
# v3.5 Stable - Hybrid Cloud Auth

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pricing_engine import UHISystemConfig, ActuarialValuationEngine, generate_dummy_population
from gcp_utils import get_gcp_project, ask_gemini_actuary

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
# GLOBAL AUTH & STATE
# =============================================================================

# 0. AI Connection Detection
project_id = get_gcp_project()
is_cloud_native = project_id is not None

gemini_api_key = st.session_state.get("gemini_api_key")

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
    st.header("🔐 AI Connection")
    
    if is_cloud_native:
        st.success(f"☁️ Connected: Vertex AI (Internal)")
        st.caption(f"Project: `{project_id[:10]}...`")
        st.info("💡 Using Cloud Run Service Account")
    else:
        st.warning("🏠 Local/Standard Mode")
        api_key_input = st.text_input(
            "🔑 Gemini API Key:",
            type="password",
            value=gemini_api_key or "",
            help="Get your free API key from https://aistudio.google.com/apikey"
        )
        if api_key_input:
            st.session_state.gemini_api_key = api_key_input
            gemini_api_key = api_key_input
            st.success("✅ Direct API Active")
        else:
            st.info("💡 Paste your API key to activate AI")

    st.divider()
    st.header("⚙️ Actuarial Assumptions")
    
    # 1.5 Module H: Strategic Scenarios (Presets)
    st.subheader("🏁 Strategic Scenarios")
    scenario = st.selectbox(
        "Select Demo Scenario:",
        ["Current Baseline (Deficit)", "Balanced Sustainability (Surplus)", "High-Efficiency Growth (Elite Surplus)"],
        index=0,
        help="Choose a pre-configured scenario to see different solvency outcomes. This automatically adjusts the economic sliders below."
    )
    
    # Define Preset Values
    if scenario == "Balanced Sustainability (Surplus)":
        p_med_inf, p_wage_inf, p_inv_ret, p_admin = 8.5, 8.0, 14.0, 0.04
    elif scenario == "High-Efficiency Growth (Elite Surplus)":
        p_med_inf, p_wage_inf, p_inv_ret, p_admin = 7.0, 8.0, 15.0, 0.03
    else: # Baseline
        p_med_inf, p_wage_inf, p_inv_ret, p_admin = 12.0, 7.0, 12.0, 0.04

    # 2. Sales Tool: Crisis Mode
    if "crisis_mode" not in st.session_state:
        st.session_state.crisis_mode = False
        
    crisis_trigger = st.button("🔴 Simulate Crisis Scenario", width="stretch", type="secondary" if not st.session_state.crisis_mode else "primary", help="Simulate an extreme economic shock with high inflation and low returns to test Article 40 resilience.")
    if crisis_trigger:
        st.session_state.crisis_mode = not st.session_state.crisis_mode
    
    if st.session_state.crisis_mode:
        st.warning("🚨 DEMO: Crisis Mode Active")
        med_inflation = 0.18  # 18%
        wage_inflation = 0.05  # 5%
        inv_return = 0.04      # 4%
        admin_expense_input = 0.07 # 7%
    else:
        st.subheader("📈 2.2 Economic Factors")
        med_inflation = st.slider("Medical Inflation (%)", 5.0, 25.0, p_med_inf, key="med_inf_slider", help="Annual growth rate of medical claims costs.", on_change=lambda: log_change(f"Updated Medical Inflation to {st.session_state.med_inf_slider}%")) / 100
        wage_inflation = st.slider("Wage Inflation (%)", 3.0, 15.0, p_wage_inf, key="wage_inf_slider", help="Annual growth rate of payroll wages (revenue base).", on_change=lambda: log_change(f"Updated Wage Inflation to {st.session_state.wage_inf_slider}%")) / 100
        inv_return = st.slider("Investment Return (%)", 5.0, 20.0, p_inv_ret, key="inv_ret_slider", help="Expected annual yield on technical reserves.", on_change=lambda: log_change(f"Updated Investment Return to {st.session_state.inv_ret_slider}%")) / 100
        admin_expense_input = p_admin
    
    st.subheader("👥 Demographics")
    pop_size = st.number_input("Population Size (Sample)", 100, 100000, 1000)
    non_capable_pct = st.slider("% Non-capable (State Supported)", 0, 50, 20) / 100
    
    st.subheader("🗓️ Valuation Cycle")
    projection_years = st.slider("Projection Horizon (Years)", 5, 50, 20)
    
    st.markdown("---")
    with st.sidebar.expander("📥 3. Download Demo Data (Governorates)"):
        st.caption("Generate and download sample datasets for different regions:")
        
        # Function to create CSV in memory
        from io import BytesIO
        def get_csv_bytes(elite=False):
            df = generate_dummy_population(1000, elite_mode=elite)
            return df.to_csv(index=False).encode('utf-8')

        st.download_button(
            "🚢 Port Said Model (High Risk)", 
            get_csv_bytes(False), 
            "port_said_baseline.csv", 
            "text/csv", 
            width="stretch",
            help="High-risk regional profile with standard revenue base."
        )
        
        st.download_button(
            "🏢 Cairo Elite Model (Positive)", 
            get_csv_bytes(True), 
            "cairo_elite_sufficient.csv", 
            "text/csv", 
            width="stretch",
            help="High-value regional profile with robust revenues and sustainable surplus."
        )

    with st.expander("🛡️ 4. Immutable Audit Trail"):
        if not st.session_state.audit_log:
            st.write("No changes recorded in this session.")
            st.caption("Every adjustment to sliders or scenarios is timestamped here for regulatory transparency.")
        else:
            for log in reversed(st.session_state.audit_log):
                st.caption(f"[{log['time']}] {log['action']}")
    
    st.info("Terminologies aligned with Egypt Law 2/2018")
    
    st.divider()
    if st.button("🔄 Reset & Return to Main", width="stretch", help="Clears all data and returns to the landing page."):
        # Explicitly clear state and force rerun
        for key in ["population_df", "main_chat"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# =============================================================================
# MAIN CONTENT
# =============================================================================

# 1. Start: System Initialization Phase
if 'population_df' not in st.session_state:
    st.session_state.population_df = None

if st.session_state.population_df is None:
    st.info("🏛️ **Mission Control: Step 1 - System Initialization (v1.8 Guided)**")
    st.markdown("""
    ### 👋 Welcome, Executive Actuary.
    Follow this **3-Step Sovereign Workflow** to initialize your command center:
    
    1. **📊 Data Layer**: Upload your citizen base or use a pre-set model.
    2. **⚙️ Assumption Layer**: Adjust actuarial factors in the sidebar (Economic/Demographic).
    3. **🧠 Intelligence Layer**: Upload JSON in the sidebar to activate Strategic AI.
    """)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        uploaded_file = st.file_uploader("📤 Step 1: Upload Citizen Structure (CSV)", type="csv", help="Mandatory. Upload the demographic dataset to trigger analytical tasks.")
    with col2:
        st.caption("Strategic Simulation")
        if st.button("🚀 Step 1 (Alt): Initialize Elite Model", width="stretch", help="Fast-track to a positive, sufficient state demonstration using our pre-calibrated Elite Governorate model."):
            from pricing_engine import generate_dummy_population
            st.session_state.population_df = generate_dummy_population(1000, elite_mode=True)
            st.success("✅ Elite 'Model Governorate' Data Initialized.")
            st.rerun()
            
    if uploaded_file:
        st.session_state.population_df = pd.read_csv(uploaded_file)
        st.success("✅ Population Data Locked! Initializing Sovereign Analysis...")
        st.rerun()
    
    st.divider()
    st.caption("Status: System Offline | Enterprise Version 3.1 Stable")
    st.stop()

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

# 3.5 Scenario Goal & Status Indicator
status_color = "#28a745" if last_year['Reserve_Fund'] > 0 else "#dc3545"
st.markdown(f"""
<div style="background-color: {status_color}; color: white; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 20px;">
    <strong>Strategic Objective:</strong> {'✅ SUSTAINABLE SURPLUS - Article 40 Compliant' if last_year['Reserve_Fund'] > 0 else '⚠️ CRITICAL DEFICIT - Article 40 Guarantee Triggered'}
</div>
""", unsafe_allow_html=True)

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
    # Unlock if EITHER cloud native OR has API key
    if not is_cloud_native and not gemini_api_key:
        st.warning("🔒 **Phase 2: Strategic Intelligence Locked**")
        st.info("""
        To activate AI reasoning, either:
        1. **Deploy to Cloud Run** (Enabled automatically via Service Account)
        2. **Paste Gemini API Key** in the sidebar.
        """)
    else:
        status_text = "🤖 Strategic Insight: Active (Vertex AI)" if is_cloud_native else "🤖 Strategic Insight: Active (Gemini API)"
        st.success(f"**{status_text}**")
        
        agent_choice = st.radio(
            "Select Specialist Agent:",
            ["Senior Actuary", "Legislative Architect"],
            index=0,
            horizontal=True,
            help="Switch between numerical solvency analysis and legislative/legal strategy."
        )
        
        placeholder = "e.g., 'Analyze solvency for 50 years'" if agent_choice == "Senior Actuary" else "e.g., 'Recommend Law 2/2018 amendments to fix this deficit'"
        chat_input = st.text_input(f"Consult with {agent_choice} (Type query and press Enter):", 
                                  placeholder=placeholder,
                                  key="main_chat")
        
        if chat_input:
            with st.spinner(f"🤖 Consulting {agent_choice}..."):
                from gcp_utils import ask_gemini_actuary
                
                data_summary = f"- Scenario: {scenario}\n- Final Reserve: {last_year['Reserve_Fund']/1e6:.1f}M\n- Medical Inf: {med_inflation:.1%}\n- Solvency Status: {'Solvent' if last_year['Reserve_Fund'] > 0 else 'Deficit'}"
                # Pass API key (could be None if is_cloud_native)
                ai_response = ask_gemini_actuary(chat_input, data_summary, agent_choice, gemini_api_key)
                st.markdown(f"**🤖 {agent_choice} Analysis:**\n\n{ai_response}")
                log_change(f"Oversight Consultation ({agent_choice}): {chat_input}")

with tab_agents:
    st.subheader("🤖 Agentic Oversight Team (CrewAI Pattern)")
    st.markdown("""
    This autonomous team provides **Secondary Verification** of the actuarial results. 
    Each agent uses a specialized persona to stress-test the simulation data against separate criteria.
    """)
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
    st.plotly_chart(fig, width="stretch")

with tab2:
    st.subheader("Revenue vs Cost Delta")
    df_proj['Net_Position'] = df_proj['Total_Revenue'] - df_proj['Total_Expenditure']
    fig = px.bar(df_proj, x='Year', y='Net_Position', 
                 color='Net_Position', 
                 color_continuous_scale=['red', 'green'],
                 title="Annual Surplus/Deficit (Before Investment Income)")
    st.plotly_chart(fig, width="stretch")

with tab3:
    st.subheader("Reserve Fund Accumulation")
    fig = px.area(df_proj, x='Year', y='Reserve_Fund', 
                  title="Accumulated Technical Reserves",
                  color_discrete_sequence=['#2ca02c'])
    # Thick Red Zero-Line for Danger Zone emphasis
    fig.add_hline(y=0, line_dash="solid", line_color="red", line_width=3)
    st.plotly_chart(fig, width="stretch")

    # Module B: Stochastic Fan Chart
    st.markdown("---")
    st.subheader("🎲 4. Solvency Risk Analysis (1,000 Scenarios)")
    if st.button("Run Monte Carlo Stress Test", help="Simulates 1,000 futures with random inflation/investment fluctuations to find the failure probability."):
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
            st.plotly_chart(fig_mc, width="stretch")
            
            st.metric("Probability of Insolvency", f"{mc['prob_insolvency']:.1f}%", 
                      delta=f"Risk: {mc['prob_insolvency']:.1f}%", delta_color="inverse")

# 5. Data Preview
with st.expander("👁️ View Projection Data Table"):
    # Display all columns except the raw Risk_Flags object to avoid formatting errors
    display_df = df_proj.drop(columns=['Risk_Flags'])
    st.dataframe(display_df.style.format("{:,.0f}"), width="stretch")

st.markdown("---")
st.caption("Legal Disclaimer: This model is for actuarial simulation based on the parameters of Law 2/2018. Investment income is assumed to be compounded annually.")
