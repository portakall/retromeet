# RetroMeet

RetroMeet is an AI-powered retrospective meeting platform that collects participant responses via chat, refines them using advanced agents, and generates lip-synced avatar videos for engaging playback.

---

## Features

- Collects responses from meeting participants via a Gradio chat interface
- Refines and tunes responses using multiple AI agents
- Stores participant responses in a database, with customizable avatars
- Modern frontend for viewing responses and generated videos

---

## Backend Setup

1. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2. **Set up environment variables:**
    - Copy `.env.example` to [.env](cci:7://file:///Users/mirror/WindSurf%20Projects/retromeet_project/.env:0:0-0:0) and fill in required values (DB connection, API keys, etc.)

3. **Run the backend server:**
    ```bash
    python backend/main.py
    ```

4. **Access API docs:**  
   Visit [http://localhost:8000/docs](http://localhost:8000/docs) for interactive API documentation.

---

## Frontend Setup

1. **Navigate to the frontend directory:**
    ```bash
    cd frontend/react-admin
    ```

2. **Install dependencies:**
    ```bash
    npm install
    ```
    or
    ```bash
    yarn install
    ```

3. **Start the frontend development server:**
    ```bash
    npm start
    ```
    or
    ```bash
    yarn start
    ```

4. **Access the frontend:**  
   Visit [http://localhost:3000](http://localhost:3000)

---

## Usage

- Open the frontend in your browser to view and manage retrospectives.
- Use the Gradio chat interface to collect responses from participants.
- View generated summaries in the frontend dashboard.

---

## Development Notes

- All dependencies (Python and Node.js) are excluded from version control.  
  Please run the appropriate install commands before starting development.
- Environment variables and secrets should be stored in the [.env](cci:7://file:///Users/mirror/WindSurf%20Projects/retromeet_project/.env:0:0-0:0) file (not tracked).
- For database migrations, see [backend/migrate_db.py](cci:7://file:///Users/mirror/WindSurf%20Projects/retromeet_project/backend/migrate_db.py:0:0-0:0).

---

## License

[MIT](LICENSE)

---

## Acknowledgements

- [Gradio](https://gradio.app/) for chat interface
- [FastAPI](https://fastapi.tiangolo.com/) for backend

---
