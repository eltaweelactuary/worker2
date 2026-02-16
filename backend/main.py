from fastapi import FastAPI, HTTPException, Body, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import pandas as pd
import io
from pricing_engine import UHISystemConfig, ActuarialValuationEngine, generate_dummy_population
from gcp_utils import ask_gemini_actuary, get_gcp_project
from ml_engine import ActuarialMLEngine

app = FastAPI(title="UHI Actuarial API", version="4.0.0")

# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Schemas ---

class SimulationRequest(BaseModel):
    wage_inflation: float = 0.07
    medical_inflation: float = 0.12
    investment_return_rate: float = 0.10
    admin_expense_pct: float = 0.04
    projection_years: int = 10
    population_size: int = 1000
    elite_mode: bool = False

class AIConsultationRequest(BaseModel):
    query: str
    data_summary: str
    persona: str
    api_key: Optional[str] = None

# --- Endpoints ---

@app.get("/")
async def root():
    return {"status": "active", "engine": "FastAPI Actuarial v4.0", "project": get_gcp_project()}

# --- Data Import ---

REQUIRED_COLUMNS = ['Age', 'Gender', 'EmploymentStatus', 'MonthlyWage', 'SpouseInSystem', 'ChildrenCount', 'EstimatedAnnualCost']

@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise HTTPException(status_code=400, detail=f"Missing columns: {', '.join(missing)}. Required: {', '.join(REQUIRED_COLUMNS)}")
        return {
            "status": "success",
            "rows": len(df),
            "columns": list(df.columns),
            "sample": df.head(5).to_dict(orient='records'),
            "statistics": {
                "avg_age": round(df['Age'].mean(), 1),
                "avg_wage": round(df['MonthlyWage'].mean(), 0),
                "avg_cost": round(df['EstimatedAnnualCost'].mean(), 0),
                "gender_split": df['Gender'].value_counts().to_dict(),
                "employment_split": df['EmploymentStatus'].value_counts().to_dict()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV Parse Error: {str(e)}")

@app.get("/sample-data")
async def sample_data(size: int = 1000, elite_mode: bool = False):
    df = generate_dummy_population(size=size, elite_mode=elite_mode)
    return {
        "status": "success",
        "rows": len(df),
        "columns": list(df.columns),
        "sample": df.head(5).to_dict(orient='records'),
        "statistics": {
            "avg_age": round(df['Age'].mean(), 1),
            "avg_wage": round(df['MonthlyWage'].mean(), 0),
            "avg_cost": round(df['EstimatedAnnualCost'].mean(), 0),
            "gender_split": df['Gender'].value_counts().to_dict(),
            "employment_split": df['EmploymentStatus'].value_counts().to_dict()
        }
    }

@app.post("/simulate")
async def simulate(req: SimulationRequest):
    try:
        config = UHISystemConfig(
            wage_inflation=req.wage_inflation,
            medical_inflation=req.medical_inflation,
            investment_return_rate=req.investment_return_rate,
            admin_expense_pct=req.admin_expense_pct
        )
        engine = ActuarialValuationEngine(config)
        pop_df = generate_dummy_population(size=req.population_size, elite_mode=req.elite_mode)
        
        projections = engine.project_solvency(pop_df, years=req.projection_years)
        explanation = engine.explain_projection(projections)
        audit = engine.perform_agentic_audit(projections)
        
        return {
            "projections": projections,
            "explanation": explanation,
            "audit": audit,
            "config": config.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/monte-carlo")
async def monte_carlo(req: SimulationRequest):
    try:
        config = UHISystemConfig(
            wage_inflation=req.wage_inflation,
            medical_inflation=req.medical_inflation,
            investment_return_rate=req.investment_return_rate,
            admin_expense_pct=req.admin_expense_pct
        )
        engine = ActuarialValuationEngine(config)
        pop_df = generate_dummy_population(size=req.population_size, elite_mode=req.elite_mode)
        
        results = engine.run_monte_carlo_simulation(pop_df, years=req.projection_years, n_sims=100)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask-ai")
async def ask_ai(req: AIConsultationRequest):
    try:
        response = ask_gemini_actuary(
            user_query=req.query,
            data_summary=req.data_summary,
            persona=req.persona,
            api_key=req.api_key
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ML Endpoints ---

@app.post("/ml/analysis")
async def ml_analysis(population_size: int = 1000, elite_mode: bool = False):
    try:
        from ml_engine import ActuarialMLEngine
        ml = ActuarialMLEngine()
        
        pop_df = generate_dummy_population(size=population_size, elite_mode=elite_mode)
        
        # Train on current pop (Simplified for Demo)
        ml.train_cost_model(pop_df)
        insights = ml.get_risk_insights(pop_df)
        
        return {
            "ml_status": "Active",
            "insights": insights
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Health Check ---

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "4.0.0", "project": get_gcp_project()}

# --- Actuarial Report (Law 2/2018 Format) ---

class ReportRequest(BaseModel):
    projection_years: int = 10
    population_size: int = 1000
    wage_inflation: float = 0.07
    medical_inflation: float = 0.12
    investment_return_rate: float = 0.10
    admin_expense_pct: float = 0.04

@app.post("/report")
async def generate_report(req: ReportRequest):
    try:
        config = UHISystemConfig(
            wage_inflation=req.wage_inflation,
            medical_inflation=req.medical_inflation,
            investment_return_rate=req.investment_return_rate,
            admin_expense_pct=req.admin_expense_pct
        )
        engine = ActuarialValuationEngine(config)
        pop_df = generate_dummy_population(size=req.population_size)

        projections = engine.project_solvency(pop_df, years=req.projection_years)
        explanation = engine.explain_projection(projections)
        audit = engine.perform_agentic_audit(projections)

        # --- Build Law 2/2018 Compliant Report ---
        first = projections[0]
        last = projections[-1]
        total_revenue_final = last.get("Total_Revenue", 0)
        total_expenditure_final = last.get("Total_Expenditure", 0)
        reserve_final = last.get("Reserve_Fund", 0)
        solvency_ratio = total_revenue_final / total_expenditure_final if total_expenditure_final > 0 else 0
        risk_flags = last.get("Risk_Flags", [])

        # Compliance determination
        is_solvent = solvency_ratio >= 1.0
        compliance_status = "COMPLIANT" if is_solvent and len(risk_flags) == 0 else "NON-COMPLIANT — Action Required"

        # Year-by-year summary
        yearly_summary = []
        for p in projections:
            yr_rev = p.get("Total_Revenue", 0)
            yr_exp = p.get("Total_Expenditure", 0)
            yearly_summary.append({
                "year": p.get("Year"),
                "total_revenue": round(yr_rev, 2),
                "total_expenditure": round(yr_exp, 2),
                "reserve_fund": round(p.get("Reserve_Fund", 0), 2),
                "solvency_ratio": round(yr_rev / yr_exp, 4) if yr_exp > 0 else 0,
                "risk_flags": p.get("Risk_Flags", [])
            })

        # Build recommendations
        recommendations = []
        if not is_solvent:
            recommendations.append("CRITICAL: Solvency ratio below 1.0 — immediate corrective action required per Article 43.")
            recommendations.append("Consider increasing contribution rates per Article 40 schedule.")
        if len(risk_flags) > 0:
            recommendations.append(f"WARNING: {len(risk_flags)} risk flag(s) detected in final projection year.")
        if req.medical_inflation > 0.10:
            recommendations.append("Medical inflation exceeds 10% — recommend negotiating provider rate caps per Article 44.")
        if solvency_ratio > 1.5:
            recommendations.append("Strong solvency position — consider expanding coverage benefits per Article 2.")
        if not recommendations:
            recommendations.append("System is within acceptable actuarial parameters. Continue monitoring.")

        report = {
            "report_title": "Actuarial Valuation Report — Universal Health Insurance (Law 2/2018)",
            "report_version": "v4.0",
            "legal_reference": "Arab Republic of Egypt — Law No. 2 of 2018 (Universal Health Insurance)",
            "executive_summary": {
                "assessment_period": f"{req.projection_years} Years",
                "population_covered": f"{req.population_size:,} members",
                "final_solvency_ratio": round(solvency_ratio, 4),
                "final_reserve_fund_egp": round(reserve_final, 2),
                "compliance_status": compliance_status,
                "total_risk_flags": len(risk_flags),
                "risk_flags_detail": risk_flags
            },
            "assumptions": {
                "wage_inflation": f"{req.wage_inflation:.1%}",
                "medical_inflation": f"{req.medical_inflation:.1%}",
                "investment_return_rate": f"{req.investment_return_rate:.1%}",
                "admin_expense_pct": f"{req.admin_expense_pct:.1%}"
            },
            "financial_projections": yearly_summary,
            "narrative_explanation": explanation,
            "agentic_audit": audit,
            "recommendations": recommendations
        }

        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

