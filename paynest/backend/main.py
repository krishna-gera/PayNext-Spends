from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from analytics import router as analytics_router
from auth import router as auth_router
from expenses import router as expenses_router
from groups import router as groups_router
from settlements import router as settlements_router

app = FastAPI(title="PayNest API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "PayNest backend running"}


app.include_router(auth_router)
app.include_router(groups_router)
app.include_router(expenses_router)
app.include_router(settlements_router)
app.include_router(analytics_router)
