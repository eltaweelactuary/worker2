# Actuarial Valuation Dashboard (UHI Egypt)
# Law No. 2 of 2018 Compliance

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
# SIDEBAR - ACTUARIAL ASSUMPTIONS
# =============================================================================

with st.sidebar:
    # GCP Authentication Status
    credentials = get_gcp_credentials()
    if credentials:
        st.sidebar.success("✅ GCP Cloud Authenticated")
    else:
        st.sidebar.info("💡 Running in Local/Public Mode")
        with st.sidebar.expander("🔍 GCP Diagnostic Tool"):
            from gcp_utils import get_gcp_diagnostics
            diag = get_gcp_diagnostics()
            st.write(f"**Status:** {diag['status']}")
            for check in diag.get('checks', []):
                st.write(f"- {check}")
            st.caption("Common fix: Ensure the key is pasted exactly inside triple quotes \"\"\" in Secrets.")

    st.header("⚙️ Actuarial Assumptions")
    
    st.subheader("📈 Economic Factors")
    med_inflation = st.slider("Medical Inflation (%)", 5.0, 25.0, 12.0) / 100
    wage_inflation = st.slider("Wage Inflation (%)", 3.0, 15.0, 7.0) / 100
    inv_return = st.slider("Investment Return (%)", 5.0, 20.0, 12.0) / 100
    
    st.subheader("👥 Demographics")
    pop_size = st.number_input("Population Size (Sample)", 100, 100000, 1000)
    non_capable_pct = st.slider("% Non-capable (State Supported)", 0, 50, 20) / 100
    
    st.subheader("🗓️ Valuation Cycle")
    projection_years = st.slider("Projection Horizon (Years)", 5, 50, 20)
    
    st.markdown("---")
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
    investment_return_rate=inv_return
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
    st.metric("Solvency Status", "Solvent" if last_year['Reserve_Fund'] > 0 else "Deficit", delta_color="normal")
with col4:
    # Enhancement: Turn red if > 0
    subsidy = last_year['Required_State_Subsidy']
    st.metric("Required State Subsidy", f"{subsidy/1e6:.1f}M", delta=f"{subsidy/1e6:.1f}M" if subsidy > 0 else None, delta_color="inverse")
    if subsidy > 0:
        st.warning(f"🚨 Article 48 Triggered: {subsidy/1e6:.1f}M deficit predicted.")

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
    fig.add_hline(y=0, line_dash="solid", line_color="black")
    st.plotly_chart(fig, use_container_width=True)

# 5. Data Preview
with st.expander("👁️ View Projection Data Table"):
    st.dataframe(df_proj.style.format("{:,.0f}"), use_container_width=True)

st.markdown("---")
st.caption("Legal Disclaimer: This model is for actuarial simulation based on the parameters of Law 2/2018. Investment income is assumed to be compounded annually.")
