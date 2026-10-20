# Nowarie Realtime

A reusable real-time backend built with **Python, FastAPI, WebSockets, and PostgreSQL**. Nowarie Realtime provides a shared foundation for messaging and future real-time applications.

The project starts with room-based WebSocket messaging and will gradually evolve into a reusable real-time service.

## Project Goals

* **Messaging:** Send real-time messages between connected clients.
* **Rooms:** Separate conversations and their participants.
* **Persistence:** Store message history in PostgreSQL.
* **Reusability:** Provide a shared backend for projects such as Love Journey.
* **Extensibility:** Prepare for future features such as online presence and multiplayer events.

## Technology Stack

| Technology     | Purpose                                         |
| -------------- | ----------------------------------------------- |
| Python         | Backend programming language                    |
| FastAPI        | API framework and WebSocket endpoints           |
| WebSockets     | Real-time, bidirectional communication          |
| PostgreSQL     | Persistent application data and message history |
| SQLAlchemy     | Database interaction                            |
| Alembic        | Database schema migrations                      |
| Uvicorn        | ASGI server                                     |
| Pytest         | Automated testing                               |
| GitHub Actions | Continuous integration                          |

Some technologies are planned for upcoming milestones and may not yet be integrated.

## Current Architecture

```text
Client Applications
        |
        | WebSocket
        v
+---------------------------+
|      FastAPI Server       |
|                           |
|  WebSocket Endpoint       |
|  Message Validation       |
|  Server-Generated IDs     |
|  Server-Generated Time    |
+---------------------------+
        |
        v
+---------------------------+
|     ConnectionManager     |
|                           |
|  Active Connections       |
|  Room-Based Broadcasts    |
+---------------------------+
        |
        v
   Connected Clients
```

The current `ConnectionManager` stores active WebSocket connections in memory and broadcasts messages to clients connected to the same room.

This architecture is sufficient for the initial small-scale use case of approximately 2–5 users, assuming low traffic and a single server process.

PostgreSQL will provide persistent message history as database integration is implemented.

### Important Limitations

* Active connections are stored in server memory.
* Restarting the server clears the active connection state.
* Multiple server instances cannot automatically share their WebSocket connections.
* The connection manager does not persist messages.
* Client-supplied message IDs and timestamps are not trusted; the server generates these values.

## Connection Manager

**File:** `app/connection_manager.py`

The connection manager is responsible for tracking WebSocket connections and broadcasting messages within rooms.

```python
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()

        if room_id not in self.active_connections:
            self.active_connections[room_id] = []

        self.active_connections[room_id].append(websocket)

    def disconnection(self, websocket: WebSocket, room_id: str):
        connections = self.active_connections.get(room_id)

        if connections and websocket in connections:
            connections.remove(websocket)

            if not connections:
                del self.active_connections[room_id]

    async def broadcast(self, message: str, room_id: str):
        connections = self.active_connections.get(room_id, [])

        for connection in connections.copy():
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnection(connection, room_id)
```

### Method Responsibilities

| Method            | Responsibility                                                   |
| ----------------- | ---------------------------------------------------------------- |
| `connect()`       | Accepts a WebSocket connection and registers it in a room.       |
| `disconnection()` | Removes a connection and deletes an empty room entry.            |
| `broadcast()`     | Sends a JSON message to connected clients in the specified room. |

The broadcast method iterates over a copy of the connection list so connections can be removed safely during iteration.

**Implementation note:** The `broadcast()` parameter is currently annotated as `str`, although `send_json()` accepts JSON-compatible values, including dictionaries. Consider updating this annotation when refining the implementation.

## Future Development: Redis Pub/Sub

**Status:** Planned. Redis is not currently implemented.

Redis will be considered when the application needs to distribute real-time events across multiple FastAPI server instances.

### Where Redis Will Be Added

The main integration points will be:

* `app/connection_manager.py` — retain responsibility for local WebSocket connections and local broadcasts.
* `app/main.py` — integrate message publishing into the WebSocket message-handling flow.
* A future dedicated Redis service module — manage Redis connections, publishing, and subscriptions.

The intended architecture is:

```text
              Client A                 Client B
                 |                         ^
                 v                         |
            FastAPI A                 FastAPI B
                 |                         ^
                 v                         |
          Local Connections          Local Connections
                 |                         ^
                 v                         |
             Redis Pub/Sub ---------------+
                 |
                 v
          Shared Real-Time Events
```

