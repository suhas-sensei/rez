# GEMINI.md

## Project Overview

This project is a simulation-based AI trading agent. It uses real-time market data from TAAPI to make trading decisions using AI models, with performance visualization through a simple GUI. The agent can use various LLMs (like OpenAI's GPT models or local models via Ollama) for decision-making. It also features a fallback mechanism that uses Python quantitative analysis libraries (`pandas-ta`, `ta`) when LLM services are unavailable. The project includes an advanced risk management system that allows for trading with customizable risk profiles (low, medium, high) and dynamic asset selection.

The project is structured as a Python application with a command-line interface to run the trading agent and a web-based GUI (built with Streamlit) to visualize the results.

## Building and Running

### Prerequisites

*   Python 3.8+
*   TAAPI.io API Key
*   Access to an LLM (OpenAI API key or a local LLM running with Ollama)

### Setup

1.  **Create and activate a virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

2.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure environment variables:**

    Copy the `.env.example` file to `.env` and fill in your API keys and other settings:

    ```bash
    cp .env.example .env
    ```

    Edit the `.env` file with your `TAAPI_API_KEY`, `LLM_API_KEY`, `LLM_BASE_URL`, and `LLM_MODEL`.

### Running the Agent

*   **Run the trading agent:**

    ```bash
    python src/main.py
    ```

    You can also run the agent with various command-line arguments to customize the assets, interval, starting funds, and risk profile. For example:

    ```bash
    python src/main.py --risk-profile high --assets SOL ARB LINK DOGE APT PEPE --starting-funds 1000
    ```

*   **Run the GUI:**

    While the agent is running, open a new terminal, activate the virtual environment, and run:

    ```bash
    streamlit run src/gui.py
    ```

## Development Conventions

*   **Code Style:** The project appears to follow the PEP 8 style guide for Python code.
*   **Testing:** The project has a `tests` directory, suggesting that it has unit tests. The `pyproject.toml` file lists `pytest` as a dev dependency, so tests can likely be run with the `pytest` command.
*   **Dependencies:** Project dependencies are managed in `requirements.txt` and `pyproject.toml`.
*   **Modularity:** The code is organized into modules for different functionalities, such as `agent`, `indicators`, `risk_management`, and `trading`. This separation of concerns makes the code easier to understand and maintain.
*   **Configuration:** The project uses a `.env` file for configuration, which is loaded by the `config_loader.py` module. This is a good practice for keeping sensitive information out of the code.
*   **Entry Point:** The main entry point of the application is `src/main.py`, which can be run as a script or as a command-line tool using the `hypeai-sim` command.
