"""
FastAPI server for apartment address evaluation
"""

import os
import sys
from typing import Dict, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Add parent directory to path to import src modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from src.main_async import evaluate_address_async

# Load environment variables
load_dotenv()

app = FastAPI(
    title="NYC Apartment Evaluator API",
    description="Evaluate apartment addresses based on commute times, transit access, and amenities",
    version="1.0.0"
)

# Enable CORS for browser extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your extension's origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory cache for evaluations (24-hour TTL)
evaluation_cache: Dict[str, Dict] = {}


class EvaluationRequest(BaseModel):
    """Request body for address evaluation"""
    address: str = Field(..., description="Full street address to evaluate", min_length=5)
    offices: Optional[list] = Field(None, description="Optional custom office locations")


class EvaluationResponse(BaseModel):
    """Response body for address evaluation"""
    address: str
    input_address: str
    timestamp: str
    coordinates: Dict[str, float]
    commutes: Dict[str, Dict]
    subway: Dict
    amenities: Dict
    score: float
    breakdown: Dict
    explanation: str
    cached: bool = False


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "NYC Apartment Evaluator API",
        "version": "1.0.0",
        "endpoints": {
            "POST /evaluate": "Evaluate an apartment address",
            "GET /health": "Health check endpoint"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    google_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "google_maps_configured": bool(google_api_key)
    }


@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(request: EvaluationRequest):
    """
    Evaluate an apartment address
    
    Returns scored evaluation with commute times, transit access, and amenities
    """
    try:
        # Check cache first
        cache_key = request.address.lower().strip()
        if cache_key in evaluation_cache:
            cached_result = evaluation_cache[cache_key]
            # Check if cache is less than 24 hours old
            cached_time = datetime.fromisoformat(cached_result['timestamp'])
            age_hours = (datetime.now() - cached_time).total_seconds() / 3600
            
            if age_hours < 24:
                print(f"Cache hit for address: {request.address}")
                cached_result['cached'] = True
                return cached_result
            else:
                # Remove stale cache entry
                del evaluation_cache[cache_key]
        
        # Evaluate address
        print(f"Evaluating address: {request.address}")
        result = await evaluate_address_async(request.address, custom_offices=request.offices)
        
        # Check for errors
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
        
        # Cache the result
        result['cached'] = False
        evaluation_cache[cache_key] = result
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error evaluating address: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.delete("/cache")
async def clear_cache():
    """Clear the evaluation cache"""
    evaluation_cache.clear()
    return {"message": "Cache cleared", "timestamp": datetime.now().isoformat()}


@app.get("/cache/stats")
async def cache_stats():
    """Get cache statistics"""
    return {
        "cached_addresses": len(evaluation_cache),
        "addresses": list(evaluation_cache.keys())
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
