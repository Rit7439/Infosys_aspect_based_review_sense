# 🎯 Aspect-Based Sentiment Analyzer (ABSA)

A comprehensive **Aspect-Based Sentiment Analysis** system with Active Learning, Admin Dashboard, and Batch Processing capabilities. The system analyzes customer reviews to extract aspects and their corresponding sentiments with high accuracy.

## ✨ Features

### User Features
- **📝 Submit Reviews**: Analyze customer reviews with instant aspect-based sentiment analysis
- **🔍 Active Learning**: Correct uncertain predictions to improve model accuracy
- **📊 Batch Analysis**: Upload CSV/Excel files to analyze multiple reviews at once
- **💬 Model Feedback**: Rate and provide feedback on model performance
- **📋 Review History**: View all submitted reviews with sentiment distribution charts (Pie & Bar)
- **📤 Export Results**: Download analysis results in CSV format
- **👤 User Profile**: Manage account settings and change password

### Admin Features
- **🎓 Active Learning Management**: View and manage user corrections for model training
- **📊 Overall Sentiment Analysis**: 
  - Global sentiment distribution (Pie & Bar charts)
  - Aspect-wise sentiment breakdown (Grouped & Stacked bar charts)
  - Sentiment percentage by aspect
- **🎯 Users Activity Logs**: 
  - Track all user-submitted reviews
  - Filter by username, sentiment, or review content
  - Delete users and their associated data
  - Export activity logs to CSV
- **👨‍💼 Admin Profile**: Manage admin account and change password

## 🛠️ Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **SQLite3** - Database management
- **JWT Authentication** - Secure token-based authentication
- **Uvicorn** - ASGI server

### Frontend
- **Streamlit** - Interactive web interface
- **Plotly** - Advanced data visualizations
- **Pandas** - Data manipulation and analysis

### NLP & Machine Learning
- **DeBERTa** - Deep BiDirectional Encoder Representations from Transformers (ABSA model)
- **spaCy** - Natural language processing
- **NLTK** - Natural Language Toolkit for sentiment analysis
- **Rule-based Sentiment Classification** - Custom sentiment rules

### Additional Libraries
- **Requests** - HTTP client
- **bcrypt** - Password hashing
- **openpyxl** - Excel file handling

## 📋 Project Structure

```
.
├── app.py                 # Streamlit frontend application
├── main.py                # FastAPI backend application
├── absa_engine.py         # NLP sentiment analysis engine
├── auth.py                # Authentication module
├── database.py            # Database initialization and setup
├── requirements.txt       # Python dependencies
├── reviews.db             # SQLite database
└── models/                # Pre-trained NLP models
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd "Infosys review sense"
```

### Step 2: Create Virtual Environment
```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Initialize Database
```bash
python database.py
```

## 💻 Running the Application

### Terminal 1: Start FastAPI Backend (Port 8000)
```bash
python main.py
```
The API will be available at `http://localhost:8000`

### Terminal 2: Start Streamlit Frontend (Port 8501)
```bash
streamlit run app.py
```
The app will open at `http://localhost:8501`

## 🔐 Default Credentials

### Admin Login
- **Username**: admin
- **Password**: admin123

### Sample User
- **Username**: user1
- **Email**: user1@example.com
- **Password**: password123

## 📖 How to Use

### For Users

1. **Login**: Use user credentials to log in
2. **Submit Review**: Go to "Submit Review" tab and enter your review
3. **View Analysis**: See aspects and sentiments with confidence scores
4. **Active Learning**: Correct uncertain predictions (<50% confidence)
5. **Batch Analysis**: Upload CSV files with reviews for bulk analysis
6. **Provide Feedback**: Rate the model and share your feedback

### For Admins

1. **Login**: Use admin credentials to log in
2. **Dashboard**: View overall statistics and sentiment distribution
3. **Active Learning Corrections**: Review and manage user corrections
4. **Overall Sentiment Analysis**: 
   - View sentiment distribution charts
   - Analyze aspect-wise sentiment breakdown
   - Export data to CSV
5. **Users Activity Logs**:
   - Filter and search user reviews
   - Delete users if needed
   - Export activity logs

## 🗄️ Database Schema

### Users Table
```sql
- id: INTEGER PRIMARY KEY
- username: TEXT UNIQUE
- email: TEXT UNIQUE
- password_hash: TEXT
- full_name: TEXT
- created_at: TIMESTAMP
```

