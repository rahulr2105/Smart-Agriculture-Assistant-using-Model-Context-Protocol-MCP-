import json

with open("weather_data.json", "r") as f:
    WEATHER_DATA = json.load(f)


def get_weather(city: str):
    city = city.upper()
    
    return WEATHER_DATA.get(
        city,
        {
            "weather": "Unknown",
            "temperature": "N/A"
        }
    )


def irrigation_advice(weather: str):
    if weather.lower() == "sunny":
        return {"advice": "Water crops today."}

    elif weather.lower() == "rain":
        return {"advice": "Do not irrigate today."}

    elif weather.lower() == "cloudy":
        return {"advice": "Monitor soil moisture before watering."}

    return {"advice": "No recommendation available."}