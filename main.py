#!/usr/bin/env python3
"""
AI Recruitment Agent - Main Application Entry Point

This is the main entry point for the AI Recruitment Agent system.
It provides a secure, compliant AI-powered recruitment platform for Data Science and Agentic AI roles.

Features:
- Resume relevance scoring with NLP
- Adaptive technical interviews
- Compliance and bias detection
- Integrity monitoring
- Comprehensive reporting

Author: Corporate Live Project Programme
Version: 1.0.0
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """Setup logging configuration."""
    # Create logs directory if it doesn't exist
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(logs_dir / 'app.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        'flask',
        'transformers',
        'torch',
        'numpy',
        'pandas',
        'nltk',
        'spacy',
        'sentence-transformers',
        'scikit-learn',
        'python-docx',
        'pdfplumber',
        'python-dotenv',
        'openai'
    ]
    
    # Map package names to import names
    package_mapping = {
        'scikit-learn': 'sklearn',
        'python-docx': 'docx',
        'sentence-transformers': 'sentence_transformers',
        'python-dotenv': 'dotenv'
    }
    
    missing_packages = []
    
    for package in required_packages:
        import_name = package_mapping.get(package, package.replace('-', '_'))
        try:
            __import__(import_name)
        except ImportError as e:
            if "No module named 'exceptions'" in str(e):
                print(f"❌ Error: Legacy 'docx' package detected. Please uninstall 'docx' and install 'python-docx'.")
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nPlease install missing packages with:")
        print("pip install -r requirements.txt")
        return False
    
    print("✅ All required packages are installed")
    return True

def setup_directories():
    """Create necessary directories."""
    directories = [
        'logs',
        'uploads',
        'data',
        'data/sample_resumes',
        'data/sample_job_descriptions'
    ]
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Directory created/verified: {directory}")

def download_nltk_data():
    """Download required NLTK data."""
    try:
        import nltk
        nltk_data = [
            'punkt',
            'stopwords',
            'wordnet',
            'averaged_perceptron_tagger'
        ]
        
        for data in nltk_data:
            try:
                nltk.data.find(f'tokenizers/{data}')
                print(f"✅ NLTK data already exists: {data}")
            except LookupError:
                print(f"📥 Downloading NLTK data: {data}")
                nltk.download(data, quiet=True)
                
    except ImportError:
        print("⚠️  NLTK not available, skipping NLTK data download")

def check_spacy_model():
    """Check if spaCy model is available."""
    try:
        import spacy
        try:
            nlp = spacy.load("en_core_web_sm")
            print("✅ spaCy English model is available")
            return True
        except OSError:
            print("⚠️  spaCy English model not found")
            print("To install, run: python -m spacy download en_core_web_sm")
            return False
    except ImportError:
        print("⚠️  spaCy not available")
        return False

def initialize_question_bank():
    """Initialize the question bank with default questions."""
    try:
        from src.interview_engine.question_bank import QuestionBank
        
        question_bank = QuestionBank()
        stats = question_bank.get_question_statistics()
        
        print(f"✅ Question bank initialized with {stats['total_questions']} questions")
        print(f"   - By difficulty: {stats['by_difficulty']}")
        print(f"   - By category: {len(stats['by_category'])} categories")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing question bank: {e}")
        return False

def test_nlp_processor():
    """Test the NLP processor."""
    try:
        from src.utils.nlp_utils import NLPProcessor
        
        processor = NLPProcessor()
        
        # Test basic functionality
        test_text = "Python machine learning data science"
        skills = processor.extract_skills(test_text)
        
        print(f"✅ NLP processor test successful")
        print(f"   - Extracted skills: {list(skills.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing NLP processor: {e}")
        return False

def run_web_server():
    """Run the Flask web application."""
    try:
        from web_interface.app import app
        
        print("\n🚀 Starting AI Recruitment Agent Web Server...")
        print("📍 Server will be available at: http://localhost:5000")
        print("🔧 Debug mode: ON")
        print("⚠️  Press Ctrl+C to stop the server\n")
        
        # Run the Flask app
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True
        )
        
    except Exception as e:
        print(f"❌ Error starting web server: {e}")
        return False
    
    return True

def show_system_info():
    """Display system information."""
    print("=" * 60)
    print("🤖 AI RECRUITMENT AGENT - SYSTEM STARTUP")
    print("=" * 60)
    print(f"📁 Project Root: {project_root}")
    print(f"🐍 Python Version: {sys.version}")
    print(f"🖥️  Platform: {os.name}")
    
    try:
        import torch
        print(f"🔥 PyTorch Version: {torch.__version__}")
        print(f"🎯 CUDA Available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"💾 CUDA Devices: {torch.cuda.device_count()}")
    except ImportError:
        print("⚠️  PyTorch not available")
    
    print("=" * 60)

def main():
    """Main application entry point."""
    show_system_info()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Check dependencies
    print("\n🔍 CHECKING DEPENDENCIES...")
    if not check_dependencies():
        logger.error("Missing dependencies. Exiting.")
        sys.exit(1)
    
    # Setup directories
    print("\n📁 SETTING UP DIRECTORIES...")
    setup_directories()
    
    # Download NLP data
    print("\n📚 DOWNLOADING NLP DATA...")
    download_nltk_data()
    
    # Check spaCy model
    print("\n🧠 CHECKING NLP MODELS...")
    spacy_available = check_spacy_model()
    
    # Test NLP processor
    print("\n🧪 TESTING NLP PROCESSOR...")
    nlp_working = test_nlp_processor()
    
    # Initialize question bank
    print("\n❓ INITIALIZING QUESTION BANK...")
    qb_working = initialize_question_bank()
    
    # Show system status
    print("\n📊 SYSTEM STATUS:")
    print(f"   Dependencies: ✅ OK")
    print(f"   Directories: ✅ OK")
    print(f"   NLTK Data: ✅ OK")
    print(f"   spaCy Model: {'✅ OK' if spacy_available else '⚠️  WARNING'}")
    print(f"   NLP Processor: {'✅ OK' if nlp_working else '❌ ERROR'}")
    print(f"   Question Bank: {'✅ OK' if qb_working else '❌ ERROR'}")
    
    # Check if critical components are working
    if not nlp_working or not qb_working:
        logger.error("Critical components are not working. Exiting.")
        print("\n❌ CRITICAL ERRORS DETECTED - CANNOT START SYSTEM")
        sys.exit(1)
    
    # Show warnings for non-critical issues
    if not spacy_available:
        print("\n⚠️  WARNING: spaCy model not available. Some features may be limited.")
    
    print("\n✅ SYSTEM INITIALIZATION COMPLETE")
    
    # Run web server
    try:
        run_web_server()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down AI Recruitment Agent...")
        logger.info("Application shutdown by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
