"""
Actuarial Valuation Engine for Egypt Universal Health Insurance (UHI)
Complies with Law No. 2 of 2018.
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
        
        # Initial State
        accumulated_reserve = 0.0
        
        # Base Population Metrics
        total_employees = len(population_df[population_df['EmploymentStatus'] == 'Employee'])
        total_self_employed = len(population_df[population_df['EmploymentStatus'] == 'Self-employed'])
        total_non_capable = len(population_df[population_df['EmploymentStatus'] == 'Non-capable'])
        
        # Calculate Base Annual Revenue from Population
        # 1. Employee + Employer Contributions
        wage_revenue_base = (
            population_df[population_df['EmploymentStatus'] == 'Employee']['MonthlyWage'].sum() * 12 * 
            (self.config.employee_contr_rate + self.config.employer_contr_rate)
        )
        
        # 2. Self-employed Contributions (4% total)
        self_employed_revenue_base = (
            population_df[population_df['EmploymentStatus'] == 'Self-employed']['MonthlyWage'].sum() * 12 * 
            self.config.self_employed_contr_rate
        )
        
        # Combine work-based revenue
        total_work_revenue_base = wage_revenue_base + self_employed_revenue_base
        
        # 3. Family Contributions (Heads of families pay for dependents)
        family_contr_base = 0
        if 'SpouseInSystem' in population_df.columns:
            family_contr_base += (
                population_df[population_df['SpouseInSystem'] == True]['MonthlyWage'].sum() * 12 * 
                self.config.family_spouse_contr_rate
            )
        if 'ChildrenCount' in population_df.columns:
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
            rev_other = self.config.cigarette_tax_lump + self.config.highway_tolls_lump
            
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
                'Required_State_Subsidy': state_subsidy_required
            })
            
        return pd.DataFrame(projections)

def generate_dummy_population(size: int = 1000) -> pd.DataFrame:
    """
    Generates population_structure.csv for demonstration.
    """
    np.random.seed(42)
    data = {
        'Age': np.random.randint(18, 75, size),
        'Gender': np.random.choice(['Male', 'Female'], size),
        'EmploymentStatus': np.random.choice(['Employee', 'Self-employed', 'Non-capable'], size, p=[0.6, 0.2, 0.2]),
        'MonthlyWage': np.random.normal(6000, 2000, size).clip(3000, 50000),
        'SpouseInSystem': np.random.choice([True, False], size),
        'ChildrenCount': np.random.choice([0, 1, 2, 3], size, p=[0.4, 0.3, 0.2, 0.1]),
        'EstimatedAnnualCost': np.random.normal(5000, 1500, size).clip(500, 50000)
    }
    return pd.DataFrame(data)
