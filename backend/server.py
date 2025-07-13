from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import aiohttp
import asyncio


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class RadioStation(BaseModel):
    stationuuid: str
    name: str
    url: str
    homepage: Optional[str] = None
    favicon: Optional[str] = None
    tags: str
    country: str
    language: str
    bitrate: int
    codec: str
    votes: Optional[int] = 0
    clickcount: Optional[int] = 0
    lastchangetime: Optional[str] = None

class FavoriteStation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    stationuuid: str
    name: str
    url: str
    country: str
    tags: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Radio Browser API server discovery
async def get_radio_browser_servers():
    """Get available Radio Browser API servers"""
    try:
        # Try multiple known servers
        servers = [
            "https://de1.api.radio-browser.info",
            "https://at1.api.radio-browser.info", 
            "https://nl1.api.radio-browser.info",
            "https://fr1.api.radio-browser.info"
        ]
        
        # Test each server and return the first working one
        for server in servers:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{server}/json/stations", timeout=5) as response:
                        if response.status == 200:
                            logger.info(f"Using Radio Browser server: {server}")
                            return server
            except:
                continue
        
        # Fallback to default if all fail
        logger.warning("All Radio Browser servers failed, using default")
        return "https://at1.api.radio-browser.info"
    except Exception as e:
        logger.error(f"Error getting Radio Browser servers: {e}")
        return "https://at1.api.radio-browser.info"

# Radio Browser API functions
async def fetch_radio_stations(tag: str = "electronic", limit: int = 50):
    """Fetch radio stations from Radio Browser API"""
    try:
        server = await get_radio_browser_servers()
        
        # Use the stations endpoint with tag filter
        url = f"{server}/json/stations/bytag/{tag}"
        params = {
            'limit': limit,
            'hidebroken': 'true',
            'order': 'clickcount',
            'reverse': 'true'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    # Filter for high-quality stations
                    filtered_stations = [
                        station for station in data 
                        if station.get('bitrate', 0) >= 64 and station.get('url') and station.get('url_resolved')
                    ]
                    logger.info(f"Found {len(filtered_stations)} stations for tag '{tag}'")
                    return filtered_stations[:limit]
                else:
                    logger.error(f"Failed to fetch stations: {response.status}")
                    return []
    except Exception as e:
        logger.error(f"Error fetching radio stations: {e}")
        return []

async def search_radio_stations(query: str, limit: int = 30):
    """Search radio stations by name"""
    try:
        server = await get_radio_browser_servers()
        
        # Use the stations endpoint with name filter
        url = f"{server}/json/stations/byname/{query}"
        params = {
            'limit': limit,
            'hidebroken': 'true',
            'order': 'clickcount',
            'reverse': 'true'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    # Filter for electronic music stations
                    electronic_stations = [
                        station for station in data 
                        if any(genre in station.get('tags', '').lower() 
                              for genre in ['electronic', 'techno', 'house', 'trance', 'dance', 'edm'])
                        and station.get('bitrate', 0) >= 64
                        and station.get('url_resolved')
                    ]
                    logger.info(f"Found {len(electronic_stations)} electronic stations for query '{query}'")
                    return electronic_stations[:limit]
                else:
                    logger.error(f"Failed to search stations: {response.status}")
                    return []
    except Exception as e:
        logger.error(f"Error searching radio stations: {e}")
        return []


# API Routes
@api_router.get("/")
async def root():
    return {"message": "World Techno Radio API"}

@api_router.get("/stations/{genre}")
async def get_stations_by_genre(genre: str):
    """Get radio stations by genre (electronic, techno, house, trance, etc.)"""
    try:
        stations = await fetch_radio_stations(genre)
        return {"stations": stations, "count": len(stations)}
    except Exception as e:
        logger.error(f"Error getting stations by genre: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stations")

@api_router.get("/stations")
async def get_all_electronic_stations():
    """Get all electronic music stations"""
    try:
        # Fetch different electronic genres
        genres = ["electronic", "techno", "house", "trance", "dance", "edm"]
        all_stations = []
        
        for genre in genres:
            stations = await fetch_radio_stations(genre, limit=20)
            all_stations.extend(stations)
        
        # Remove duplicates based on stationuuid
        seen = set()
        unique_stations = []
        for station in all_stations:
            if station.get('stationuuid') not in seen:
                seen.add(station.get('stationuuid'))
                unique_stations.append(station)
        
        # Sort by clickcount (popularity)
        unique_stations.sort(key=lambda x: x.get('clickcount', 0), reverse=True)
        
        return {"stations": unique_stations[:100], "count": len(unique_stations[:100])}
    except Exception as e:
        logger.error(f"Error getting all stations: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stations")

@api_router.get("/search/{query}")
async def search_stations(query: str):
    """Search for radio stations by name"""
    try:
        stations = await search_radio_stations(query)
        return {"stations": stations, "count": len(stations)}
    except Exception as e:
        logger.error(f"Error searching stations: {e}")
        raise HTTPException(status_code=500, detail="Failed to search stations")

@api_router.post("/favorites")
async def add_favorite_station(station_data: dict):
    """Add a station to favorites"""
    try:
        favorite = FavoriteStation(
            stationuuid=station_data["stationuuid"],
            name=station_data["name"],
            url=station_data["url"],
            country=station_data.get("country", ""),
            tags=station_data.get("tags", "")
        )
        
        # Check if already in favorites
        existing = await db.favorites.find_one({"stationuuid": favorite.stationuuid})
        if existing:
            return {"message": "Station already in favorites", "favorite": existing}
        
        await db.favorites.insert_one(favorite.dict())
        return {"message": "Station added to favorites", "favorite": favorite}
    except Exception as e:
        logger.error(f"Error adding favorite: {e}")
        raise HTTPException(status_code=500, detail="Failed to add favorite")

@api_router.get("/favorites")
async def get_favorite_stations():
    """Get all favorite stations"""
    try:
        favorites = await db.favorites.find().sort("created_at", -1).to_list(100)
        return {"favorites": favorites, "count": len(favorites)}
    except Exception as e:
        logger.error(f"Error getting favorites: {e}")
        raise HTTPException(status_code=500, detail="Failed to get favorites")

@api_router.delete("/favorites/{stationuuid}")
async def remove_favorite_station(stationuuid: str):
    """Remove a station from favorites"""
    try:
        result = await db.favorites.delete_one({"stationuuid": stationuuid})
        if result.deleted_count > 0:
            return {"message": "Station removed from favorites"}
        else:
            raise HTTPException(status_code=404, detail="Station not found in favorites")
    except Exception as e:
        logger.error(f"Error removing favorite: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove favorite")


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()