# AI Agent for Resume Relevance Scoring and Secure Technical Screening

## Project Overview

This project builds a secure, compliance-aware AI agent that automates early-stage hiring for Data Science and Agentic AI roles through two interconnected modules:

1. **Resume Relevance Scoring** - NLP-based evaluation of candidate resumes against job descriptions
2. **Secure AI Technical Screening Interview** - Adaptive technical interview with anti-cheating mechanisms

## Features

### Module 1: Resume Relevance Scoring
- Parse resumes and job descriptions using NLP and semantic similarity models
- Evaluate alignment on data science and AI-agentic competencies
- Generate Relevance Score (0-100) with transparent explanations
- Built-in compliance layer ensuring fairness and privacy

### Module 2: Secure AI Technical Screening
- Autonomous chat-based technical interviews
- Dynamic question adaptation based on candidate responses
- Comprehensive question bank covering:
  - Data science, statistics, ML, and Python
  - Deep learning, transformers, LLMs
  - Agentic AI systems (prompt chaining, reasoning, multi-agent coordination)
- Structured interview reports with domain-specific scoring

### Compliance & Anti-Cheating Mechanisms
- AI Compliance Engine for bias detection and fairness
- Candidate authentication system
- Real-time integrity monitoring
- Privacy and ethical governance
- Comprehensive audit logging

## Project Structure

```
ai-recruitment-agent/
├── README.md
├── requirements.txt
├── config/
│   ├── __init__.py
│   └── settings.py
├── src/
│   ├── __init__.py
│   ├── resume_scorer/
│   │   ├── __init__.py
│   │   ├── parser.py
│   │   ├── scorer.py
│   │   └── compliance.py
│   ├── interview_engine/
│   │   ├── __init__.py
│   │   ├── question_bank.py
│   │   ├── adaptive_interview.py
│   │   └── evaluator.py
│   ├── compliance/
│   │   ├── __init__.py
│   │   ├── bias_detector.py
│   │   ├── integrity_monitor.py
│   │   └── audit_logger.py
│   └── utils/
│       ├── __init__.py
│       ├── nlp_utils.py
│       └── data_models.py
├── web_interface/
│   ├── app.py
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── templates/
│       ├── index.html
│       ├── resume_upload.html
│       ├── interview.html
│       └── results.html
├── data/
│   ├── sample_resumes/
│   ├── sample_job_descriptions/
│   └── question_bank.json
├── tests/
│   ├── __init__.py
│   ├── test_resume_scorer.py
│   ├── test_interview_engine.py
│   └── test_compliance.py
├── docs/
│   ├── architecture.md
│   ├── api_documentation.md
│   └── compliance_report.md
└── main.py
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-recruitment-agent
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configurations
```

## Usage

### Running the Application

1. Start the web interface:
```bash
python main.py
```

2. Open your browser and navigate to `http://localhost:5000`

### Using the Resume Scorer

1. Upload a resume (PDF, DOCX, or TXT format)
2. Provide a job description
3. Receive a relevance score with detailed breakdown

### Conducting Technical Interviews

1. Candidate authentication through secure login
2. Adaptive interview session begins
3. Real-time integrity monitoring
4. Comprehensive evaluation report generated

## API Documentation

### Resume Scoring Endpoints
- `POST /api/resume/score` - Score resume against job description
- `GET /api/resume/score/{score_id}` - Retrieve scoring results

### Interview Endpoints
- `POST /api/interview/start` - Initiate interview session
- `POST /api/interview/answer` - Submit answer to question
- `GET /api/interview/report/{session_id}` - Get interview report

### Compliance Endpoints
- `GET /api/compliance/audit/{session_id}` - Retrieve audit logs
- `POST /api/compliance/check` - Run compliance check

## Compliance & Ethics

This system adheres to strict AI governance principles:
- No bias based on protected attributes (gender, age, religion, etc.)
- Full explainability for all decisions
- Data privacy protection (no PII exposure)
- Transparent AI evaluation disclosure
- Candidate feedback mechanisms

## Technical Requirements

- Python 3.8+
- Flask for web interface
- Transformers/NLTK for NLP processing
- OpenAI API or similar for LLM capabilities
- SQLite/PostgreSQL for data storage
- Redis for session management

## Evaluation Metrics

The system tracks:
- Resume scoring accuracy
- Interview assessment reliability
- Bias detection effectiveness
- Anti-cheating mechanism performance
- User satisfaction scores

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For questions or support, please contact the development team.

---

**Note**: This is a prototype system designed for demonstration purposes. Not intended for live hiring without proper validation and compliance review.
