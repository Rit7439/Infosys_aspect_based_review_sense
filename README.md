# Infosys Aspect-Based Review Sense Extraction

An advanced **Aspect-Based Sentiment Analysis (ABSA)** system with **Active Learning** capabilities for analyzing customer reviews and extracting sentiment insights at the aspect level.

## 🌟 Features

- **Aspect-Based Sentiment Analysis**: Automatically identifies aspects (features/topics) in reviews and analyzes sentiment for each aspect
- **Active Learning**: Iteratively improves model accuracy by learning from user corrections on uncertain predictions
- **Dual Interface**:
  - **Streamlit UI** (`app.py`): User-friendly interface for review submission and analysis
  - **FastAPI Backend** (`main.py`): RESTful API for programmatic access
- **User Authentication**: Secure login and registration system with role-based access (Admin/User)
- **Admin Dashboard**: Monitor system metrics, manage users, and view analytics
- **Real-time Analysis**: Instant sentiment analysis with confidence scores
- **Data Export**: Export corrected predictions for model retraining

## 🛠️ Tech Stack

- **Backend**: FastAPI
- **Frontend**: Streamlit
- **NLP Engine**: Custom ABSA engine with transformer models
- **Database**: SQLite
- **Authentication**: JWT tokens, bcrypt password hashing
- **ML Libraries**: PyTorch, Transformers, spaCy

## 📋 Prerequisites

- Python 3.12+
- Virtual environment (recommended)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Rit7439/Infosys_aspect_based_review_sense.git
   cd Infosys_aspect_based_review_sense
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux/Mac
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 💻 Usage

### Running the Streamlit App
```bash
streamlit run app.py
```
Access the app at `http://localhost:8501`

### Running the FastAPI Backend
```bash
python main.py
```
API documentation available at `http://localhost:8000/docs`

### Default Admin Credentials
- **Username**: `admin`
- **Password**: `Admin@123`

## 📁 Project Structure

```
├── app.py                  # Streamlit user interface
├── main.py                 # FastAPI backend server
├── absa_engine.py          # Core ABSA analysis engine
├── requirements.txt        # Python dependencies
├── reviews.db             # SQLite database (auto-created)
├── .gitignore             # Git ignore rules
└── README.md              # Project documentation
```

## 🔑 Key Endpoints (FastAPI)

- `POST /register` - User registration
- `POST /login` - User authentication
- `POST /submit-review` - Submit review for analysis
- `GET /active-learning/uncertain` - Get uncertain predictions
- `POST /active-learning/correct` - Submit corrections
- `GET /admin/dashboard-stats` - Admin dashboard metrics

## 🎯 How It Works

1. **Review Submission**: Users submit product/service reviews
2. **Aspect Extraction**: System identifies key aspects (e.g., "battery life", "customer service")
3. **Sentiment Analysis**: Analyzes sentiment (positive/negative/neutral) for each aspect
4. **Confidence Scoring**: Assigns confidence scores to predictions
5. **Active Learning**: Low-confidence predictions are flagged for user review
6. **Model Improvement**: User corrections are stored for future model retraining

## 📊 Database Schema

- **users**: User accounts and authentication
- **reviews**: Submitted reviews
- **aspects**: Extracted aspects with sentiment and confidence
- **active_learning_corrections**: User corrections for model improvement
- **models**: Model version tracking

## 🔒 Security

- Password hashing with bcrypt
- JWT-based authentication
- Role-based access control (Admin/User)
- Secure session management

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details

## 👨‍💻 Author

**Rit7439**

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

---

**Note**: This project was developed as part of the Infosys internship/project work focusing on sentiment analysis and active learning techniques.