### Reviews Table
```sql
- id: INTEGER PRIMARY KEY
- user_id: INTEGER (FOREIGN KEY)
- review_text: TEXT
- product_name: TEXT
- rating: INTEGER
- created_at: TIMESTAMP
```

### Aspects Table
```sql
- id: INTEGER PRIMARY KEY
- review_id: INTEGER (FOREIGN KEY)
- aspect: TEXT
- sentiment: TEXT
- confidence: REAL
- corrected_sentiment: TEXT
- is_corrected: INTEGER
- created_at: TIMESTAMP
```

### Active Learning Corrections Table
```sql
- id: INTEGER PRIMARY KEY
- aspect_id: INTEGER (FOREIGN KEY)
- original_sentiment: TEXT
- corrected_sentiment: TEXT
- confidence: REAL
- user_id: INTEGER (FOREIGN KEY)
- corrected_at: TIMESTAMP
- used_for_training: INTEGER
```

### User Feedback Table
```sql
- id: INTEGER PRIMARY KEY
- user_id: INTEGER (FOREIGN KEY)
- rating: INTEGER (1-5)
- feedback_text: TEXT
- feedback_type: TEXT
- created_at: TIMESTAMP
```

## 🔌 API Endpoints (Main)

### Authentication
- `POST /admin/login` - Admin login
- `POST /login` - User login
- `POST /register` - User registration

### Reviews
- `POST /submit-review` - Submit a review for analysis
- `GET /my-reviews` - Get user's submitted reviews
- `POST /predict-batch` - Batch analysis of reviews

### Active Learning
- `GET /uncertain-samples` - Get samples with low confidence
- `POST /save-corrections` - Save corrections and retrain model
- `GET /active-learning-corrections` - Get correction history

### Admin
- `GET /admin/dashboard-stats` - Dashboard statistics
- `GET /admin/sentiment-analysis` - Overall sentiment analysis
- `GET /admin/activity-logs` - User activity logs
- `DELETE /admin/delete-user/{user_id}` - Delete user and data

### Feedback
- `POST /submit-feedback` - Submit user feedback (stored in database)

## 🎨 Features Breakdown

### Sentiment Analysis
- **Aspects Extracted**: Product features, service quality, price, delivery, etc.
- **Sentiments Predicted**: Positive, Negative, Neutral
- **Confidence Scores**: 0-100% indicating prediction confidence

### Active Learning
- Identifies predictions with confidence < 50%
- Users can correct uncertain predictions
- Corrections saved to database
- Model can be retrained using corrections
- Tracks which corrections have been used for training

### Batch Processing
- Upload CSV/Excel files with review data
- Bulk sentiment analysis
- Export results with visualizations
- Support for multiple products

## 📊 Visualizations

### User Dashboard
- Sentiment distribution (Pie chart)
- Aspect distribution (Bar chart)
- Sentiment breakdown across reviews
- Review statistics and metrics

### Admin Dashboard
- Overall sentiment distribution (Pie & Bar)
- Aspect-sentiment heatmap
- Sentiment percentage by aspect
- User activity timeline
- Correction history with stats

## ⚙️ Configuration

### Timezone
- System configured for **IST (Indian Standard Time, UTC+5:30)**
- All timestamps stored in local time

### Model Settings
- **DeBERTa Model**: Fine-tuned for ABSA tasks
- **Confidence Threshold**: 50% for uncertainty detection
- **Batch Size**: Configurable for batch processing

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Kill process on port 8501
netstat -ano | findstr :8501
taskkill /PID <PID> /F
```

### Database Issues
```bash
# Reinitialize database
python database.py
```

### Model Not Found
```bash
# Reinstall requirements
pip install --upgrade transformers torch
```

## 📝 Sample Review

**Input**: "The battery life is excellent but the screen resolution could be better. Delivery was fast."

**Output**:
```
Aspect: battery → Sentiment: Positive (Confidence: 95%)
Aspect: screen → Sentiment: Negative (Confidence: 87%)
Aspect: delivery → Sentiment: Positive (Confidence: 91%)
```

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 👨‍💻 Author

**Ritam** - Infosys Review Sense System

## 📞 Support

For issues, questions, or feature requests, please open an issue on GitHub.

---

**Built with ❤️ using FastAPI, Streamlit, and DeBERTa**
