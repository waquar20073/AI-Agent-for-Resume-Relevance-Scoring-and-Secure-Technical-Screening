from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum

class DifficultyLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class QuestionType(Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    CODING = "coding"
    CONCEPTUAL = "conceptual"
    PRACTICAL = "practical"

class ComplianceStatus(Enum):
    COMPLIANT = "compliant"
    WARNING = "warning"
    VIOLATION = "violation"

@dataclass
class Skill:
    name: str
    category: str
    proficiency_level: int  # 1-5
    years_experience: float

@dataclass
class ResumeData:
    candidate_id: str
    skills: List[Skill]
    experience_years: float
    education: List[Dict[str, Any]]
    certifications: List[str]
    raw_text: str
    processed_at: datetime

@dataclass
class JobDescription:
    job_id: str
    title: str
    required_skills: List[Skill]
    experience_required: float
    education_requirements: List[str]
    responsibilities: List[str]
    raw_text: str

@dataclass
class ScoringResult:
    resume_id: str
    job_id: str
    overall_score: float  # 0-100
    skill_match_score: float
    experience_score: float
    education_score: float
    certification_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    explanation: str
    compliance_flags: List[str]
    scored_at: datetime

@dataclass
class Question:
    question_id: str
    text: str
    type: QuestionType
    difficulty: DifficultyLevel
    category: str
    topics: List[str]
    expected_answer: Optional[str]
    code_template: Optional[str]
    time_limit: int  # minutes
    points: int

@dataclass
class InterviewSession:
    session_id: str
    candidate_id: str
    job_id: str
    started_at: datetime
    current_question: Optional[Question]
    answers: List[Dict[str, Any]]
    difficulty_level: DifficultyLevel
    integrity_score: float
    compliance_status: ComplianceStatus
    is_active: bool

@dataclass
class Answer:
    question_id: str
    answer_text: str
    code_snippet: Optional[str]
    time_taken: int  # seconds
    submitted_at: datetime
    score: float
    feedback: str

@dataclass
class InterviewReport:
    session_id: str
    candidate_id: str
    overall_score: float
    domain_scores: Dict[str, float]
    question_results: List[Dict[str, Any]]
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    integrity_metrics: Dict[str, Any]
    compliance_summary: Dict[str, Any]
    generated_at: datetime

@dataclass
class ComplianceLog:
    log_id: str
    session_id: Optional[str]
    event_type: str
    description: str
    severity: str
    metadata: Dict[str, Any]
    timestamp: datetime

@dataclass
class IntegrityMetrics:
    session_id: str
    copy_paste_detected: bool
    unusual_timing_patterns: bool
    browser_anomalies: bool
    answer_consistency_score: float
    overall_integrity_score: float
    flags: List[str]
