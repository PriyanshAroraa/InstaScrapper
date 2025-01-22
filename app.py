from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from instagram_analyzer import analyze_account
from dotenv import load_dotenv
import logging
import os
from typing import Union

load_dotenv()

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze")
async def analyze_instagram_account(
    instagram_handle: Union[str, None] = Query(default=None),
    data: Union[dict, None] = Body(default=None)
):
    """
    Analyze an Instagram account by its handle
    Accepts both query parameter and JSON body input
    """
    try:
        # Handle both input methods
        handle = instagram_handle or (data.get("instagram_handle") if data else None)
        
        if not handle:
            raise HTTPException(
                status_code=400,
                detail="Instagram handle is required. Use either query parameter ?instagram_handle=... or JSON body"
            )

        # Clean handle input
        handle = handle.lstrip('@').strip()
        if not handle:
            raise HTTPException(status_code=400, detail="Invalid Instagram handle")

        logger.info(f"Starting analysis for @{handle}")
        
        result = analyze_account(handle)
        
        if 'error' in result:
            logger.error(f"Analysis failed for @{handle}: {result['error']}")
            raise HTTPException(status_code=400, detail=result['error'])
            
        logger.info(f"Successfully analyzed @{handle}")
        return {
            "success": True,
            "handle": f"@{handle}",
            "data": result
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
