# Nowarie Realtime

A reusable real-time backend built with **Python, FastAPI, WebSockets, and PostgreSQL**. Nowarie Realtime is designed to provide a shared backend foundation for messaging systems and future real-time applications.

The goal is to build a modular service that can support multiple projects without requiring each project to implement its own real-time communication infrastructure.

## Project Vision

Nowarie Realtime begins as a messaging backend and will gradually evolve into a reusable real-time communication service.

The long-term vision is to support applications such as:

* **Messaging:** Real-time conversations and message delivery.
* **Presence:** Track whether users are online or disconnected.
* **Rooms:** Organize users into conversations or shared spaces.
* **Multiplayer:** Exchange real-time player actions and game events.
* **Shared Infrastructure:** Allow multiple applications to use the same backend.

The initial implementation will focus on reliable WebSocket communication and a foundation that can be extended as requirements grow.

## Technology Stack

| Technology     | Purpose                                         |
| -------------- | ----------------------------------------------- |
| Python         | Backend programming language                    |
| FastAPI        | HTTP API and application framework              |
| WebSockets     | Real-time, bidirectional communication          |
| PostgreSQL     | Persistent application data and message history |
| SQLAlchemy     | Database interaction                            |
| Alembic        | Database schema migrations                      |
| Uvicorn        | ASGI server                                     |
| Pytest         | Automated testing                               |
| GitHub Actions | Continuous integration                          |

## Architecture

The backend is organized into modules so that different real-time features can evolve independently.

```text
Client Applications
        |
        | HTTP / WebSocket
        v
+---------------------------+
|     FastAPI Backend       |
|                           |
|  API Endpoints            |
|  WebSocket Connections    |
|  Messaging Module         |
|  Presence Module          |
|  Rooms Module             |
+---------------------------+
        |
        v
+---------------------------+
|       PostgreSQL          |
|                           |
|  Users and Conversations  |
|  Messages and History     |
|  Persistent Application   |
|  Data                     |
+---------------------------+
```

This is the intended architecture. Components will be implemented incrementally as the project develops.

### Design Principles

* **Modular:** Keep messaging, presence, and room functionality separated.
* **Reusable:** Design the backend to serve multiple client applications.
* **Persistent:** Store messages that users may need to retrieve after disconnecting.
* **Real-time:** Use WebSockets for low-latency, bidirectional communication.
* **Practical:** Start with a small deployment and introduce additional infrastructure only when needed.
* **Testable:** Verify core behavior with automated tests and CI.

## Project Structure

```text
nowarie-realtime/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .scripts/
│   └── ship.ps1
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── modules/
│   │   ├── messaging/
│   │   ├── presence/
│   │   └── rooms/
│   ├── services/
│   ├── websocket/
│   ├── __init__.py
│   └── main.py
├── tests/
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

The structure represents the planned organization. Some directories may remain empty until their corresponding features are implemented.

## Getting Started

### Requirements

* Python 3.12 or a compatible supported Python version
* Git
* PowerShell on Windows, or an equivalent terminal
* PostgreSQL when database integration is introduced

### 1. Clone the Repository

```powershell
git clone <repository-url>
cd nowarie-realtime
```

Replace `<repository-url>` with the repository's Git URL.

### 2. Create a Virtual Environment

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a local `.env` file using `.env.example` as a reference.

```dotenv
APP_NAME=Nowarie Realtime
APP_ENV=development
DATABASE_URL=
```

Database configuration will be completed when PostgreSQL integration is implemented.

**Never commit `.env` or credentials to the repository.**

### 5. Run the Development Server

Once the initial FastAPI application is implemented:

```powershell
python -m uvicorn app.main:app --reload
```

The API documentation will be available at:

```text
http://127.0.0.1:8000/docs
```

## Development Workflow

The project uses a pull-request-based workflow.

1. Start from the latest `main` branch.
2. Create a feature branch.
3. Implement a focused change.
4. Run tests locally.
5. Use `.scripts/ship.ps1` to create a pull request.
6. Let GitHub Actions run CI.
7. Review the pull request and merge when checks pass.

Example:

```powershell
.\.scripts\ship.ps1 "feat: add websocket connection"
```

The script automates branch creation, committing, pushing, pull-request creation, and the merge workflow.

## Roadmap

### Phase 1 — Foundation

* [ ] Initialize the FastAPI application.
* [ ] Add an HTTP health endpoint.
* [ ] Implement a basic WebSocket endpoint.
* [ ] Add automated tests.
* [ ] Configure GitHub Actions CI.

### Phase 2 — Messaging

* [ ] Define the message protocol.
* [ ] Support sending and receiving messages.
* [ ] Design conversations and message persistence.
* [ ] Retrieve message history.
* [ ] Handle disconnected clients.

### Phase 3 — Users and Presence

* [ ] Define user identity and authentication.
* [ ] Track active WebSocket connections.
* [ ] Handle connection and disconnection events.
* [ ] Support conversation or room membership.

### Phase 4 — Reusable Real-Time Infrastructure

* [ ] Define a consistent event protocol.
* [ ] Support multiple client applications.
* [ ] Separate transport handling from application logic.
* [ ] Add authorization and input validation.

### Phase 5 — Multiplayer Support

* [ ] Define player and room events.
* [ ] Support events such as player movement and interaction.
* [ ] Evaluate state synchronization requirements.
* [ ] Integrate with a multiplayer client.

### Phase 6 — Deployment and Reliability

* [ ] Configure production environment variables.
* [ ] Deploy the API.
* [ ] Connect a managed PostgreSQL database.
* [ ] Add logging and operational health checks.
* [ ] Evaluate a message broker if scaling requirements justify it.

## Current Status

**Status:** Initial development.

The project is being built incrementally, beginning with the application foundation and WebSocket communication. Roadmap items are planned work, not claims that the features are already implemented.

## License

A license will be added when the project's distribution and reuse terms are decided.
