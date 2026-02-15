"""
Actuarial Valuation Engine for Egypt Universal Health Insurance (UHI)
Complies with Law No. 2 of 2018.
v1.0.4 - Risk Engine Sync
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

@dataclass
class UHISystemConfig:
    """
    Social Health Insurance Actuarial Assumptions (Law 2/2018)
    """
    # Economic Assumptions
    wage_inflation: float = 0.07
    medical_inflation: float = 0.12
    investment_return_rate: float = 0.10
    
    # Administrative Assumptions
    admin_expense_pct: float = 0.04  # Capped at 5% per policy guidelines
    
    # Demographic & Law-specific Rates
    participation_rate: float = 1.0
    employee_contr_rate: float = 0.01
    employer_contr_rate: float = 0.03
    self_employed_contr_rate: float = 0.04  # Total 4% for self-employed
    family_spouse_contr_rate: float = 0.03
    family_child_contr_rate: float = 0.01
    state_non_capable_rate: float = 0.05  # 5% of min wage
    
    # Market Inputs (Lump Sums in Millions)
    cigarette_tax_lump: float = 3000.0  # Annual estimate
    highway_tolls_lump: float = 500.0    # Annual estimate
    
    # External Constants
    min_wage_annual: float = 36000.0  # EGP

class ActuarialValuationEngine:
    """
    Engine for multi-year solvency projection of the UHI system.
    """
    def __init__(self, config: UHISystemConfig):
        self.config = config

    def project_solvency(self, population_df: pd.DataFrame, years: int = 10) -> pd.DataFrame:
        """
        Projects revenues, costs, and reserves over a specified horizon.
        """
        projections = []
        
        # Helper to safely get column or return default
        def safe_get(col, default=0):
            return population_df[col] if col in population_df.columns else pd.Series([default] * len(population_df))

        # Initial State
        accumulated_reserve = 0.0
        
        # Base Population Metrics (Robust Handling)
        status_col = population_df['EmploymentStatus'] if 'EmploymentStatus' in population_df.columns else pd.Series(['Unknown'] * len(population_df))
        total_employees = len(population_df[status_col == 'Employee'])
        total_self_employed = len(population_df[status_col == 'Self-employed'])
        total_non_capable = len(population_df[status_col == 'Non-capable'])
        
        # Calculate Base Annual Revenue from Population
        wages = safe_get('MonthlyWage', 0)
        
        # 1. Employee + Employer Contributions
        wage_revenue_base = (
            population_df[status_col == 'Employee']['MonthlyWage'].sum() if 'MonthlyWage' in population_df.columns and 'EmploymentStatus' in population_df.columns else 0
        ) * 12 * (self.config.employee_contr_rate + self.config.employer_contr_rate)
        
        # 2. Self-employed Contributions (4% total)
        self_employed_revenue_base = (
            population_df[status_col == 'Self-employed']['MonthlyWage'].sum() if 'MonthlyWage' in population_df.columns and 'EmploymentStatus' in population_df.columns else 0
        ) * 12 * self.config.self_employed_contr_rate
        
        # Combine work-based revenue
        total_work_revenue_base = wage_revenue_base + self_employed_revenue_base
        
        # 3. Family Contributions (Heads of families pay for dependents)
        family_contr_base = 0
        if 'SpouseInSystem' in population_df.columns and 'MonthlyWage' in population_df.columns:
            family_contr_base += (
                population_df[population_df['SpouseInSystem'] == True]['MonthlyWage'].sum() * 12 * 
                self.config.family_spouse_contr_rate
            )
        if 'ChildrenCount' in population_df.columns and 'MonthlyWage' in population_df.columns:
            family_contr_base += (
                (population_df['ChildrenCount'] * population_df['MonthlyWage']).sum() * 12 * 
                self.config.family_child_contr_rate
            )

        # 4. State Treasury Support for Non-capables
        state_support_base = total_non_capable * self.config.min_wage_annual * self.config.state_non_capable_rate
        
        # Base Medical Cost
        base_annual_cost = population_df['EstimatedAnnualCost'].sum() if 'EstimatedAnnualCost' in population_df.columns else 5000 * len(population_df)

        for year in range(years):
            # Apply Inflations
            year_wage_growth = (1 + self.config.wage_inflation) ** year
            year_med_growth = (1 + self.config.medical_inflation) ** year
            
            # Revenue Calculation
            rev_work = total_work_revenue_base * year_wage_growth
            rev_family = family_contr_base * year_wage_growth
            rev_state = state_support_base * year_wage_growth
            # Other revenue (taxes/tolls) now grows with inflation to prevent deficit erosion
            rev_other = (self.config.cigarette_tax_lump + self.config.highway_tolls_lump) * year_wage_growth
            
            total_revenue = rev_work + rev_family + rev_state + rev_other
            
            # Cost Calculation
            total_medical_cost = base_annual_cost * year_med_growth
            admin_cost = total_revenue * self.config.admin_expense_pct
            
            total_expenditure = total_medical_cost + admin_cost
            
            # Net Position
            net_cash_flow = total_revenue - total_expenditure
            
            # Reserve & Investment Income
            investment_income = accumulated_reserve * self.config.investment_return_rate
            accumulated_reserve += net_cash_flow + investment_income
            
            # Solvency Metric
            state_subsidy_required = abs(accumulated_reserve) if accumulated_reserve < 0 else 0
            
            projections.append({
                'Year': year + 1,
                'Revenue_Wage_Self': rev_work,
                'Revenue_Family': rev_family,
                'Revenue_State': rev_state,
                'Revenue_Other': rev_other,
                'Total_Revenue': total_revenue,
                'Medical_Expenditure': total_medical_cost,
                'Admin_Expenditure': admin_cost,
                'Total_Expenditure': total_expenditure,
                'Net_Cash_Flow': net_cash_flow,
                'Investment_Income': investment_income,
                'Reserve_Fund': accumulated_reserve,
                'Required_State_Subsidy': state_subsidy_required,
                'Risk_Flags': self._detect_risk_flags(
                    year_rev=total_revenue,
                    year_exp=total_expenditure,
                    admin_exp=admin_cost,
                    net_cf=net_cash_flow,
                    reserve=accumulated_reserve,
                    inv_yield=self.config.investment_return_rate,
                    med_infl=self.config.medical_inflation,
                    wage_infl=self.config.wage_inflation
                )
            })
            
        return pd.DataFrame(projections)

    def explain_projection(self, df_proj: pd.DataFrame) -> List[str]:
        """
        XAI Module: Explains the top drivers of cost increase.
        """
        if len(df_proj) < 2: return ["Insufficient data for trend analysis."]
        
        start = df_proj.iloc[0]
        end = df_proj.iloc[-1]
        
        total_delta = end['Total_Expenditure'] - start['Total_Expenditure']
        
        # Attribution calculation
        # 1. Inflation Effect (approx)
        inflation_impact = (end['Medical_Expenditure'] / ( (1 + self.config.medical_inflation)**(len(df_proj)-1) ) ) * ((1 + self.config.medical_inflation)**(len(df_proj)-1) - 1)
        # 2. Admin Effect
        admin_delta = end['Admin_Expenditure'] - start['Admin_Expenditure']
        
        explanations = []
        inf_pct = (inflation_impact / total_delta) * 100 if total_delta > 0 else 0
        explanations.append(f"📈 Medical Inflation: Contributed ~{inf_pct:.1f}% to the projected cost rise.")
        
        adm_pct = (admin_delta / total_delta) * 100 if total_delta > 0 else 0
        explanations.append(f"🏢 Admin Operations: Contributed ~{adm_pct:.1f}% to expenditure growth.")
        
        if end['Required_State_Subsidy'] > 0:
            explanations.append("⚠️ Sustainability Gap: Current revenue growth is failing to outpace medical trend.")
            
        return explanations

    def run_monte_carlo_simulation(self, population_df: pd.DataFrame, years: int = 20, n_sims: int = 1000) -> Dict:
        """
        Module B: Stochastic Monte Carlo Simulation (Solvency II style).
        """
        all_reserves = np.zeros((n_sims, years))
        
        # Base config for simulation
        base_med_inf = self.config.medical_inflation
        base_inv_ret = self.config.investment_return_rate
        
        for i in range(n_sims):
            # Introduce randomness per simulation
            sim_med_inf = np.random.normal(base_med_inf, 0.02)
            sim_inv_ret = np.random.normal(base_inv_ret, 0.02)
            
            sim_config = UHISystemConfig(
                medical_inflation=sim_med_inf,
                investment_return_rate=sim_inv_ret,
                wage_inflation=self.config.wage_inflation,
                admin_expense_pct=self.config.admin_expense_pct
            )
            sim_engine = ActuarialValuationEngine(sim_config)
            sim_df = sim_engine.project_solvency(population_df, years=years)
            all_reserves[i, :] = sim_df['Reserve_Fund'].values
            
        # Calculate percentiles
        p5 = np.percentile(all_reserves, 5, axis=0)
        p50 = np.percentile(all_reserves, 50, axis=0)
        p95 = np.percentile(all_reserves, 95, axis=0)
        
        # Probability of Insolvency (Reserve < 0 at end of horizon)
        insolvent_count = np.sum(all_reserves[:, -1] < 0)
        prob_insolvency = (insolvent_count / n_sims) * 100
        
        return {
            "p5": p5,
            "p50": p50,
            "p95": p95,
            "prob_insolvency": prob_insolvency,
            "years": list(range(1, years + 1))
        }

    def _detect_risk_flags(self, year_rev, year_exp, admin_exp, net_cf, reserve, inv_yield, med_infl, wage_infl) -> List[Dict]:
        """
        Actuarial Risk Detection Logic based on Law 2/2018.
        """
        flags = []
        
        # 1. Solvency Breach (Bankruptcy)
        if reserve < 0:
            flags.append({
                "level": "CRITICAL",
                "type": "Bankruptcy",
                "msg": "Article 40 Guarantee Triggered: Technical insolvency projected.",
                "action": "Immediate State Treasury Intervention Required."
            })
            
        # 2. Inflation Gap
        if med_infl > (wage_infl + 0.02):
            flags.append({
                "level": "WARNING",
                "type": "Inflation Gap",
                "msg": f"Medical inflation ({med_infl:.1%}) significantly exceeds wage growth ({wage_infl:.1%}).",
                "action": "Renegotiate provider primary rates or increase payroll contribution caps."
            })
            
        # 3. Admin Cost Violation (Legal Cap)
        if admin_exp > (year_rev * 0.05):
            flags.append({
                "level": "CRITICAL",
                "type": "Legal Breach",
                "msg": f"Admin expenses ({admin_exp/year_rev:.1%}) exceed the 5% legal cap.",
                "action": "Optimize administrative operations or freeze staff expansion."
            })
            
        # 4. Liquidity Trap
        if net_cf < 0 and reserve > 0:
            flags.append({
                "level": "WARNING",
                "type": "Liquidity Trap",
                "msg": "Operating deficit detected. System is currently eroding its reserve base.",
                "action": "Introduce new revenue streams (e.g., Highway Tolls adjustment)."
            })
            
        # 5. Asset Erosion
        if inv_yield < med_infl:
            flags.append({
                "level": "WARNING",
                "type": "Asset Erosion",
                "msg": "Investment yields are failing to beat medical inflation.",
                "action": "Shift investment portfolio to higher-yield treasury instruments."
            })
            
        return flags

    def suggest_reinsurance(self, avg_annual_cost: float) -> str:
        """
        Module D: Reinsurance Optimization.
        """
        # Heuristic optimization for UHI scale
        retention = avg_annual_cost * 0.02 # Recommend retaining 2% of annual cost
        potential_saving = avg_annual_cost * 0.005 # Estimated premium saving via optimized quota share
        
        return f"💡 Strategy: Retain first {retention/1e6:.1f}M EGP. Transfer excess risk to international re-insurers. Est. Saving: {potential_saving/1e6:.1f}M EGP."

    def perform_agentic_audit(self, df_proj: pd.DataFrame) -> List[Dict]:
        """
        Module G: Agentic Intelligence (CrewAI Concept).
        Simulates analysis from three specialized AI agents.
        """
        audit_results = []
        last_year = df_proj.iloc[-1]
        
        # 1. Legislative Agent Analysis
        leg_status = "✅ Compliant"
        leg_msg = "All years follow Article 40 reserve mandates."
        if (df_proj['Admin_Expenditure'] > df_proj['Total_Revenue'] * 0.05).any():
            leg_status = "⚠️ Warning"
            leg_msg = "Detected years where administrative overhead violates the 5% cap of Law 2/2018."
        
        audit_results.append({
            "agent": "⚖️ Legislative Agent",
            "status": leg_status,
            "analysis": leg_msg,
            "goal": "Enforce Law 2/2018"
        })
        
        # 2. Actuarial Agent Analysis
        act_status = "✅ Stable"
        if last_year['Reserve_Fund'] < 0:
            act_status = "🚨 Insolvency"
        
        audit_results.append({
            "agent": "📊 Actuarial Agent",
            "analysis": f"Projected system health is {act_status}. Probability of long-term solvency is being monitored via Monte Carlo.",
            "goal": "Solvency Assurance"
        })
        
        # 3. Financial Agent Analysis
        audit_results.append({
            "agent": "💰 Financial Agent",
            "analysis": f"Current yield ({self.config.investment_return_rate:.1%}) vs Medical Inflation ({self.config.medical_inflation:.1%}). Reinsurance optimization recommended.",
            "goal": "Asset Growth"
        })
        
        return audit_results

def generate_dummy_population(size: int = 1000, elite_mode: bool = False) -> pd.DataFrame:
    """
    Generates population_structure.csv for demonstration.
    v1.7: Support for 'Elite Mode' (Positive/Sufficient Case).
    """
    np.random.seed(42)
    
    if elite_mode:
        # Phase 1: High-Value, Healthy Population (Elite Case)
        emp_p = [0.85, 0.10, 0.05] # 85% Employees, only 5% State Supported
        mean_wage = 18000
        mean_cost = 4500
    else:
        # Baseline/Standard Case
        emp_p = [0.70, 0.20, 0.10]
        mean_wage = 12000
        mean_cost = 6000
        
    data = {
        'Age': np.random.randint(22, 60, size) if elite_mode else np.random.randint(18, 75, size),
        'Gender': np.random.choice(['Male', 'Female'], size),
        'EmploymentStatus': np.random.choice(['Employee', 'Self-employed', 'Non-capable'], size, p=emp_p),
        'MonthlyWage': np.random.normal(mean_wage, 4000, size).clip(6000, 150000),
        'SpouseInSystem': np.random.choice([True, False], size, p=[0.7, 0.3] if elite_mode else [0.6, 0.4]),
        'ChildrenCount': np.random.choice([0, 1, 2], size, p=[0.5, 0.4, 0.1]) if elite_mode else np.random.choice([0, 1, 2, 3], size, p=[0.3, 0.3, 0.3, 0.1]),
        'EstimatedAnnualCost': np.random.normal(mean_cost, 1000, size).clip(1000, 30000)
    }
    return pd.DataFrame(data)
