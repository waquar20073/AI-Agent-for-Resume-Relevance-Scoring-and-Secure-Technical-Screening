import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///recruitment_agent.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'docx'}
    
    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Security Configuration
    SESSION_TIMEOUT = 3600  # 1 hour
    MAX_INTERVIEW_DURATION = 7200  # 2 hours
    
    # Scoring Configuration
    RESUME_SCORE_WEIGHTS = {
        'skills_match': 0.4,
        'experience_relevance': 0.3,
        'education': 0.2,
        'certifications': 0.1
    }
    
    # Interview Configuration
    QUESTION_DIFFICULTY_LEVELS = ['beginner', 'intermediate', 'advanced', 'expert']
    DEFAULT_DIFFICULTY = 'intermediate'
    MAX_QUESTIONS_PER_INTERVIEW = 15
    
    # Compliance Configuration
    PROTECTED_ATTRIBUTES = ['gender', 'age', 'race', 'religion', 'nationality', 'disability']
    BIAS_THRESHOLD = 0.15
    INTEGRITY_SCORE_THRESHOLD = 0.7
