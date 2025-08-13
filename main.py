from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from geopy.geocoders import Nominatim
import requests
import os
import logging
import uvicorn
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
import json

# Фильтр для игнорирования запросов Chrome DevTools
class ChromeDevtoolsFilter(logging.Filter):
    def filter(self, record):
        return "com.chrome.devtools.json" not in record.getMessage()

# Применяем фильтр к логгеру
uvicorn_logger = logging.getLogger("uvicorn.access")
uvicorn_logger.addFilter(ChromeDevtoolsFilter())

app = FastAPI(title="In Search of Adventures API", default_response_class=JSONResponse)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создаем необходимые директории
for directory in ["static", "templates"]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Инициализация шаблонов
templates = Jinja2Templates(directory="templates")

# Настройка геокодера
geolocator = Nominatim(
    user_agent="adventure-weather-app/1.0",
    timeout=15
)

class CityRequest(BaseModel):
    city: str
    start_date: str = Field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d'))
    end_date: str = Field(default_factory=lambda: (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'))

def get_country_info(country_code: str):
    """Получаем полную информацию о стране по коду страны"""
    try:
        response = requests.get(
            f"https://restcountries.com/v3.1/alpha/{country_code}",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        if data and isinstance(data, list):
            country = data[0]
            
            # Извлекаем валюту
            currencies = country.get('currencies', {})
            currency = list(currencies.values())[0]['name'] if currencies else "Unknown"
            
            # Извлекаем язык
            languages = country.get('languages', {})
            language = list(languages.values())[0] if languages else "Unknown"
            
            # Название страны
            country_name = country.get('name', {}).get('common', 'Unknown')
            
            # Столица
            capital = country.get('capital', ['Unknown'])[0] if country.get('capital') else "Unknown"
            
            # Население с форматированием
            population = country.get('population', 'Unknown')
            if isinstance(population, int):
                population = f"{population:,}"
            
            return {
                "flag": country['flags']['png'],
                "currency": currency,
                "language": language,
                "country_name": country_name,
                "capital": capital,
                "population": population
            }
        return None
    except Exception as e:
        print(f"Country info error: {e}")
        return None

@app.exception_handler(Exception)
async def universal_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )

@app.post("/api/get-weather")
async def get_weather(city_request: CityRequest):
    city = city_request.city
    start_date = city_request.start_date
    end_date = city_request.end_date
    
    try:
        location = geolocator.geocode(city, language="en", addressdetails=True)
        if not location:
            return JSONResponse(
                status_code=404,
                content={"detail": f"City '{city}' not found"},
            )
        
        address = location.raw.get('address', {})
        country_code = address.get('country_code', "").upper()
        
        country_info = {}
        if country_code:
            country_info = get_country_info(country_code) or {}
        
        country_name = country_info.get('country_name', address.get('country', 'Unknown'))
        
        lat, lon = location.latitude, location.longitude

        # Параметры запроса для диапазона дат
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,weather_code",
            "timezone": "auto",
            "start_date": start_date,
            "end_date": end_date
        }

        # Используем прямой запрос к API
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        weather_data = response.json()
        
        # Извлекаем ежедневные данные
        daily = weather_data.get("daily", {})
        dates = daily.get("time", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        weather_codes = daily.get("weather_code", [])
        
        # Формируем прогноз
        forecast = []
        for i in range(len(dates)):
            forecast.append({
                "date": dates[i],
                "max_temp": max_temps[i],
                "min_temp": min_temps[i],
                "weather_code": weather_codes[i]
            })
        
        return {
            "city": city,
            "location": location.address,
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "flag": country_info.get('flag', ''),
            "currency": country_info.get('currency', 'Unknown'),
            "language": country_info.get('language', 'Unknown'),
            "country_name": country_name,
            "capital": country_info.get('capital', 'Unknown'),
            "population": country_info.get('population', 'Unknown'),
            "forecast": forecast
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)},
        )

@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Adventure API is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)