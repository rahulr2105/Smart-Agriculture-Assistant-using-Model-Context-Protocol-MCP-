# Smart Agriculture Assistant using Model Context Protocol (MCP)

An AI-powered agricultural advisory system that integrates multiple specialized Model Context Protocol (MCP) servers with a centralized host server and a modern React web dashboard. The assistant helps farmers and advisors make informed decisions on crop selection, disease diagnosis, market pricing, and weather conditions.

---

## 📂 Repository Structure

The project has been organized into modular components. The host integration code and user interface reside in the `Host/` directory, while individual agricultural modules run as standalone MCP servers.

*   **[Host/](file:///d:/mcp-host/Host/)**: The orchestration layer.
    *   **[Host/server.py](file:///d:/mcp-host/Host/server.py)**: A FastAPI supervisor agent that communicates with the MCP servers and exposes endpoints to the frontend.
    *   **[Host/host.py](file:///d:/mcp-host/Host/host.py)**: A CLI client to test MCP tools interactively.
    *   **[Host/config.py](file:///d:/mcp-host/Host/config.py)**: Network configuration mapping the addresses of downstream MCP servers.
    *   **[Host/frontend/](file:///d:/mcp-host/Host/frontend)**: A React & Vite dashboard for an intuitive user experience.
*   **[crop-mcp/](file:///d:/mcp-host/crop-mcp/)**: MCP server providing crop recommendation and soil suitability tools.
*   **[disease_mcp/](file:///d:/mcp-host/disease_mcp/)**: MCP server focusing on plant disease identification and remedies.
*   **[market_mcp/](file:///d:/mcp-host/market_mcp/)**: MCP server serving mandi prices, market trends, and government schemes.

---

## 🚀 Getting Started

### 1. Run the MCP Servers
Each MCP server runs as a standalone microservice using HTTP transport. 

For each module, navigate to its directory, activate a virtual environment, install its dependencies, and start the server:

#### Crop Advisor Server
```bash
cd crop-mcp
python -m venv venv
venv\Scripts\activate     # On Windows
source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt
python server.py
```
*Runs on `http://localhost:8001`*

#### Disease Diagnosis Server
```bash
cd disease_mcp
python -m venv venv
venv\Scripts\activate     # On Windows
source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt
python server.py
```
*Runs on `http://localhost:8002`*

#### Market Pricing & Schemes Server
```bash
cd market_mcp
python -m venv venv
venv\Scripts\activate     # On Windows
source venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt
python server.py
```
*Runs on `http://localhost:8004`*

---

### 2. Configure and Run the Host Backend

The Host Backend bridges the LLM (OpenAI) with the running MCP servers to act as an agentic supervisor.

1.  Navigate to the `Host` directory:
    ```bash
    cd Host
    ```
2.  Set up the Python virtual environment and install dependencies:
    ```bash
    python -m venv venv
    venv\Scripts\activate     # On Windows
    source venv/bin/activate  # On macOS/Linux
    pip install -r requirements.txt
    ```
3.  Configure the environment:
    Create a file named `.env` in the `Host/` directory and configure your API keys:
    ```env
    OPENAI_API_KEY=your_openai_api_key_here
    ```
4.  Configure MCP Server Connections:
    Verify the HTTP endpoints of your running MCP servers in **[Host/config.py](file:///d:/mcp-host/Host/config.py)**:
    ```python
    SERVERS = {
        "mcpServers": {
            "crop": {"transport": "http", "url": "http://localhost:8001/mcp"},
            "disease": {"transport": "http", "url": "http://localhost:8002/mcp"},
            "weather": {"transport": "http", "url": "http://localhost:8003/mcp"},
            "market": {"transport": "http", "url": "http://localhost:8004/mcp"}
        }
    }
    ```
5.  Start the FastAPI Server:
    ```bash
    uvicorn server:app --reload --port 8000
    ```

---

### 3. Run the Frontend Dashboard

1.  Navigate to the frontend directory:
    ```bash
    cd Host/frontend
    ```
2.  Install packages and run the development server:
    ```bash
    npm install
    npm run dev
    ```
3.  Access the web dashboard in your browser (usually `http://localhost:5173`).

---

## 🛠️ Verification & CLI Client

To verify your MCP connections via terminal without running the React UI, you can use the interactive CLI tool:
```bash
cd Host
python host.py
```
This CLI lists all active tools registered in the FastMCP client and allows you to run calls directly against them.