from mcp.server.fastmcp import FastMCP
import requests
from typing import Literal

# Initialize MCP
mcp = FastMCP(name="sumo_trading_server")

@mcp.tool()
def get_weather(
    city: str,
    units: Literal["metric", "imperial"] = "metric"
) -> dict:
    """
    Get current weather info for a city.
    """
    url = f"https://wttr.in/{city}?format=j1"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        return {"success": False, "error": str(e)}

    data = response.json()
    current = data["current_condition"][0]

    if units == "metric":
        temp = f"{current['temp_C']}°C"
        feels_like = f"{current['FeelsLikeC']}°C"
    else:
        temp = f"{current['temp_F']}°F"
        feels_like = f"{current['FeelsLikeF']}°F"

    return {
        "success": True,
        "city": city,
        "temperature": temp,
        "feels_like": feels_like,
        "condition": current['weatherDesc'][0]['value'],
        "humidity": f"{current['humidity']}%",
        "wind_speed": f"{current['windspeedKmph']} km/h",
        "wind_direction": current['winddir16Point'],
        "pressure": f"{current['pressure']} mb",
        "visibility": f"{current['visibility']} km",
        "uv_index": current['uvIndex']
    }

if __name__ == "__main__":
    # Run MCP SSE server
    mcp.run(transport="stdio")
