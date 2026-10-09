# Firing Simulator Backend Server

Central telemetry, relational data storage, and control service for the Firing Training Simulator.

## Architecture
- **Framework**: FastAPI (Python 3.12+)
- **ORM & DB**: SQLAlchemy 2.0 with SQLite (`Backend/data/firing_sim.db`)
- **WebSockets**:
  - `/ws/console`: Instructor Console real-time event & control stream
  - `/ws/sim`: Unreal Engine simulation state synchronization
- **UDP Ingestion**: Background listener on `UDP 47001` receiving cloned marksmanship telemetry from Tracker.

## REST Endpoints
- `/auth/login`: Instructor login & token generation
- `/trainees`: Trainee registration and lookup
- `/groups`: Trainee squad/batch organization
- `/users`: System operator accounts
- `/weapons`: Weapon definitions (caliber, classification)
- `/guns`: Physical laser weapon units assigned to lanes
- `/targets`: Target geometries and scoring ring dimensions
- `/scoring-patterns`: Point valuation rules
- `/exercises`: Single firing drills
- `/courses`: Multi-stage qualification courses
- `/scenarios/3d`: Unreal virtual range definitions
- `/scenarios/video`: Branching judgmental video scenarios
- `/sessions`: Live marksmanship sessions & lane assignments
- `/reports`: Evaluation templates and performance exports
- `/calibration/screen`: Projector screen 4-point homography
- `/calibration/weapon`: Weapon zeroing offset coordinates
- `/system/health`: System and database operational status
- `/system/licence`: Software licence validity
- `/system/settings`: Global simulator configuration

## Running the Backend

```powershell
# Using the software suite virtual environment:
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive API documentation (Swagger UI) is accessible at:
`http://127.0.0.1:8000/docs`

Health check endpoint:
`http://127.0.0.1:8000/system/health`
