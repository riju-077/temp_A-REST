# How to Read This Project (Objects API)

A step-by-step guide to understand this codebase.

---

## Project Structure

```
Agnik/
├── pyproject.toml       # 1. START HERE - Config & dependencies
├── main.py              # 2. Entry point - App setup
├── routes/              # 3. API endpoints
│   ├── __init__.py
│   └── objects.py
├── schemas/             # 4. Data validation models
│   ├── __init__.py
│   └── object.py
├── data/                # 5. Data storage
│   ├── __init__.py
│   └── store.py
└── README.md            # Test data for endpoints
```

---

## Reading Order (Follow This Exactly)

### Step 1: `pyproject.toml`

**What it tells you:**
- Python 3.12+ project
- Uses FastAPI (web framework)
- Uses uvicorn (server)

**Key lines:**
```toml
dependencies = [
    "fastapi>=0.128.0",
    "uvicorn[standard]>=0.40.0",
]
```

---

### Step 2: `main.py`

**What it tells you:**
- App is named "Objects API"
- Uses `objects_router` from routes folder
- Runs on port 8000 with auto-reload

**Key lines:**
```python
from routes import objects_router
app = FastAPI(title="Objects API", version="1.0.0")
app.include_router(objects_router)
uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
```

**Next question:** What is `objects_router`? → Go to `routes/`

---

### Step 3: `routes/__init__.py`

**What it tells you:**
- Exports `objects_router` from `objects.py`

```python
from .objects import router as objects_router
```

**Next:** Read `routes/objects.py`

---

### Step 4: `routes/objects.py`

**What it tells you:**
- All 7 API endpoints
- All routes start with `/objects`
- Uses schemas for validation
- Uses data store for storage

**Endpoints:**
| Method | Route | Function |
|--------|-------|----------|
| GET | `/objects` | Get all objects |
| GET | `/objects/?id=1&id=2` | Get objects by IDs |
| GET | `/objects/{id}` | Get single object |
| POST | `/objects` | Create object |
| PUT | `/objects/{id}` | Full update |
| PATCH | `/objects/{id}` | Partial update |
| DELETE | `/objects/{id}` | Delete object |

**Key imports:**
```python
from schemas import ObjectCreate, ObjectResponse, ...
from data import objects_db, get_next_id
```

**Next questions:**
- What do schemas look like? → Go to `schemas/`
- What is `objects_db`? → Go to `data/`

---

### Step 5: `schemas/__init__.py`

**What it tells you:**
- Exports all Pydantic models from `object.py`

---

### Step 6: `schemas/object.py`

**What it tells you:**
- Data structure for objects
- Validation rules

**Models:**
| Model | Purpose |
|-------|---------|
| `ObjectCreate` | Input for POST (name, data) |
| `ObjectUpdate` | Input for PUT (name, data) |
| `ObjectPatch` | Input for PATCH (optional name, data) |
| `ObjectResponse` | Output format (id, name, data) |
| `ObjectCreateResponse` | Output with createdAt |
| `ObjectUpdateResponse` | Output with updatedAt |
| `DeleteResponse` | Output with message |

**Object structure:**
```python
{
    "id": "1",              # string
    "name": "Product Name", # string, required
    "data": {...}           # dict or null, optional
}
```

---

### Step 7: `data/__init__.py`

**What it tells you:**
- Exports `objects_db` and `get_next_id`

---

### Step 8: `data/store.py`

**What it tells you:**
- Data is stored in a Python list (in-memory)
- 13 objects pre-loaded
- `get_next_id()` generates new IDs starting from 14

**Key code:**
```python
objects_db: list[dict] = [
    {"id": "1", "name": "Google Pixel 6 Pro", "data": {...}},
    # ... 13 total objects
]
```

---

## How a Request Flows

**Example: `POST /objects` (Create new object)**

```
1. Request hits main.py
         ↓
2. main.py sends to objects_router
         ↓
3. routes/objects.py → create_object() function
         ↓
4. Validates input using schemas/ObjectCreate
         ↓
5. Gets new ID from data/get_next_id()
         ↓
6. Adds to data/objects_db list
         ↓
7. Returns response using schemas/ObjectCreateResponse
```

---

## Quick Reference

| Want to know... | Look at... |
|-----------------|------------|
| Dependencies | `pyproject.toml` |
| How app starts | `main.py` |
| All endpoints | `routes/objects.py` |
| Data structure | `schemas/object.py` |
| Stored data | `data/store.py` |
| Test examples | `README.md` |

---

## To Run the Project

```bash
uv run main.py
```

- Server: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`

---

## Key Takeaways

1. **Config first** (`pyproject.toml`) - Know what tools are used
2. **Entry point** (`main.py`) - See how app is assembled
3. **Follow imports** - They guide you to the next file
4. **Routes** - Show what the API can do
5. **Schemas** - Show what data looks like
6. **Data** - Show where data lives

---

**When in doubt, trace one request from start to finish.**
