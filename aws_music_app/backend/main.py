# ./backend/module/user_api.py
from fastapi import FastAPI
from module.user_api.user_api import router as user_api_router
from module.music_api.music_api import router as music_api_router

app = FastAPI(title="User Management API", version="1.0")

# Include the router from user_api module
app.include_router(user_api_router)
app.include_router(music_api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
    
# uvicorn main:app --reload --host 0.0.0.0 --port 8000
