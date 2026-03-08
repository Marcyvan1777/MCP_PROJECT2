from fastmcp import FastMCP
import os
import requests
import json
import urllib.parse
from datetime import datetime
from dotenv import load_dotenv
from amadeus import Client, ResponseError
import wikipedia 
import random


# Load environment variables from .env file
load_dotenv()

# Initialize the server
mcp = FastMCP("travel-server")

# Global state for budget tracking
budget_state = {
    "remaining_budget": 0.0
}

@mcp.tool()
def check_flight_prices(origin: str, destination: str, date: str, adults: int) -> str:
    """Check flight prices. Requires AMADEUS_API_KEY environment variable.
    for the origin and destination args you should use the city code iota
    example Paris is PAR and Dubai is DXB"""
    api_key = os.environ.get("AMADEUS_API_KEY")
    api_secret = os.environ.get("AMADEUS_API_SECRET")
    
    if not api_key or not api_secret:
        return (f"[API KEY MISSING] To get Amadeus flight data from {origin} to {destination} on {date}, "
                f"you must provide an Amadeus token via the 'AMADEUS_API_KEY' environment variable.\n"
                f"How to use: Set AMADEUS_API_KEY to your real Amadeus Bearer token.")

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    ]
    amadeus = Client(
        client_id=api_key,
        client_secret=api_secret,
        custom_app_id="TravelBot",
        custom_app_version="1.0"
    )
    amadeus.http.headers = {"User-Agent": random.choice(user_agents)}
       
    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=date,
            adults=adults).data
            
        results = []
        for flight in response:
            flight_id = flight.get('id')
            price_info = flight.get('price', {})
            total_price = price_info.get('total')
            currency = price_info.get('currency')
            results.append(f"Flight ID {flight_id}: {total_price} {currency}")
            
        if not results:
            return f"No flight offers found for {origin} -> {destination} on {date}"
            
        return "\n".join(results)
    except ResponseError as error:
        return f"Amadeus Error: {error}"

@mcp.tool()
def check_hotel(cityCode: str ) -> str:
    """Get list of hotels by city code. Requires AMADEUS_API_KEY environment variable."""
    api_key = os.environ.get("AMADEUS_API_KEY")
    api_secret = os.environ.get("AMADEUS_API_SECRET")
    
    if not api_key or not api_secret:
        return "[API KEY MISSING] You must provide the AMADEUS_API_KEY and AMADEUS_API_SECRET."

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    ]
    amadeus = Client(
        client_id=api_key,
        client_secret=api_secret,
        custom_app_id="TravelBot",
        custom_app_version="1.0"
    )
    amadeus.http.headers = {"User-Agent": random.choice(user_agents)}
       
    try:
        response = amadeus.reference_data.locations.hotels.by_city.get(cityCode=cityCode).data
        
        if not response:
            return f"No hotels found in {cityCode}"
            
        results = [f"Found hotels in {cityCode}:"]
        # Limit to 10 hotels to avoid a massive text block
        for hotel in response[:10]:
            name = hotel.get('name', 'Unknown Name')
            hotelId = hotel.get('hotelId', 'Unknown ID')
            results.append(f"Hotel: {name} (ID: {hotelId})")
                
        return "\n".join(results)

    except ResponseError as error:
        return f"Amadeus Error: {error}"

@mcp.tool()
def check_hotel_prices(hotelIds: str, adults: int = 2) -> str:
    """Check hotel prices by hotel ID. Requires AMADEUS_API_KEY environment variable.
    IMPORTANT: You must first call `check_hotel(cityCode)` to get a valid `hotelIds` string before using this tool."""
    api_key = os.environ.get("AMADEUS_API_KEY")
    api_secret = os.environ.get("AMADEUS_API_SECRET")
    
    if not api_key or not api_secret:
        return "[API KEY MISSING] You must provide the AMADEUS_API_KEY and AMADEUS_API_SECRET."

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    ]
    amadeus = Client(
        client_id=api_key,
        client_secret=api_secret,
        custom_app_id="TravelBot",
        custom_app_version="1.0"
    )
    amadeus.http.headers = {"User-Agent": random.choice(user_agents)}
       
    try:
        response = amadeus.shopping.hotel_offers_search.get(hotelIds=hotelIds, adults=str(adults)).data
        
        if not response:
            return f"No rooms available or data found for hotelIds={hotelIds}"
            
        results = [f"Found hotel offers for {hotelIds}"]
        for offer in response:
            for room in offer.get("offers", []):
                price = room.get("price", {}).get("total")
                currency = room.get("price", {}).get("currency")
                roomId = room.get("id")
                results.append(f"Room {roomId}: {price} {currency}")
                
        return "\n".join(results)

    except ResponseError as error:
        return f"Amadeus Error: {error}"

@mcp.tool()
def set_budget(amount: float) -> str:
    """Budget tracker: set up how much money you have for the trip."""
    budget_state["remaining_budget"] = amount
    return f"Budget successfully set to ${amount}"

@mcp.tool()
def get_budget() -> float:
    """Budget tracker: retrieve remaining budget float."""
    return budget_state["remaining_budget"]


@mcp.tool()
def validate_booking(price: float) -> str:
    """Capability Fencing tool. If the price is over the remaining budget, returns an error."""
    if price > budget_state["remaining_budget"]:
        return f"Error: Booking price (${price}) exceeds remaining budget (${budget_state['remaining_budget']:.2f}). Please find a cheaper alternative."
    
    # Deduct from budget on success
    budget_state["remaining_budget"] -= price
    return f"Booking valid! ${price} deducted. Remaining budget: ${budget_state['remaining_budget']:.2f}"


@mcp.tool()
def recommend_sites(destination: str) -> str:
    """Recommend sites to visit based on real Wikipedia search data."""
    try:
        user_agents = [
            "TravelBot/1.0 (travel@example.com)",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15"
        ]
        wikipedia.set_user_agent(random.choice(user_agents))
        query = f"landmarks in {destination}"
        return wikipedia.summary(query)
    except Exception as e:
        return f"Error fetching sites: {str(e)}"

# --- Resources ---

@mcp.resource("info://server")
def server_info() -> str:
    """Server metadata and version information."""
    return json.dumps({
        "name": "travel-server-v3",
        "version": "3.0.0",
        "tools": [
            "check_flight_prices",
            "check_hotel",
            "check_hotel_prices",
            "set_budget",
            "get_budget",
            "validate_booking",
            "recommend_sites"
        ],
    })

if __name__ == "__main__":
    mcp.run()
