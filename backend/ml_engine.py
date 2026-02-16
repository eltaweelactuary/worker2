"""
Actuarial ML Engine (v4.0)
Uses Scikit-Learn for Predictive Risk Modeling & Segmentation.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler, LabelEncoder
from typing import Dict, List, Tuple

class ActuarialMLEngine:
    """
    ML Module for predicting costs and segmenting risk.
    """
    def __init__(self):
        self.regressor = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.is_trained = False

    def _preprocess(self, df: pd.DataFrame, training: bool = False) -> pd.DataFrame:
        df_ml = df.copy()
        
        # Categorical Encoding
        cat_cols = ['Gender', 'EmploymentStatus', 'SpouseInSystem']
        for col in cat_cols:
            if col in df_ml.columns:
                if training:
                    le = LabelEncoder()
                    df_ml[col] = le.fit_transform(df_ml[col].astype(str))
                    self.label_encoders[col] = le
                else:
                    le = self.label_encoders.get(col)
                    if le:
                        # Handle unknown categories safely
                        df_ml[col] = df_ml[col].astype(str).map(lambda x: le.transform([x])[0] if x in le.classes_ else -1)

        return df_ml

    def train_cost_model(self, data: pd.DataFrame):
        """
        Trains a Random Forest to predict 'EstimatedAnnualCost' based on demographics.
        """
        if 'EstimatedAnnualCost' not in data.columns:
            return False
        
        X = self._preprocess(data.drop(columns=['EstimatedAnnualCost']), training=True)
        y = data['EstimatedAnnualCost']
        
        self.regressor.fit(X, y)
        self.is_trained = True
        return True

    def predict_individual_risks(self, data: pd.DataFrame) -> List[float]:
        """
        Predicts medical costs for a set of individuals.
        """
        if not self.is_trained:
            # Fallback to simple logic if not trained
            return [5000.0] * len(data)
            
        X = self._preprocess(data)
        if 'EstimatedAnnualCost' in X.columns:
            X = X.drop(columns=['EstimatedAnnualCost'])
            
        preds = self.regressor.predict(X)
        return preds.tolist()

    def segment_population(self, data: pd.DataFrame, n_clusters: int = 3) -> List[int]:
        """
        Uses K-Means to segment the population into risk clusters (Low, Med, High).
        """
        features = ['Age', 'MonthlyWage']
        if 'EstimatedAnnualCost' in data.columns:
            features.append('EstimatedAnnualCost')
            
        X = data[features].fillna(0)
        X_scaled = self.scaler.fit_transform(X)
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_transform(X_scaled)
        
        # Return cluster assignments
        return kmeans.labels_.tolist()

    def get_risk_insights(self, data: pd.DataFrame) -> Dict:
        """
        Composite ML report for executives.
        """
        if data.empty:
            return {}
            
        clusters = self.segment_population(data)
        data['Risk_Segment'] = clusters
        
        avg_cost_by_segment = data.groupby('Risk_Segment')['EstimatedAnnualCost'].mean().to_dict()
        
        # Actuarial Best Practice: Calculate Severity Index (Cost / Mean Cost)
        overall_mean = data['EstimatedAnnualCost'].mean()
        severity_index = {str(k): float(v/overall_mean) for k,v in avg_cost_by_segment.items()}
        
        return {
            "risk_distribution": pd.Series(clusters).value_counts().to_dict(),
            "avg_cost_by_segment": {str(k): float(v) for k,v in avg_cost_by_segment.items()},
            "segment_severity": severity_index,
            "high_risk_threshold": float(data['EstimatedAnnualCost'].quantile(0.90)),
            "high_risk_count": int(len(data[data['EstimatedAnnualCost'] > data['EstimatedAnnualCost'].quantile(0.90)]))
        }
