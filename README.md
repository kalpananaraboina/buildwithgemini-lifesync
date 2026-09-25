# LifeSync: Precision Wellness & Lifestyle Coach

LifeSync is an intelligent agentic wellness coach designed for busy professionals. It combines clinical nutrition formulas, express desk resets, smart pantry meal rescues, sandboxed Python code execution, and cross-session memory to help knowledge workers balance demanding work hours with consistent vitality.

Built with Google Agent Development Kit (ADK) and Google Agents CLI for the **Build with Gemini** challenge.

---

## ✨ Features Wired & Active

- 🧘 **Express Workouts & Firestore Logs**:
  - `search_workouts`: Filter workouts by duration (5-min desk stretch, 15-min mobility, 30-min strength) and muscle focus.
  - `log_workout`, `add_workout`, `get_workout`: Persists user fitness logs in Firestore.
- 📊 **Clinical Nutrition & Macro Engine**:
  - `calculate_tdee_and_macros`: Computes BMR, TDEE, Calorie Targets, and Macro grams (protein, carbs, fat, hydration) using the Mifflin-St Jeor equation.
- 🍳 **Fridge Rescue Recipe Rescuer**:
  - `fridge_rescue_recipe`: Generates instant 10-minute high-protein meals tailored to user macros from 2–3 on-hand pantry ingredients.
- 🎨 **Vertex AI Image Generation**:
  - `generate_domain_image`: Generates appetizing meal presentation visuals or stretch posture guides using `gemini-3.1-flash-lite-image` in the `global` region, streams bytes to Cloud Storage (`https://storage.googleapis.com/...`), and embeds images into A2UI cards.
- 🗺️ **Google Maps Platform Integration**:
  - `geocode_address`: Converts addresses or location names to coordinates via Google Maps Geocoding API.
  - `search_nearby_places`: Discovers nearby wellness hubs (gyms, healthy dining, parks) using the Google Places API (New).
- 🧠 **Cross-Session Long-Term Memory**:
  - Integrates `PreloadMemoryTool` to inject recalled preferences at turn start and `generate_memories_callback` to store durable user facts across sessions via Vertex AI Memory Bank.
- ⚡ **Agent Platform Sandboxed Code Execution**:
  - Employs `AgentEngineSandboxCodeExecutor` to safely execute Python code in a Vertex AI Agent Engine sandbox environment for advanced calculations, simulations, and data modeling.
- 🎴 **Rich A2UI Card & Table UI**:
  - Natively outputs A2UI (v0.8) display components (Cards, Columns, Rows, Texts, and Images) rendered directly in the chat interface.
- 🌐 **Dedicated Web Frontend**:
  - Full-stack FastAPI proxy talking the A2A protocol to the agent with a custom, sleek glassmorphism chat interface, speech-to-text voice input, hydration tracker, and quick suggestion chips.

---

## 🏗️ Project Architecture

```
lifesync/
├── app/
│   ├── agent.py                 # Core agent definition, prompts, tools, memory & callbacks
│   ├── a2ui_utils.py            # A2UI response formatter callback
│   ├── firestore_db.py          # Firestore database integration for workouts & logs
│   ├── nutrition_calculator.py  # Mifflin-St Jeor TDEE & macro computation
│   ├── recipe_rescuer.py        # Pantry ingredient recipe synthesis
│   ├── image_generator.py       # Vertex AI image generation & GCS upload
│   └── maps_service.py          # Google Maps Geocoding & Places API (New)
├── frontend/
│   ├── main.py                  # FastAPI server & A2A protocol gateway
│   ├── static/
│   │   ├── index.html           # Modern glassmorphism chat UI with A2UI renderer
│   │   └── app.js               # Client-side messaging, speech recognition & state
│   └── run.sh                   # Frontend launcher script
├── tests/
│   └── unit/                    # Unit tests for tools, maps, images, and code executor
├── deployment_metadata.json     # Remote runtime, engine, and sandbox identifiers
└── pyproject.toml               # Python package configuration & dependencies
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- `uv` package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Google Cloud SDK (`gcloud`) authenticated with a project having Vertex AI enabled

### Installation

1. Clone this repository:
   ```bash
   git clone <your-repo-url>
   cd <repo-folder>
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Configure environment variables in `.env`:
   ```bash
   GOOGLE_GENAI_USE_VERTEXAI=true
   GOOGLE_CLOUD_PROJECT=<your-gcp-project-id>
   GOOGLE_CLOUD_LOCATION=global
   GCS_BUCKET_NAME=<your-public-assets-bucket>
   GOOGLE_MAPS_API_KEY=<your-google-maps-api-key>
   ```

### Running Locally

1. **Launch the Agent Playground**:
   ```bash
   agents-cli playground --host 0.0.0.0 --port 8080
   ```

2. **Launch the Custom Frontend**:
   ```bash
   cd frontend
   ./run.sh
   ```
   Open `http://localhost:8081` in your browser.

### Running Tests

```bash
uv run pytest tests/unit
```
