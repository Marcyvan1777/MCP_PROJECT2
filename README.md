# Travel Assistant MCP Server

The Travel Assistant is a Model Context Protocol (MCP) server built with Python and `FastMCP`. It provides a large language model with real-time tools to plan and budget travel itineraries. The assistant can fetch live flight and hotel data, track a trip budget,  and recommend local landmarks securely.

## Features & Available Tools

This server exposes several capabilities to the LLM (`server3.py`):

* **Flights:** `check_flight_prices(origin, destination, date, adults)` - Fetches live flight offers and prices using the Amadeus API (requires 3-letter IATA city codes).
* **Hotels:** 
  * `check_hotel(cityCode)` - Retrieves a list of available hotels and their `hotelIds` in a specific city.
  * `check_hotel_prices(hotelIds, adults)` - Retrieves live room availability and pricing for a specific Hotel ID.
* **Budget Management:** 
  * `set_budget(amount)` and `get_budget()` - Keeps track of the user's total spending capacity for the trip.
  * `validate_booking(price)` - A capability fence that prevents the AI from finalizing or proposing bookings that exceed the remaining budget.
* **Local Info:**
  * `recommend_sites(destination)` - Gathers landmark and sightseeing recommendations using Wikipedia data.

## Setup & Configuration

1. **Environment Variables:**
   The server requires real-time API keys to function. Create a `.env` file in the root `my-mcp-server` directory:
   ```env
   AMADEUS_API_KEY=your_amadeus_api_key
   AMADEUS_API_SECRET=your_amadeus_api_secret
   ```
   *(Note: The `.env` file is gitignored to protect your credentials).*

2. **Dependencies:**
   Ensure you have the required Python packages installed in your virtual environment:
   ```bash
   pip install fastmcp requests python-dotenv amadeus wikipedia
   ```

## Using with Gemini CLI

To use this Travel Assistant through the Gemini CLI, you need to configure the MCP server in your system settings and apply the strict agent prompt.

1. **Configure the MCP Server:**
   Add `server3.py` to your Gemini CLI `settings.json` file under `mcpServers`. Make sure to provide the absolute path to your Python virtual environment executable and the server script:
   ```json
   "mcpServers": {
     "travel-server": {
       "command": "C:\\path\\to\\my-mcp-server\\.venv\\Scripts\\python.exe",
       "args": [
         "C:\\path\\to\\my-mcp-server\\server3.py"
       ]
     }
   }
   ```

2. **System Prompt & Guardrails:**
   For the best and safest experience, provide the AI with the system prompt found in `system_prompt/sys_prompt.md`. This document instructs the LLM on exactly how to behave (e.g., using IATA codes, chaining the city code tool with the hotel ID tool natively, and validating the budget).

3. **Start the Conversation:**
   Run the Gemini CLI in your terminal:
   ```bash
   gemini
   ```
   You can now start asking the assistant to plan your trip! For example:
   * *"I have a budget of $3000. Find me a flight from Paris (PAR) to Athens (ATH) for next Friday,  recommend some hotels!"*
