import os
import shutil
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import List, Optional

from backend.database import engine, get_db, User, QueryHistory, ViolationReport, init_db
from backend.ai.pipeline import generate_ai_response
from backend.processing.document_processor import process_document
from backend.processing.aa_processor import process_aa_consent
from sqlalchemy import func

# Initialize models
init_db()

app = FastAPI(title="ComplianceHub AI & Legal Assistant API")

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydantic models for request validation
class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class QueryRequest(BaseModel):
    query: str
    domain: str  # 'law', 'banks', 'irdai'
    user_id: int = 0

class QueryResponse(BaseModel):
    response: str
    
class HistoryItem(BaseModel):
    query_text: str
    domain: str
    response: str
    timestamp: str

class AARequest(BaseModel):
    phone_number: str
    user_id: int

# Helper functions for password hashing
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# --- Routes ---

@app.post("/api/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    hashed_pwd = get_password_hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully", "user_id": new_user.id}

@app.post("/api/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    return {"message": "Login successful", "user_id": db_user.id, "username": db_user.username}

@app.post("/api/query_ai", response_model=QueryResponse)
def query_ai(request: QueryRequest, db: Session = Depends(get_db)):
    # 1. Fetch AI response
    try:
        ai_response = generate_ai_response(request.query, request.domain)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # 2. Save to history
    history_entry = QueryHistory(
        user_id=request.user_id,
        query_text=request.query,
        domain=request.domain,
        response=ai_response
    )
    db.add(history_entry)
    db.commit()
    
    return {"response": ai_response}

@app.get("/api/history/{user_id}")
def get_user_history(user_id: int, db: Session = Depends(get_db)):
    if user_id == 0:
        return [] # Guest has no remote history
    history = db.query(QueryHistory).filter(QueryHistory.user_id == user_id).order_by(QueryHistory.timestamp.desc()).limit(20).all()
    return [{
        "query_text": h.query_text,
        "domain": h.domain,
        "response": h.response,
        "timestamp": str(h.timestamp)
    } for h in history]

@app.post("/api/upload_document", status_code=status.HTTP_202_ACCEPTED)
def upload_document(
    background_tasks: BackgroundTasks,
    category: str = Form(...), # 'law', 'banks', 'irdai'
    file: UploadFile = File(...)
):
    # Setup temp upload directory
    upload_dir = "temp_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    temp_path = os.path.join(upload_dir, file.filename)
    
    try:
        # Save file securely for background processor
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Push process to background
        background_tasks.add_task(process_document, temp_path, category)
        
        return {"message": f"Document {file.filename} is being processed asynchronously into {category}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/aa/fetch")
def fetch_aa_compliance(request: AARequest):
    try:
        result = process_aa_consent(request.phone_number, request.user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/heatmap_stats")
def get_heatmap_stats(db: Session = Depends(get_db)):
    # Group violations by state to mimic a geographic heatmap
    stats = db.query(
        ViolationReport.location_state, 
        func.count(ViolationReport.id).label('count')
    ).group_by(ViolationReport.location_state).all()
    
    # Also get recent 10 violations for a feed
    recent = db.query(ViolationReport).order_by(ViolationReport.timestamp.desc()).limit(10).all()
    
    heatmap_data = [{"state": s.location_state, "count": s.count} for s in stats]
    feed_data = [{"bank": r.bank_name, "type": r.violation_type, "state": r.location_state, "timestamp": str(r.timestamp)} for r in recent]
    
    return {"heatmap": heatmap_data, "recent_violations": feed_data}
