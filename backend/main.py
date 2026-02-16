from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import pandas as pd
import io
from pricing_engine import UHISystemConfig, ActuarialValuationEngine, generate_dummy_population
from gcp_utils import ask_gemini_actuary, get_gcp_project
from ml_engine import ActuarialMLEngine

app = FastAPI(title="UHI Actuarial API", version="4.0.0")

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
