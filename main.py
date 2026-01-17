import uvicorn
from fastapi import FastAPI

from routes import objects_router

app = FastAPI(title="Objects API", version="1.0.0")

app.include_router(objects_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
