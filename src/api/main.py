"""
FastAPI application for Avto-Net Scraper API - User-based persistent system
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import os

from src.api.models import ScrapeFilters
from src.database.models import Database, UserManager
from src.shared.log import logger

# Initialize database
db = Database(db_path=os.getenv("DB_PATH", "data/scraper.db"))
user_manager = UserManager(db)

# Note: Lifespan context is handled in api_server.py
app = FastAPI(
    title="Avto-Net Scraper API",
    description="User-based persistent scraping system for avto.net",
    version="2.0.0"
)

# CORS middleware for PWA compatibility
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserRegistrationRequest(BaseModel):
    """Request model for user registration"""
    user_id: str = Field(..., description="Unique user identifier")
    pushover_api_token: str = Field(..., description="Pushover API token")
    pushover_user_key: str = Field(..., description="Pushover user key")
    filters: ScrapeFilters = Field(..., description="Search filters")
    notify_on_first_scrape: Optional[bool] = Field(
        default=False,
        description="Send notifications on first scrape (default: False)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "pushover_api_token": "your_pushover_api_token",
                "pushover_user_key": "your_pushover_user_key",
                "filters": {
                    "znamka": ["Volkswagen"],
                    "model": "Golf",
                    "cenaMin": 10000,
                    "cenaMax": 25000,
                    "letnikMin": 2015,
                    "letnikMax": 2023
                },
                "notify_on_first_scrape": False
            }
        }


class UserUpdateRequest(BaseModel):
    """Request model for updating user filters"""
    pushover_api_token: Optional[str] = Field(None, description="Pushover API token")
    pushover_user_key: Optional[str] = Field(None, description="Pushover user key")
    filters: Optional[ScrapeFilters] = Field(None, description="Search filters")
    notify_on_first_scrape: Optional[bool] = Field(None, description="Notify on first scrape")


class UserResponse(BaseModel):
    """Response model for user information"""
    user_id: str
    filters: Dict
    notify_on_first_scrape: bool
    created_at: str
    updated_at: str


class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool
    message: str


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Avto-Net Scraper API v2.0",
        "version": "2.0.0",
        "description": "User-based persistent scraping system",
        "endpoints": {
            "POST /api/users/register": "Register a new user with filters",
            "GET /api/users/{user_id}": "Get user information",
            "PUT /api/users/{user_id}": "Update user filters or Pushover keys",
            "DELETE /api/users/{user_id}": "Deactivate a user",
            "GET /api/health": "Health check"
        }
    }


@app.post("/api/users/register", response_model=SuccessResponse, status_code=201)
async def register_user(request: UserRegistrationRequest):
    """
    Register a new user with filters and Pushover credentials.
    
    The user will be automatically included in the background scraping loop.
    """
    try:
        logger.info(f"Registration request received for user: {request.user_id}")
        logger.info(f"Filters provided: {request.filters.model_dump(exclude_none=True)}")
        
        # Convert filters to dict, exclude None values (only include explicitly set fields)
        filters_dict = request.filters.model_dump(exclude_none=True, exclude_unset=True)
        
        # Remove empty strings and empty lists (only keep meaningful values)
        filters_dict = {k: v for k, v in filters_dict.items() 
                       if v != "" and v != [] and v is not None}
        
        # Normalize znamka to list format
        if "znamka" in filters_dict:
            znamka = filters_dict["znamka"]
            if isinstance(znamka, str):
                filters_dict["znamka"] = [znamka] if znamka else [""]
            elif not isinstance(znamka, list):
                filters_dict["znamka"] = [""]
        
        success = user_manager.create_or_update_user(
            user_id=request.user_id,
            pushover_api_token=request.pushover_api_token,
            pushover_user_key=request.pushover_user_key,
            filters=filters_dict,
            notify_on_first_scrape=request.notify_on_first_scrape
        )
        
        if success:
            return SuccessResponse(
                success=True,
                message=f"User {request.user_id} registered successfully. Scraping will start automatically."
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to register user")
            
    except Exception as e:
        logger.error(f"Error registering user: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to register user: {str(e)}")


@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Get user information"""
    user = user_manager.get_user(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    return UserResponse(
        user_id=user['user_id'],
        filters=user['filters'],
        notify_on_first_scrape=user['notify_on_first_scrape'],
        created_at=user['created_at'],
        updated_at=user['updated_at']
    )


@app.put("/api/users/{user_id}", response_model=SuccessResponse)
async def update_user(user_id: str, request: UserUpdateRequest):
    """Update user filters or Pushover credentials"""
    # Get existing user
    existing_user = user_manager.get_user(user_id)
    
    if not existing_user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    # Merge updates
    pushover_api_token = request.pushover_api_token or existing_user['pushover_api_token']
    pushover_user_key = request.pushover_user_key or existing_user['pushover_user_key']
    filters = existing_user['filters']
    notify_on_first_scrape = request.notify_on_first_scrape if request.notify_on_first_scrape is not None else existing_user['notify_on_first_scrape']
    
    # Update filters if provided
    if request.filters:
        filters_dict = request.filters.model_dump(exclude_none=True)
        
        # Remove default values that user didn't explicitly set
        defaults_to_remove = {
            'letnikMin': 2000, 'letnikMax': 2090,
            'kmMin': 0, 'kmMax': 300000,
            'kwMin': 0, 'kwMax': 999,
            'ccmMin': 0, 'ccmMax': 99999,
            'bencin': 0,
            'EQ1': 1001000000, 'EQ2': 1000000000, 'EQ3': 1001000000,
            'EQ4': 100000000, 'EQ5': 1000000000, 'EQ6': 1000000000,
            'EQ7': 1000000000, 'EQ8': 101000000, 'EQ9': 100000002, 'EQ10': 1000000000
        }
        
        # Remove defaults that match exactly
        filters_dict = {k: v for k, v in filters_dict.items() 
                       if k not in defaults_to_remove or v != defaults_to_remove[k]}
        
        # Normalize znamka
        if "znamka" in filters_dict:
            znamka = filters_dict["znamka"]
            if isinstance(znamka, str):
                filters_dict["znamka"] = [znamka] if znamka else [""]
            elif not isinstance(znamka, list):
                filters_dict["znamka"] = [""]
        
        # Replace existing filters (don't merge, replace)
        filters = filters_dict
    
    success = user_manager.create_or_update_user(
        user_id=user_id,
        pushover_api_token=pushover_api_token,
        pushover_user_key=pushover_user_key,
        filters=filters,
        notify_on_first_scrape=notify_on_first_scrape
    )
    
    if success:
        return SuccessResponse(
            success=True,
            message=f"User {user_id} updated successfully"
        )
    else:
        raise HTTPException(status_code=500, detail="Failed to update user")


@app.delete("/api/users/{user_id}", response_model=SuccessResponse)
async def deactivate_user(user_id: str):
    """Deactivate a user (stops scraping for this user)"""
    success = user_manager.deactivate_user(user_id)
    
    if success:
        return SuccessResponse(
            success=True,
            message=f"User {user_id} deactivated successfully"
        )
    else:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        users = user_manager.get_all_active_users()
        return {
            "status": "healthy",
            "database": "connected",
            "active_users": len(users)
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@app.post("/api/users/{user_id}/test-notification", response_model=SuccessResponse)
async def test_notification(user_id: str):
    """
    Send a test Pushover notification to verify credentials are working.
    This sends a test message without scraping.
    """
    user = user_manager.get_user(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    
    try:
        from src.api.notifications import send_pushover_notification_for_listing
        
        # Create a test listing
        test_listing = {
            'HASH': 'test_' + str(int(__import__('time').time())),
            'URL': 'https://www.avto.net/',
            'Cena': '15000',
            'Naziv': 'Test Car - Notification Test',
            '1.registracija': '2020',
            'Prevoženih': '50000',
            'Menjalnik': 'Avtomatski',
            'Motor': '2.0 TDI, 110kW',
            'lastnikov': '1'
        }
        
        # Send test notification
        success = send_pushover_notification_for_listing(
            test_listing,
            user['pushover_api_token'],
            user['pushover_user_key']
        )
        
        if success:
            return SuccessResponse(
                success=True,
                message=f"Test notification sent to user {user_id}. Check your Pushover app!"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to send test notification. Check your Pushover credentials."
            )
            
    except Exception as e:
        logger.error(f"Error sending test notification: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send test notification: {str(e)}"
        )


@app.post("/api/monitoring/start", response_model=SuccessResponse)
async def start_monitoring():
    """
    Start the monitoring service (scraper worker).
    Note: This endpoint is informational - the worker starts automatically with the API server.
    """
    return SuccessResponse(
        success=True,
        message="Monitoring is active. The scraper runs automatically every 60 seconds."
    )


@app.post("/api/monitoring/stop", response_model=SuccessResponse)
async def stop_monitoring():
    """
    Stop the monitoring service by shutting down the API server.
    Note: This will stop the entire API server process.
    """
    import asyncio
    import signal
    
    logger.info("Stop monitoring requested - shutting down server")
    
    # Schedule shutdown after response is sent
    async def shutdown_delayed():
        await asyncio.sleep(1)  # Give time for response to be sent
        logger.info("Shutting down server...")
        os.kill(os.getpid(), signal.SIGTERM)
    
    asyncio.create_task(shutdown_delayed())
    
    return SuccessResponse(
        success=True,
        message="Monitoring stopped. Server will shut down shortly."
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