Conceptually, when a client sends a message to one server, that server publishes the event to Redis. Other server instances subscribe to the event and deliver it to their own connected clients.

The actual implementation must also handle room filtering, event routing, and duplicate-delivery prevention.

### Future Developer Instructions

When implementing Redis:

1. Add a Redis-compatible client dependency.
2. Configure the Redis connection through environment variables.
3. Create a dedicated Redis service module rather than placing all Redis logic inside `ConnectionManager`.
4. Publish validated message events to Redis channels.
5. Subscribe each server instance to relevant events.
6. Deliver received events through each instance's local WebSocket connections.
7. Manage Redis connections and subscription tasks during application startup and shutdown.
8. Add tests for event distribution, room isolation, connection failures, and duplicate delivery.

**Keep Redis separate from PostgreSQL.**

Redis Pub/Sub distributes real-time events but does not retain messages for disconnected subscribers. PostgreSQL should remain responsible for persistent message history. A reconnecting client should retrieve missed messages from persistent storage.

Redis is not necessary for the initial single-server implementation. Documenting this integration point keeps the current system simple while making future scaling easier.

## Getting Started

### Requirements

* Python 3.12 or a compatible supported Python version
* Git
* PowerShell on Windows, or an equivalent terminal

PostgreSQL will be required when database integration is implemented.

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

**Never commit `.env` files or credentials to the repository.**

### 5. Run the Development Server

From the project root:

```powershell
python -m uvicorn app.main:app --reload
```

Open the API documentation at:

`http://127.0.0.1:8000/docs`

## Testing

Run the complete test suite with coverage:

```powershell
python -m pytest --cov=app --cov-report=term-missing -v
```

This command runs the tests with verbose output and reports application code coverage, including lines that were not executed.

Review failed tests and uncovered lines before shipping a change.

## Development Workflow

The project uses a pull-request-based workflow.

1. Start from the latest `main` branch.
2. Make sure the working tree contains only the intended changes.
3. Use the shipping script to create a feature branch and pull request.
4. Review the staged files and commit.
5. Allow GitHub Actions to run CI.
6. Review and merge the pull request after checks pass.

### Ship a Feature

The current server-generated message IDs milestone uses:

```powershell
.scripts\ship "feat: add server-generated message IDs"
```

The script automates branch creation, committing, pushing, pull-request creation, CI checks, and the merge workflow.

**Important:** The script stages changes using `git add .`. Inspect the staged files and ensure unrelated changes are not included before allowing the workflow to continue.

## Roadmap

### Phase 1 — WebSocket Foundation

* [x] Initialize the FastAPI application.
* [x] Add an HTTP health endpoint.
* [x] Implement a WebSocket endpoint.
* [x] Implement room-based connection management.
* [x] Add automated tests and CI.

### Phase 2 — Messaging

* [x] Define an incoming message schema.
* [x] Validate incoming messages.
* [x] Generate message timestamps on the server.
* [x] Generate unique message IDs on the server.
* [x] Broadcast messages within a room.
* [ ] Implement PostgreSQL message persistence.
* [ ] Retrieve message history.

### Phase 3 — Identity and Reliability

* [ ] Implement authentication and trusted user identity.
* [ ] Authorize room membership.
* [ ] Improve connection lifecycle and error handling.
* [ ] Handle reconnecting clients and missed messages.

### Phase 4 — Shared Real-Time Infrastructure

* [ ] Separate messaging logic from transport handling where appropriate.
* [ ] Introduce Redis Pub/Sub when cross-instance event distribution is needed.
* [ ] Add online presence and typing indicators if required.

### Phase 5 — Deployment

* [ ] Configure production environment variables.
* [ ] Deploy the API.
* [ ] Connect persistent PostgreSQL storage.
* [ ] Add operational logging and monitoring.
* [ ] Evaluate hosting costs and reliability before production use.

## Current Status

**Status:** Initial real-time messaging implementation.

The project currently focuses on room-based WebSocket communication, message validation, server-generated message IDs and timestamps, and automated testing.

PostgreSQL persistence and Redis integration remain future milestones.

## License

A license will be added when the project's distribution and reuse terms are decided.
