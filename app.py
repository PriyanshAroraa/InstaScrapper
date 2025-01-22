from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from instagram_analyzer import analyze_account
from dotenv import load_dotenv
import logging
import os

load_dotenv()

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def analyze_instagram_account(instagram_handle: str):
    """
    Analyze an Instagram account by its handle
    Example: {"instagram_handle": "nike"}
    """
    try:
        if not instagram_handle:
            raise HTTPException(status_code=400, detail="Instagram handle is required")
        
        if not instagram_handle.startswith('@'):
            instagram_handle = f"@{instagram_handle.lstrip('@')}"
        
        result = analyze_account(instagram_handle.lstrip('@'))
        
        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])
            
        return {
            "success": True,
            "data": result,
            "handle": instagram_handle
        }
        
    except Exception as e:
        logging.error(f"API Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
