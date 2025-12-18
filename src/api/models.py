from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ScrapeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScrapeFilters(BaseModel):
    """Search filters for car listings"""
    znamka: Optional[List[str]] = Field(default=None, description="Brand(s) - empty string for all brands")
    model: Optional[str] = Field(default=None, description="Model name - empty string for all models")
    cenaMin: Optional[int] = Field(default=None, description="Minimum price in EUR")
    cenaMax: Optional[int] = Field(default=None, description="Maximum price in EUR")
    subcenaMIN: Optional[int] = Field(default=None, description="Price range minimum (Avto.net specific)")
    subcenaMAX: Optional[int] = Field(default=None, description="Price range maximum (Avto.net specific)")
    letnikMin: Optional[int] = Field(default=None, description="Minimum registration year")
    letnikMax: Optional[int] = Field(default=None, description="Maximum registration year")
    kmMin: Optional[int] = Field(default=None, description="Minimum mileage")
    kmMax: Optional[int] = Field(default=None, description="Maximum mileage")
    kwMin: Optional[int] = Field(default=None, description="Minimum engine power (kW)")
    kwMax: Optional[int] = Field(default=None, description="Maximum engine power (kW)")
    ccmMin: Optional[int] = Field(default=None, description="Minimum engine displacement (ccm)")
    ccmMax: Optional[int] = Field(default=None, description="Maximum engine displacement (ccm)")
    mocMin: Optional[str] = Field(default=None, description="Minimum power")
    mocMax: Optional[str] = Field(default=None, description="Maximum power")
    subLOCATION: Optional[str] = Field(default=None, description="Location filter")
    oblika: Optional[str] = Field(default=None, description="Body type")
    bencin: Optional[int] = Field(default=None, description="Fuel type: 0=all, 201=petrol, 202=diesel, 207=electric")
    EQ1: Optional[int] = Field(default=None, description="Equipment flag 1")
    EQ2: Optional[int] = Field(default=None, description="Equipment flag 2")
    EQ3: Optional[int] = Field(default=None, description="Equipment flag 3 (Transmission)")
    EQ4: Optional[int] = Field(default=None, description="Equipment flag 4")
    EQ5: Optional[int] = Field(default=None, description="Equipment flag 5")
    EQ6: Optional[int] = Field(default=None, description="Equipment flag 6")
    EQ7: Optional[int] = Field(default=None, description="Equipment flag 7 (Status)")
    EQ8: Optional[int] = Field(default=None, description="Equipment flag 8")
    EQ9: Optional[int] = Field(default=None, description="Equipment flag 9")
    EQ10: Optional[int] = Field(default=None, description="Equipment flag 10")
    sort: Optional[str] = Field(default=None, description="Sort field")
    sort_order: Optional[str] = Field(default=None, description="Sort order")
    presort: Optional[str] = Field(default=None, description="Pre-sort option")
    tipsort: Optional[str] = Field(default=None, description="Tip sort option")
    lastnikov: Optional[str] = Field(default=None, description="Number of owners filter")

    class Config:
        json_schema_extra = {
            "example": {
                "znamka": ["Volkswagen"],
                "model": "Golf",
                "cenaMin": 10000,
                "cenaMax": 25000,
                "letnikMin": 2015,
                "letnikMax": 2023,
                "kmMin": 0,
                "kmMax": 100000,
                "bencin": 201
            }
        }


class CarListing(BaseModel):
    """Car listing data"""
    HASH: str
    URL: str
    Cena: Optional[str] = None
    Naziv: Optional[str] = None
    registracija: Optional[str] = Field(None, alias="1.registracija", serialization_alias="1.registracija")
    Prevoženih: Optional[str] = None
    Menjalnik: Optional[str] = None
    Motor: Optional[str] = None
    lastnikov: Optional[str] = None

    class Config:
        populate_by_name = True


class ScrapeJobResponse(BaseModel):
    """Response when starting a scrape job"""
    job_id: str
    status: ScrapeStatus
    message: str
    created_at: datetime


class ScrapeStatusResponse(BaseModel):
    """Response for scrape job status"""
    job_id: str
    status: ScrapeStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    total_listings: Optional[int] = None
    error: Optional[str] = None


class ScrapeResultsResponse(BaseModel):
    """Response containing scrape results"""
    job_id: str
    status: ScrapeStatus
    total_listings: int
    listings: List[CarListing]
    created_at: datetime
    completed_at: Optional[datetime] = None

