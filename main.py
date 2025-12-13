from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import sqlite3
from datetime import datetime
import jwt
import bcrypt
import json

# Configuration
SECRET_KEY = "your-super-secret-key-2024"
ALGORITHM = "HS256"

app = FastAPI(title="Aspect-Based Sentiment Analysis API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database
def get_db():
    conn = sqlite3.connect('reviews.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            review_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS aspects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id INTEGER NOT NULL,
            aspect TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            confidence REAL NOT NULL,
            keywords TEXT,
            corrected_sentiment TEXT,
            is_corrected INTEGER DEFAULT 0,
            correction_notes TEXT,
            corrected_at TIMESTAMP,
            FOREIGN KEY (review_id) REFERENCES reviews (id)
        )
    ''')
    
    # Models table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            version TEXT,
            path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Active learning corrections table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_learning_corrections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aspect_id INTEGER NOT NULL,
            original_sentiment TEXT NOT NULL,
            corrected_sentiment TEXT NOT NULL,
            confidence REAL NOT NULL,
            review_text TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            corrected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            used_for_training INTEGER DEFAULT 0,
            FOREIGN KEY (aspect_id) REFERENCES aspects (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Ensure dynamic migrations for new columns
    # Users table migrations
    cursor.execute('PRAGMA table_info(users)')
    user_cols = {row[1] for row in cursor.fetchall()}
    if 'role' not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'")

    # Seed a default admin account if none exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
    if cursor.fetchone()[0] == 0:
        import bcrypt
        default_admin_user = 'admin'
        default_admin_email = 'admin@example.com'
        default_admin_pass = 'Admin@123'
        password_hash = bcrypt.hashpw(default_admin_pass.encode(), bcrypt.gensalt()).decode('utf-8')
        cursor.execute("INSERT OR IGNORE INTO users (username, email, full_name, password_hash, role) VALUES (?, ?, ?, ?, 'admin')", 
                       (default_admin_user, default_admin_email, 'Administrator', password_hash))
        print("\n[INFO] Default admin account created: username='admin' password='Admin@123'")

    # Aspects table migrations
    cursor.execute('PRAGMA table_info(aspects)')
    cols = {row[1] for row in cursor.fetchall()}
    if 'keywords' not in cols:
        cursor.execute('ALTER TABLE aspects ADD COLUMN keywords TEXT')
    if 'corrected_sentiment' not in cols:
        cursor.execute('ALTER TABLE aspects ADD COLUMN corrected_sentiment TEXT')
    if 'is_corrected' not in cols:
        cursor.execute('ALTER TABLE aspects ADD COLUMN is_corrected INTEGER DEFAULT 0')
    if 'correction_notes' not in cols:
        cursor.execute('ALTER TABLE aspects ADD COLUMN correction_notes TEXT')
    if 'corrected_at' not in cols:
        cursor.execute('ALTER TABLE aspects ADD COLUMN corrected_at TIMESTAMP')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

init_db()

# Load ABSA Engine
def get_absa_engine():
    from absa_engine import absa_engine
    return absa_engine

# Models
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class ReviewSubmit(BaseModel):
    review_text: str

class BatchAnalyze(BaseModel):
    reviews: List[str]

class CorrectionUpdate(BaseModel):
    aspect_id: Optional[int] = None
    prediction_id: Optional[int] = None
    corrected_sentiment: str
    notes: Optional[str] = None

class BulkCorrection(BaseModel):
    corrections: List[Dict[str, Any]]

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

# Auth helpers
def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain: str, hashed) -> bool:
    plain_bytes = plain.encode('utf-8')[:72]
    # Handle both string and bytes for hashed password
    if isinstance(hashed, bytes):
        hashed_bytes = hashed
    else:
        hashed_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(plain_bytes, hashed_bytes)

def create_token(user_id: int, username: str, role: str) -> str:
    from datetime import datetime, timedelta
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    return verify_token(token)

# Admin dependency

def is_admin(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Routes

@app.get("/admin/summary")
async def admin_summary(current_user: dict = Depends(is_admin)):
    """Return key metrics for the admin dashboard"""
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM reviews")
        total_reviews = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM aspects")
        total_aspects = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM models")
        models_count = cursor.fetchone()[0]

        # Aspect ratio calculation
        cursor.execute("SELECT sentiment, COUNT(*) as cnt FROM aspects GROUP BY sentiment")
        rows = cursor.fetchall()
        aspect_ratio = {row[0]: row[1] for row in rows}

        return {
            "total_users": total_users,
            "total_reviews": total_reviews,
            "total_aspects": total_aspects,
            "models_count": models_count,
            "aspect_ratio": aspect_ratio
        }
    finally:
        conn.close()
@app.post("/register")
async def register(user: UserRegister):
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", 
                      (user.username, user.email))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username or email already exists")
        
        hashed = hash_password(user.password)
        # Determine if there is already an admin; if none, first user becomes admin automatically
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_count = cursor.fetchone()[0]
        assigned_role = 'admin' if admin_count == 0 else 'user'

        cursor.execute(
            "INSERT INTO users (username, email, full_name, password_hash, role) VALUES (?, ?, ?, ?, ?)",
            (user.username, user.email, user.full_name, hashed, assigned_role)
        )
        user_id = cursor.lastrowid
        conn.commit()
        
        token = create_token(user_id, user.username, assigned_role)
        return {
            "token": token,
            "user_id": user_id,
            "username": user.username,
            "role": assigned_role,
            "message": "Registration successful"
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/login")
async def login(user: UserLogin):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", 
                      (user.username,))
        db_user = cursor.fetchone()
        
        if not db_user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        if not verify_password(user.password, db_user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        token = create_token(db_user['id'], db_user['username'], db_user['role'])
        return {
            "token": token,
            "user_id": db_user['id'],
            "username": db_user['username'],
            "role": db_user['role'],
            "message": "Login successful"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn:
            conn.close()

@app.post("/admin/login")
async def admin_login(user: UserLogin):
    """Admin login endpoint"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username = ? AND role = 'admin'", 
                      (user.username,))
        db_user = cursor.fetchone()
        
        if not db_user:
            raise HTTPException(status_code=401, detail="Invalid admin credentials")
        
        # Verify password
        try:
            if not verify_password(user.password, db_user['password_hash']):
                raise HTTPException(status_code=401, detail="Invalid admin credentials")
        except Exception as e:
            print(f"Password verification error: {e}")
            raise HTTPException(status_code=401, detail="Invalid admin credentials")
        
        token = create_token(db_user['id'], db_user['username'], db_user['role'])
        return {
            "token": token,
            "user_id": db_user['id'],
            "username": db_user['username'],
            "role": db_user['role'],
            "message": "Admin login successful"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Admin login error: {e}")
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")
    finally:
        conn.close()

@app.post("/change-password")
async def change_password(password_data: PasswordChange, current_user: dict = Depends(get_current_user)):
    """Change user password"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get current user's password hash
        cursor.execute(
            "SELECT password_hash FROM users WHERE id = ?",
            (current_user['user_id'],)
        )
        user_row = cursor.fetchone()
        
        if not user_row:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify current password
        if not verify_password(password_data.current_password, user_row['password_hash']):
            raise HTTPException(status_code=401, detail="Current password is incorrect")
        
        # Validate new password
        if len(password_data.new_password) < 6:
            raise HTTPException(status_code=400, detail="New password must be at least 6 characters long")
        
        if password_data.current_password == password_data.new_password:
            raise HTTPException(status_code=400, detail="New password must be different from current password")
        
        # Hash new password and update
        new_password_hash = hash_password(password_data.new_password)
        cursor.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (new_password_hash, current_user['user_id'])
        )
        conn.commit()
        
        return {
            "message": "Password changed successfully",
            "username": current_user['username']
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error changing password: {str(e)}")
    finally:
        conn.close()

@app.get("/admin/dashboard-stats")
async def admin_dashboard_stats(current_user: dict = Depends(is_admin)):
    """Get dashboard statistics for admin"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM reviews")
        total_reviews = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'user'")
        registered_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM models")
        total_models = cursor.fetchone()[0]
        
        # Aspect ratio
        cursor.execute("SELECT aspect, COUNT(*) as count FROM aspects GROUP BY aspect")
        rows = cursor.fetchall()
        aspect_ratio = {row[0]: row[1] for row in rows}
        
        return {
            "total_users": total_users,
            "total_reviews": total_reviews,
            "registered_users": registered_users,
            "total_models": total_models,
            "aspect_ratio": aspect_ratio
        }
    finally:
        conn.close()

@app.get("/admin/aspect-categories")
async def get_aspect_categories(current_user: dict = Depends(is_admin)):
    """Get all aspect categories"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT DISTINCT aspect as name FROM aspects ORDER BY aspect")
        rows = cursor.fetchall()
        categories = [{"id": i+1, "name": row[0], "description": ""} for i, row in enumerate(rows)]
        return categories
    finally:
        conn.close()

@app.post("/admin/aspect-categories")
async def add_aspect_category(category: dict, current_user: dict = Depends(is_admin)):
    """Add new aspect category"""
    # For now, categories are derived from aspects table
    # This is a placeholder endpoint
    return {"id": 1, "name": category.get("name"), "description": category.get("description", "")}

@app.delete("/admin/aspect-categories/{category_id}")
async def delete_aspect_category(category_id: int, current_user: dict = Depends(is_admin)):
    """Delete aspect category"""
    # Placeholder endpoint
    return {"message": "Category deleted successfully"}

@app.get("/admin/system-logs")
async def get_system_logs(current_user: dict = Depends(is_admin)):
    """Get system logs"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                r.created_at as timestamp,
                'Review submitted' as event,
                r.user_id,
                u.username,
                'User submitted a review' as details
            FROM reviews r
            JOIN users u ON r.user_id = u.id
            ORDER BY r.created_at DESC
            LIMIT 100
        """)
        rows = cursor.fetchall()
        logs = [
            {
                "timestamp": row[0],
                "event": row[1],
                "user_id": row[2],
                "username": row[3],
                "details": row[4]
            }
            for row in rows
        ]
        return logs
    finally:
        conn.close()

@app.get("/admin/quality-settings")
async def get_quality_settings(current_user: dict = Depends(is_admin)):
    """Get quality settings"""
    return {
        "confidence_threshold": 0.7,
        "accuracy_threshold": 0.8,
        "enable_auto_review": True,
        "max_review_items": 50,
        "enable_notifications": True,
        "notification_email": "admin@example.com"
    }

@app.put("/admin/quality-settings")
async def update_quality_settings(settings: dict, current_user: dict = Depends(is_admin)):
    """Update quality settings"""
    # Settings would be stored in database in production
    return {"message": "Settings updated successfully", "settings": settings}

@app.post("/submit-review")
async def submit_review(review: ReviewSubmit, current_user: dict = Depends(get_current_user)):
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO reviews (user_id, review_text) VALUES (?, ?)",
            (current_user['user_id'], review.review_text)
        )
        review_id = cursor.lastrowid
        
        engine = get_absa_engine()
        aspects = engine.extract_aspects(review.review_text)
        results = engine.analyze_aspect_sentiment(review.review_text, aspects)
        
        for result in results:
            keywords = ','.join(result.get('keywords', []))
            cursor.execute(
                """INSERT INTO aspects (review_id, aspect, sentiment, confidence, keywords) 
                   VALUES (?, ?, ?, ?, ?)""",
                (review_id, result['aspect'], result['sentiment'], result['confidence'], keywords)
            )
        
        conn.commit()
        
        return {
            "review_id": review_id,
            "results": results,
            "message": "Review analyzed successfully"
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Active Learning Endpoints
@app.get("/active-learning/uncertain")
async def get_uncertain_predictions(
    current_user: dict = Depends(get_current_user),
    confidence_threshold: float = 0.5,
    limit: int = 50
):
    """Get predictions with confidence below threshold for active learning"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT 
                a.id,
                r.review_text,
                a.aspect,
                a.sentiment,
                a.confidence,
                a.keywords,
                a.corrected_sentiment,
                a.is_corrected,
                a.correction_notes
            FROM aspects a
            JOIN reviews r ON a.review_id = r.id
            WHERE r.user_id = ? 
            AND a.confidence < ?
            AND a.is_corrected = 0
            ORDER BY a.confidence ASC
            LIMIT ?
        ''', (current_user['user_id'], confidence_threshold, limit))
        
        rows = cursor.fetchall()
        
        uncertain_predictions = []
        for row in rows:
            keywords = row['keywords'].split(',') if row['keywords'] else []
            keywords = [k.strip() for k in keywords if k.strip()]
            
            uncertain_predictions.append({
                'id': row['id'],
                'review_text': row['review_text'],
                'aspect': row['aspect'],
                'sentiment': row['sentiment'],
                'confidence': float(row['confidence']),
                'keywords': keywords,
                'corrected_sentiment': row['corrected_sentiment'],
                'is_corrected': bool(row['is_corrected']),
                'correction_notes': row['correction_notes']
            })
        
        return {
            "total_uncertain": len(uncertain_predictions),
            "confidence_threshold": float(confidence_threshold),
            "predictions": uncertain_predictions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching uncertain predictions: {str(e)}")
    finally:
        conn.close()

@app.post("/active-learning/correct")
async def save_correction(correction: CorrectionUpdate, current_user: dict = Depends(get_current_user)):
    """Save user's correction for a prediction"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        aspect_id = correction.aspect_id or correction.prediction_id
        # Verify the aspect belongs to the user
        cursor.execute('''
            SELECT a.id, a.sentiment, a.confidence, r.review_text 
            FROM aspects a
            JOIN reviews r ON a.review_id = r.id
            WHERE a.id = ? AND r.user_id = ?
        ''', (aspect_id, current_user['user_id']))
        
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Aspect not found")
        
        # Update the aspect table
        cursor.execute('''
            UPDATE aspects
            SET corrected_sentiment = ?, 
                is_corrected = 1,
                correction_notes = ?,
                corrected_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (correction.corrected_sentiment, correction.notes, aspect_id))
        
        # Save to active learning corrections table
        cursor.execute('''
            INSERT INTO active_learning_corrections 
            (aspect_id, original_sentiment, corrected_sentiment, confidence, review_text, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            aspect_id,
            result['sentiment'],
            correction.corrected_sentiment,
            result['confidence'],
            result['review_text'],
            current_user['user_id']
        ))
        
        conn.commit()
        
        return {
            "message": "Correction saved successfully",
            "aspect_id": aspect_id,
            "original_sentiment": result['sentiment'],
            "corrected_sentiment": correction.corrected_sentiment
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/active-learning/bulk-correct")
async def save_bulk_corrections(corrections: BulkCorrection, current_user: dict = Depends(get_current_user)):
    """Save multiple corrections at once"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        saved_corrections = []
        
        for correction in corrections.corrections:
            aspect_id = correction.get('aspect_id')
            corrected_sentiment = correction.get('corrected_sentiment')
            notes = correction.get('notes', '')
            
            if not aspect_id or not corrected_sentiment:
                continue
            
            # Verify the aspect belongs to the user
            cursor.execute('''
                SELECT a.id, a.sentiment, a.confidence, r.review_text 
                FROM aspects a
                JOIN reviews r ON a.review_id = r.id
                WHERE a.id = ? AND r.user_id = ?
            ''', (aspect_id, current_user['user_id']))
            
            result = cursor.fetchone()
            if not result:
                continue
            
            # Update aspect
            cursor.execute('''
                UPDATE aspects
                SET corrected_sentiment = ?, 
                    is_corrected = 1,
                    correction_notes = ?,
                    corrected_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (corrected_sentiment, notes, aspect_id))
            
            # Save to corrections table
            cursor.execute('''
                INSERT INTO active_learning_corrections 
                (aspect_id, original_sentiment, corrected_sentiment, confidence, review_text, user_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                aspect_id,
                result['sentiment'],
                corrected_sentiment,
                result['confidence'],
                result['review_text'],
                current_user['user_id']
            ))
            
            saved_corrections.append({
                'aspect_id': aspect_id,
                'original_sentiment': result['sentiment'],
                'corrected_sentiment': corrected_sentiment
            })
        
        conn.commit()
        
        return {
            "message": f"{len(saved_corrections)} corrections saved successfully",
            "saved_corrections": saved_corrections
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/active-learning/export")
async def export_corrections(current_user: dict = Depends(get_current_user)):
    """Export corrected data for model retraining"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT 
                alc.id as correction_id,
                r.review_text,
                a.aspect,
                alc.original_sentiment,
                alc.corrected_sentiment,
                alc.confidence,
                alc.corrected_at,
                alc.used_for_training
            FROM active_learning_corrections alc
            JOIN aspects a ON alc.aspect_id = a.id
            JOIN reviews r ON a.review_id = r.id
            WHERE alc.user_id = ?
            ORDER BY alc.corrected_at DESC
        ''', (current_user['user_id'],))
        
        rows = cursor.fetchall()
        
        corrections = []
        for row in rows:
            corrections.append({
                'correction_id': row['correction_id'],
                'review_text': row['review_text'],
                'aspect': row['aspect'],
                'original_sentiment': row['original_sentiment'],
                'corrected_sentiment': row['corrected_sentiment'],
                'confidence': row['confidence'],
                'corrected_at': row['corrected_at'],
                'used_for_training': bool(row['used_for_training'])
            })
        
        return {
            "total_corrections": len(corrections),
            "corrections": corrections
        }
    finally:
        conn.close()

@app.get("/active-learning/stats")
async def get_active_learning_stats(current_user: dict = Depends(get_current_user)):
    """Get statistics for active learning"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Total uncertain predictions
        cursor.execute('''
            SELECT COUNT(*) as total_uncertain
            FROM aspects a
            JOIN reviews r ON a.review_id = r.id
            WHERE r.user_id = ? AND a.confidence < 0.6 AND a.is_corrected = 0
        ''', (current_user['user_id'],))
        uncertain = cursor.fetchone()['total_uncertain']
        
        # Total corrected
        cursor.execute('''
            SELECT COUNT(*) as total_corrected
            FROM aspects a
            JOIN reviews r ON a.review_id = r.id
            WHERE r.user_id = ? AND a.is_corrected = 1
        ''', (current_user['user_id'],))
        corrected = cursor.fetchone()['total_corrected']
        
        # Confidence distribution
        cursor.execute('''
            SELECT 
                COUNT(*) as count,
                CASE 
                    WHEN confidence < 0.3 THEN 'Very Low (<30%)'
                    WHEN confidence < 0.5 THEN 'Low (30-50%)'
                    WHEN confidence < 0.7 THEN 'Medium (50-70%)'
                    ELSE 'High (>70%)'
                END as confidence_level
            FROM aspects a
            JOIN reviews r ON a.review_id = r.id
            WHERE r.user_id = ?
            GROUP BY confidence_level
            ORDER BY confidence
        ''', (current_user['user_id'],))
        
        confidence_dist = cursor.fetchall()
        confidence_stats = [{"level": row['confidence_level'], "count": row['count']} for row in confidence_dist]
        
        return {
            "uncertain_predictions": uncertain,
            "corrected_predictions": corrected,
            "confidence_distribution": confidence_stats,
            "correction_rate": corrected / (uncertain + corrected) if (uncertain + corrected) > 0 else 0
        }
    finally:
        conn.close()

@app.get("/user-stats")
async def get_user_stats(current_user: dict = Depends(get_current_user)):
    """Get statistics for user's reviews and aspects"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Total reviews count
        cursor.execute(
            "SELECT COUNT(*) as count FROM reviews WHERE user_id = ?",
            (current_user['user_id'],)
        )
        total_reviews = cursor.fetchone()['count']
        
        # Total aspects and sentiment counts
        cursor.execute('''
            SELECT 
                COUNT(*) as total_aspects,
                SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive_aspects,
                SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative_aspects,
                SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral_aspects
            FROM aspects a
            JOIN reviews r ON a.review_id = r.id
            WHERE r.user_id = ?
        ''', (current_user['user_id'],))
        
        stats_row = cursor.fetchone()
        
        return {
            "total_reviews": total_reviews,
            "total_aspects": stats_row['total_aspects'] or 0,
            "positive_aspects": stats_row['positive_aspects'] or 0,
            "negative_aspects": stats_row['negative_aspects'] or 0,
            "neutral_aspects": stats_row['neutral_aspects'] or 0
        }
    finally:
        conn.close()

@app.get("/user-reviews")
async def get_user_reviews(current_user: dict = Depends(get_current_user)):
    """Get all reviews for the current user with their aspects"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get all reviews for the user
        cursor.execute('''
            SELECT id, review_text, created_at
            FROM reviews
            WHERE user_id = ?
            ORDER BY created_at DESC
        ''', (current_user['user_id'],))
        
        review_rows = cursor.fetchall()
        reviews = []
        
        for review_row in review_rows:
            review_id = review_row['id']
            
            # Get all aspects for this review
            cursor.execute('''
                SELECT aspect, sentiment, confidence, keywords
                FROM aspects
                WHERE review_id = ?
                ORDER BY confidence DESC
            ''', (review_id,))
            
            aspect_rows = cursor.fetchall()
            aspects = []
            
            for aspect_row in aspect_rows:
                aspects.append({
                    'aspect': aspect_row['aspect'],
                    'sentiment': aspect_row['sentiment'],
                    'confidence': aspect_row['confidence'],
                    'keywords': aspect_row['keywords'].split(',') if aspect_row['keywords'] else []
                })
            
            reviews.append({
                'review_text': review_row['review_text'],
                'created_at': review_row['created_at'],
                'aspects': aspects
            })
        
        return {
            "reviews": reviews,
            "total_reviews": len(reviews)
        }
    finally:
        conn.close()

@app.post("/batch-analyze")
async def batch_analyze(batch: BatchAnalyze, current_user: dict = Depends(get_current_user)):
    """Analyze multiple reviews at once and save to database"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        engine = get_absa_engine()
        all_results = []
        
        for review_text in batch.reviews:
            # Insert review into database
            cursor.execute(
                "INSERT INTO reviews (user_id, review_text) VALUES (?, ?)",
                (current_user['user_id'], review_text)
            )
            review_id = cursor.lastrowid
            
            # Extract and analyze aspects
            aspects = engine.extract_aspects(review_text)
            results = engine.analyze_aspect_sentiment(review_text, aspects)
            
            # Save aspects to database
            for result in results:
                keywords = ','.join(result.get('keywords', []))
                cursor.execute(
                    """INSERT INTO aspects (review_id, aspect, sentiment, confidence, keywords) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (review_id, result['aspect'], result['sentiment'], result['confidence'], keywords)
                )
                
                # Add review_text to result for display
                result['review_text'] = review_text
                all_results.append(result)
        
        conn.commit()
        
        return {
            "total_aspects": len(all_results),
            "total_reviews": len(batch.reviews),
            "results": all_results,
            "message": f"Analyzed {len(batch.reviews)} reviews successfully"
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/active-learning/retrain")
async def retrain_model(current_user: dict = Depends(get_current_user)):
    """Retrain a lightweight sentiment model using corrected samples.
    This implementation trains a simple TF-IDF + LogisticRegression pipeline
    on all corrections that have not yet been used for training. The trained
    model is stored on disk (./models/trained_sentiment_model.pkl).
    """
    import os
    from pathlib import Path
    import joblib  # scikit-learn provides joblib vendored, safe to import
    from sklearn.pipeline import Pipeline
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression

    conn = get_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 1. Fetch all corrections not yet used for training
        cursor.execute(
            """
            SELECT id, review_text, corrected_sentiment
            FROM active_learning_corrections
            WHERE used_for_training = 0
            """
        )
        rows = cursor.fetchall()
        if not rows:
            return {
                "message": "No new corrections available for training.",
                "corrections_used": 0,
                "status": "no_data"
            }

        texts = [row["review_text"] for row in rows]
        labels = [row["corrected_sentiment"] for row in rows]

        # 2. Basic sanity-checks before training
        unique_labels = set(labels)
        if len(unique_labels) < 2:
            # Need at least two distinct classes for supervised training
            return {
                "message": "At least two different sentiment classes are required to retrain the model. Add more diverse corrections and try again.",
                "corrections_used": 0,
                "status": "not_enough_classes"
            }
        if len(texts) < 5:
            # Warn if the dataset is probably too small
            return {
                "message": "Need at least 5 corrected samples to retrain reliably. Currently provided: " + str(len(texts)),
                "corrections_used": 0,
                "status": "not_enough_samples"
            }

        # 3. Build & train the model
        pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words="english")),
            ("clf", LogisticRegression(max_iter=1000, n_jobs=-1)),
        ])
        try:
            pipeline.fit(texts, labels)
        except ValueError as ve:
            # Handle edge cases (e.g., only one class present after the above checks, or other sklearn errors)
            raise HTTPException(status_code=400, detail=f"Training failed: {ve}")

        # 4. Persist the model
        models_dir = Path("models")
        models_dir.mkdir(exist_ok=True)
        model_path = models_dir / "trained_sentiment_model.pkl"
        joblib.dump(pipeline, model_path)

        # 4. Mark these corrections as used
        correction_ids = [row["id"] for row in rows]
        cursor.execute(
            f"UPDATE active_learning_corrections SET used_for_training = 1 WHERE id IN ({','.join(['?']*len(correction_ids))})",
            correction_ids,
        )
        conn.commit()

        return {
            "message": "Model retrained successfully and saved.",
            "corrections_used": len(correction_ids),
            "model_path": str(model_path),
            "status": "success"
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

from pydantic import BaseModel

class CorrectionItem(BaseModel):
    review_text: str
    corrected_sentiment: str
    original_sentiment: str | None = None
    confidence: float | None = None

@app.post("/active-learning/upload-corrections")
async def upload_corrections(items: list[CorrectionItem], current_user: dict = Depends(get_current_user)):
    """Upload corrected samples (via CSV/Excel) and store for future training"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        for item in items:
            # 1. Save a placeholder review for traceability
            cursor.execute(
                "INSERT INTO reviews (user_id, review_text) VALUES (?, ?)",
                (current_user['user_id'], item.review_text)
            )
            review_id = cursor.lastrowid

            # 2. Create a placeholder aspect so FK constraints are satisfied
            cursor.execute(
                """
                INSERT INTO aspects (review_id, aspect, sentiment, confidence, keywords)
                VALUES (?, 'general', COALESCE(?, 'unknown'), COALESCE(?, 0.0), '')
                """,
                (
                    review_id,
                    item.original_sentiment,
                    item.confidence or 0.0
                )
            )
            aspect_id = cursor.lastrowid

            # 3. Store the correction referencing the new aspect
            cursor.execute(
                """
                INSERT INTO active_learning_corrections (aspect_id, original_sentiment, corrected_sentiment, confidence, review_text, user_id, used_for_training)
                VALUES (?, COALESCE(?, 'unknown'), ?, COALESCE(?, 0.0), ?, ?, 0)
                """,
                (
                    aspect_id,
                    item.original_sentiment,
                    item.corrected_sentiment,
                    item.confidence or 0.0,
                    item.review_text,
                    current_user['user_id']
                )
            )
        conn.commit()
        return {"message": f"Uploaded {len(items)} corrections", "status": "success", "corrections_added": len(items)}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.post("/active-learning/add-to-training")
async def add_to_training_set(current_user: dict = Depends(get_current_user)):
    """Add all corrections to the training set"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Count unused corrections
        cursor.execute('''
            SELECT COUNT(*) as count FROM active_learning_corrections
            WHERE user_id = ? AND used_for_training = 0
        ''', (current_user['user_id'],))
        
        unused_count = cursor.fetchone()['count']
        
        if unused_count > 0:
            # Mark them as used for training
            cursor.execute('''
                UPDATE active_learning_corrections
                SET used_for_training = 1
                WHERE user_id = ? AND used_for_training = 0
            ''', (current_user['user_id'],))
            
            conn.commit()
            
            return {
                "message": f"Added {unused_count} corrections to training set",
                "corrections_added": unused_count,
                "status": "success"
            }
        else:
            return {
                "message": "No new corrections to add",
                "corrections_added": 0,
                "status": "success"
            }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ============ ACTIVE LEARNING ENDPOINTS ============

@app.get("/uncertain-samples")
async def get_uncertain_samples(current_user: dict = Depends(get_current_user)):
    """Get review samples with confidence < 50% for active learning"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get aspects with confidence < 0.5 that haven't been corrected
        cursor.execute('''
            SELECT 
                a.id as aspect_id,
                r.id as review_id,
                r.review_text,
                a.aspect,
                a.sentiment as predicted_sentiment,
                a.confidence
            FROM aspects a
            JOIN reviews r ON a.review_id = r.id
            WHERE r.user_id = ? 
            AND a.confidence < 0.5
            AND a.is_corrected = 0
            ORDER BY a.confidence ASC
            LIMIT 50
        ''', (current_user['user_id'],))
        
        samples = []
        for row in cursor.fetchall():
            samples.append({
                'aspect_id': row['aspect_id'],
                'review_id': row['review_id'],
                'review_text': row['review_text'],
                'aspect': row['aspect'],
                'predicted_sentiment': row['predicted_sentiment'],
                'confidence': row['confidence']
            })
        
        conn.close()
        return {
            'uncertain_samples': samples,
            'total_count': len(samples)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/save-corrections")
async def save_corrections(corrections_data: dict, current_user: dict = Depends(get_current_user)):
    """Save corrected sentiments and automatically retrain model"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        corrections = corrections_data.get('corrections', {})
        saved_count = 0
        
        for review_id, correction_info in corrections.items():
            try:
                review_id_int = int(review_id)
                aspect = correction_info.get('aspect', '')
                corrected_sentiment = correction_info.get('corrected_sentiment', '')
                
                # Find the aspect record
                cursor.execute('''
                    SELECT a.id, a.sentiment, a.confidence, r.review_text FROM aspects a
                    JOIN reviews r ON a.review_id = r.id
                    WHERE a.review_id = ? AND a.aspect = ?
                ''', (review_id_int, aspect))
                
                aspect_row = cursor.fetchone()
                if aspect_row:
                    aspect_id = aspect_row['id']
                    original_sentiment = aspect_row['sentiment']
                    confidence = aspect_row['confidence']
                    review_text = aspect_row['review_text']
                    
                    # Update aspect with correction - also update the sentiment field itself
                    cursor.execute('''
                        UPDATE aspects 
                        SET sentiment = ?, corrected_sentiment = ?, is_corrected = 1, corrected_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (corrected_sentiment, corrected_sentiment, aspect_id))
                    
                    # Record in active learning table
                    cursor.execute('''
                        INSERT INTO active_learning_corrections 
                        (aspect_id, original_sentiment, corrected_sentiment, confidence, review_text, user_id, used_for_training)
                        VALUES (?, ?, ?, ?, ?, ?, 0)
                    ''', (aspect_id, original_sentiment, corrected_sentiment, confidence, review_text, current_user['user_id']))
                    
                    saved_count += 1
            except Exception as e:
                print(f"Error saving correction for review {review_id}: {e}")
                continue
        
        conn.commit()
        
        # Automatically trigger model retraining if we have enough corrections
        retrain_result = None
        if saved_count > 0:
            try:
                # Check total unused corrections
                cursor.execute('''
                    SELECT COUNT(*) as count FROM active_learning_corrections
                    WHERE used_for_training = 0
                ''')
                total_unused = cursor.fetchone()['count']
                
                # Retrain if we have at least 5 corrections
                if total_unused >= 5:
                    import os
                    from pathlib import Path
                    import joblib
                    from sklearn.pipeline import Pipeline
                    from sklearn.feature_extraction.text import TfidfVectorizer
                    from sklearn.linear_model import LogisticRegression
                    
                    # Fetch all corrections not yet used for training
                    cursor.execute('''
                        SELECT id, review_text, corrected_sentiment
                        FROM active_learning_corrections
                        WHERE used_for_training = 0
                    ''')
                    rows = cursor.fetchall()
                    
                    texts = [row['review_text'] for row in rows]
                    labels = [row['corrected_sentiment'] for row in rows]
                    
                    # Check if we have at least 2 different classes
                    unique_labels = set(labels)
                    if len(unique_labels) >= 2:
                        # Build & train the model
                        pipeline = Pipeline([
                            ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words="english")),
                            ("clf", LogisticRegression(max_iter=1000, n_jobs=-1)),
                        ])
                        pipeline.fit(texts, labels)
                        
                        # Persist the model
                        models_dir = Path("models")
                        models_dir.mkdir(exist_ok=True)
                        model_path = models_dir / "trained_sentiment_model.pkl"
                        joblib.dump(pipeline, model_path)
                        
                        # Mark corrections as used
                        correction_ids = [row['id'] for row in rows]
                        cursor.execute(
                            f"UPDATE active_learning_corrections SET used_for_training = 1 WHERE id IN ({','.join(['?']*len(correction_ids))})",
                            correction_ids,
                        )
                        
                        # Record model training in database
                        cursor.execute('''
                            INSERT INTO models (name, version, path)
                            VALUES (?, ?, ?)
                        ''', ('sentiment_model', f'v{len(correction_ids)}', str(model_path)))
                        
                        conn.commit()
                        
                        retrain_result = {
                            'retrained': True,
                            'corrections_used': len(correction_ids),
                            'model_path': str(model_path)
                        }
                    else:
                        retrain_result = {
                            'retrained': False,
                            'reason': 'Need at least 2 different sentiment classes'
                        }
                else:
                    retrain_result = {
                        'retrained': False,
                        'reason': f'Need at least 5 corrections (currently: {total_unused})'
                    }
            except Exception as retrain_error:
                print(f"Error during automatic retraining: {retrain_error}")
                retrain_result = {
                    'retrained': False,
                    'error': str(retrain_error)
                }
        
        conn.close()
        
        response = {
            'message': f'Saved {saved_count} corrections successfully!',
            'corrections_saved': saved_count,
            'status': 'success'
        }
        
        if retrain_result:
            response['retraining'] = retrain_result
            if retrain_result.get('retrained'):
                response['message'] += f" Model automatically retrained with {retrain_result['corrections_used']} corrections."
        
        return response
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-corrections")
async def get_user_corrections(current_user: dict = Depends(get_current_user)):
    """Get all corrections made by the user"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                alc.id,
                alc.review_text,
                alc.original_sentiment,
                alc.corrected_sentiment,
                alc.confidence,
                alc.corrected_at
            FROM active_learning_corrections alc
            WHERE alc.user_id = ?
            ORDER BY alc.corrected_at DESC
        ''', (current_user['user_id'],))
        
        corrections = []
        for row in cursor.fetchall():
            corrections.append({
                'id': row['id'],
                'review_text': row['review_text'],
                'original_sentiment': row['original_sentiment'],
                'corrected_sentiment': row['corrected_sentiment'],
                'confidence': f"{row['confidence']:.2%}",
                'corrected_at': row['corrected_at']
            })
        
        conn.close()
        return {
            'corrections': corrections,
            'total_corrections': len(corrections)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict-batch")
async def predict_batch(batch_data: dict, current_user: dict = Depends(get_current_user)):
    """Batch predict sentiment for uploaded reviews"""
    try:
        reviews = batch_data.get('reviews', [])
        
        if not reviews:
            raise HTTPException(status_code=400, detail="No reviews provided")
        
        absa_engine = get_absa_engine()
        predictions = []
        
        for review in reviews:
            review_text = review.get('review_text') or review.get('text') or ''
            if not review_text:
                continue
            
            aspects = absa_engine.extract_aspects(review_text)
            sentiment_results = absa_engine.analyze_aspect_sentiment(review_text, aspects)
            
            for result in sentiment_results:
                predictions.append({
                    'review_text': review_text[:150],
                    'aspect': result['aspect'],
                    'sentiment': result['sentiment'],
                    'confidence': f"{result['confidence']:.2%}",
                    'keywords': result.get('keywords', [])
                })
        
        return {
            'predictions': predictions,
            'total_predictions': len(predictions),
            'status': 'success'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/model-stats")
async def get_model_stats(current_user: dict = Depends(get_current_user)):
    """Get model performance statistics for the user"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Count uncertain samples
        cursor.execute('''
            SELECT COUNT(*) as count FROM aspects
            WHERE review_id IN (SELECT id FROM reviews WHERE user_id = ?)
            AND confidence < 0.5 AND is_corrected = 0
        ''', (current_user['user_id'],))
        uncertain_count = cursor.fetchone()['count']
        
        # Count corrections made
        cursor.execute('''
            SELECT COUNT(*) as count FROM active_learning_corrections
            WHERE user_id = ?
        ''', (current_user['user_id'],))
        corrections_count = cursor.fetchone()['count']
        
        # Average confidence
        cursor.execute('''
            SELECT AVG(confidence) as avg_conf FROM aspects
            WHERE review_id IN (SELECT id FROM reviews WHERE user_id = ?)
        ''', (current_user['user_id'],))
        avg_conf_row = cursor.fetchone()
        avg_confidence = avg_conf_row['avg_conf'] or 0.65
        
        conn.close()
        
        return {
            'total_uncertain': uncertain_count,
            'total_corrections': corrections_count,
            'avg_confidence': avg_confidence,
            'model_version': 'v1.1',
            'improvement_potential': f"{(corrections_count / max(uncertain_count, 1)) * 100:.1f}%" if uncertain_count > 0 else "0%"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "ABSA API is running", "status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
