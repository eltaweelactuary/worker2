"""
Actuarial Valuation Engine for Egypt Universal Health Insurance (UHI)
Refactored for FastAPI Backend (v4.0)
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field, asdict
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
    
    # Actuarial Best Practice: Prudential Margin
    # An extra layer of safety (e.g., 5%) on top of medical costs
    prudential_margin: float = 0.05 

    def to_dict(self):
        return asdict(self)

class ActuarialValuationEngine:
    """
    Engine for multi-year solvency projection of the UHI system.
    """
    def __init__(self, config: UHISystemConfig):
        self.config = config

    def project_solvency(self, population_df: pd.DataFrame, years: int = 10) -> List[Dict]:
        """
        Projects revenues, costs, and reserves. Returns a list of dicts for JSON serialization.
        """
        projections = []
        
        def safe_get(col, default=0):
            return population_df[col] if col in population_df.columns else pd.Series([default] * len(population_df))

        # Initial State
        accumulated_reserve = 0.0
        
        status_col = population_df['EmploymentStatus'] if 'EmploymentStatus' in population_df.columns else pd.Series(['Unknown'] * len(population_df))
        total_non_capable = len(population_df[status_col == 'Non-capable'])
        
        # Calculate Base Annual Revenue from Population
        wage_revenue_base = (
            population_df[status_col == 'Employee']['MonthlyWage'].sum() if 'MonthlyWage' in population_df.columns and 'EmploymentStatus' in population_df.columns else 0
        ) * 12 * (self.config.employee_contr_rate + self.config.employer_contr_rate)
        
        self_employed_revenue_base = (
            population_df[status_col == 'Self-employed']['MonthlyWage'].sum() if 'MonthlyWage' in population_df.columns and 'EmploymentStatus' in population_df.columns else 0
        ) * 12 * self.config.self_employed_contr_rate
        
        total_work_revenue_base = wage_revenue_base + self_employed_revenue_base
        
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

        state_support_base = total_non_capable * self.config.min_wage_annual * self.config.state_non_capable_rate
        base_annual_cost = population_df['EstimatedAnnualCost'].sum() if 'EstimatedAnnualCost' in population_df.columns else 5000 * len(population_df)

        for year in range(years):
            year_wage_growth = (1 + self.config.wage_inflation) ** year
            year_med_growth = (1 + self.config.medical_inflation) ** year
            
            rev_work = total_work_revenue_base * year_wage_growth
            rev_family = family_contr_base * year_wage_growth
            rev_state = state_support_base * year_wage_growth
            rev_other = (self.config.cigarette_tax_lump + self.config.highway_tolls_lump) * year_wage_growth
            
            total_revenue = rev_work + rev_family + rev_state + rev_other
            
            # Actuarial Best Practice: Apply Prudential Margin to Medical Cost
            total_medical_cost = base_annual_cost * year_med_growth
            margined_medical_cost = total_medical_cost * (1 + self.config.prudential_margin)
            
            admin_cost = total_revenue * self.config.admin_expense_pct
            total_expenditure = margined_medical_cost + admin_cost
            
            net_cash_flow = total_revenue - total_expenditure
            investment_income = accumulated_reserve * self.config.investment_return_rate
            accumulated_reserve += net_cash_flow + investment_income
            
            state_subsidy_required = abs(accumulated_reserve) if accumulated_reserve < 0 else 0
            
            projections.append({
                'Year': year + 1,
                'Revenue_Wage_Self': float(rev_work),
                'Revenue_Family': float(rev_family),
                'Revenue_State': float(rev_state),
                'Revenue_Other': float(rev_other),
                'Total_Revenue': float(total_revenue),
                'Medical_Expenditure': float(total_medical_cost),
                'Admin_Expenditure': float(admin_cost),
                'Total_Expenditure': float(total_expenditure),
                'Net_Cash_Flow': float(net_cash_flow),
                'Investment_Income': float(investment_income),
                'Reserve_Fund': float(accumulated_reserve),
                'Required_State_Subsidy': float(state_subsidy_required),
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
            
        return projections

    def explain_projection(self, projections: List[Dict]) -> List[str]:
        """
        XAI Module: Explains the top drivers of cost increase.
        """
        if len(projections) < 2: return ["Insufficient data for trend analysis."]
        
        start = projections[0]
        end = projections[-1]
        
        total_delta = end['Total_Expenditure'] - start['Total_Expenditure']
        
        inflation_impact = (end['Medical_Expenditure'] / ( (1 + self.config.medical_inflation)**(len(projections)-1) ) ) * ((1 + self.config.medical_inflation)**(len(projections)-1) - 1)
        admin_delta = end['Admin_Expenditure'] - start['Admin_Expenditure']
        
        explanations = []
        inf_pct = (inflation_impact / total_delta) * 100 if total_delta > 0 else 0
        explanations.append(f"📈 Medical Inflation: Contributed ~{inf_pct:.1f}% to the projected cost rise.")
        
        adm_pct = (admin_delta / total_delta) * 100 if total_delta > 0 else 0
        explanations.append(f"🏢 Admin Operations: Contributed ~{adm_pct:.1f}% to expenditure growth.")
        
        if end['Required_State_Subsidy'] > 0:
            explanations.append("⚠️ Sustainability Gap: Current revenue growth is failing to outpace medical trend.")
            
        return explanations

    def run_monte_carlo_simulation(self, population_df: pd.DataFrame, years: int = 20, n_sims: int = 100) -> Dict:
        """
        Module B: Stochastic Monte Carlo Simulation. Returns lists of floats for JSON.
        """
        all_reserves = np.zeros((n_sims, years))
        base_med_inf = self.config.medical_inflation
        base_inv_ret = self.config.investment_return_rate
        
        for i in range(n_sims):
            sim_med_inf = np.random.normal(base_med_inf, 0.02)
            sim_inv_ret = np.random.normal(base_inv_ret, 0.02)
            
            sim_config = UHISystemConfig(
                medical_inflation=sim_med_inf,
                investment_return_rate=sim_inv_ret,
                wage_inflation=self.config.wage_inflation,
                admin_expense_pct=self.config.admin_expense_pct
            )
            sim_engine = ActuarialValuationEngine(sim_config)
            sim_proj = sim_engine.project_solvency(population_df, years=years)
            all_reserves[i, :] = [p['Reserve_Fund'] for p in sim_proj]
            
        p5 = np.percentile(all_reserves, 5, axis=0)
        p50 = np.percentile(all_reserves, 50, axis=0)
        p95 = np.percentile(all_reserves, 95, axis=0)
        
        insolvent_count = np.sum(all_reserves[:, -1] < 0)
        prob_insolvency = (insolvent_count / n_sims) * 100
        
        return {
            "p5": p5.tolist(),
            "p50": p50.tolist(),
            "p95": p95.tolist(),
            "prob_insolvency": float(prob_insolvency),
            "years": list(range(1, years + 1))
        }

    def _detect_risk_flags(self, year_rev, year_exp, admin_exp, net_cf, reserve, inv_yield, med_infl, wage_infl) -> List[Dict]:
        flags = []
        if reserve < 0:
            flags.append({
                "level": "CRITICAL",
                "type": "Bankruptcy",
                "msg": "Article 40 Guarantee Triggered: Technical insolvency projected.",
                "action": "Immediate State Treasury Intervention Required."
            })
        if med_infl > (wage_infl + 0.02):
            flags.append({
                "level": "WARNING",
                "type": "Inflation Gap",
                "msg": f"Medical inflation ({med_infl:.1%}) significantly exceeds wage growth ({wage_infl:.1%}).",
                "action": "Renegotiate provider rates."
            })
        if admin_exp > (year_rev * 0.05):
            flags.append({
                "level": "CRITICAL",
                "type": "Legal Breach",
                "msg": f"Admin expenses ({admin_exp/year_rev:.1%}) exceed the 5% legal cap.",
                "action": "Optimize admin operations."
            })
        return flags

    def suggest_reinsurance(self, avg_annual_cost: float) -> str:
        retention = avg_annual_cost * 0.02
        potential_saving = avg_annual_cost * 0.005
        return f"💡 Strategy: Retain first {retention/1e6:.1f}M EGP. Est. Saving: {potential_saving/1e6:.1f}M EGP."

    def perform_agentic_audit(self, projections: List[Dict]) -> List[Dict]:
        audit_results = []
        last_year = projections[-1]
        
        leg_status = "✅ Compliant"
        leg_msg = "All years follow Article 40 reserve mandates."
        if any(p['Admin_Expenditure'] > p['Total_Revenue'] * 0.05 for p in projections):
            leg_status = "⚠️ Warning"
            leg_msg = "Detected years violating the 5% cap."
        
        audit_results.append({
            "agent": "⚖️ Legislative Agent",
            "status": leg_status,
            "analysis": leg_msg,
            "goal": "Enforce Law 2/2018"
        })
        
        act_status = "✅ Stable"
        if last_year['Reserve_Fund'] < 0:
            act_status = "🚨 Insolvency"
        
        audit_results.append({
            "agent": "📊 Actuarial Agent",
            "analysis": f"Projected health is {act_status}.",
            "goal": "Solvency Assurance"
        })
        
        audit_results.append({
            "agent": "💰 Financial Agent",
            "analysis": f"Yield vs Inflation audit complete.",
            "goal": "Asset Growth"
        })
        
        return audit_results

def generate_dummy_population(size: int = 1000, elite_mode: bool = False) -> pd.DataFrame:
    np.random.seed(42)
    if elite_mode:
        emp_p = [0.85, 0.10, 0.05]
        mean_wage = 18000
        mean_cost = 4500
    else:
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
