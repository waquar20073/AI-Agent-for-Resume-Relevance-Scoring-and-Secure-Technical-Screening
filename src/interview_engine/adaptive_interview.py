from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import uuid
import logging
from src.utils.data_models import (
    InterviewSession, Question, Answer, DifficultyLevel, 
    QuestionType, InterviewReport, IntegrityMetrics
)
from src.interview_engine.question_bank import QuestionBank
from src.compliance.integrity_monitor import IntegrityMonitor
from src.compliance.audit_logger import AuditLogger
from config.settings import Config

logger = logging.getLogger(__name__)

class AdaptiveInterviewEngine:
    def __init__(self):
        self.question_bank = QuestionBank()
        self.integrity_monitor = IntegrityMonitor()
        self.audit_logger = AuditLogger()
        self.active_sessions = {}
        
        # Adaptive difficulty parameters
        self.difficulty_adjustment_threshold = 0.7  # Score threshold for difficulty adjustment
        self.difficulty_step_up = 1  # How many levels to increase
        self.difficulty_step_down = 1  # How many levels to decrease
        
        # Interview flow parameters
        self.max_questions_per_session = Config.MAX_QUESTIONS_PER_INTERVIEW
        self.min_questions_per_session = 5
        self.session_timeout = Config.MAX_INTERVIEW_DURATION
    
    def start_interview_session(self, candidate_id: str, job_id: str, 
                              target_categories: List[str] = None) -> InterviewSession:
        """Start a new adaptive interview session."""
        session_id = str(uuid.uuid4())
        
        # Initialize integrity monitoring
        self.integrity_monitor.initialize_session_monitoring(session_id, candidate_id)
        
        # Create initial question set
        initial_questions = self._generate_initial_question_set(target_categories)
        
        # Create session
        session = InterviewSession(
            session_id=session_id,
            candidate_id=candidate_id,
            job_id=job_id,
            started_at=datetime.now(),
            current_question=initial_questions[0] if initial_questions else None,
            answers=[],
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            integrity_score=100.0,
            compliance_status="compliant",
            is_active=True
        )
        
        self.active_sessions[session_id] = {
            'session': session,
            'remaining_questions': initial_questions[1:],
            'asked_questions': [initial_questions[0]] if initial_questions else [],
            'performance_history': [],
            'category_performance': {},
            'integrity_metrics': []
        }
        
        # Log session start
        self.audit_logger.log_event(
            session_id=session_id,
            event_type="interview_session_start",
            description=f"Started interview session for candidate {candidate_id}",
            metadata={
                'candidate_id': candidate_id,
                'job_id': job_id,
                'target_categories': target_categories,
                'initial_difficulty': session.difficulty_level.value
            }
        )
        
        logger.info(f"Started interview session {session_id} for candidate {candidate_id}")
        return session
    
    def _generate_initial_question_set(self, target_categories: List[str] = None) -> List[Question]:
        """Generate initial set of questions for the interview."""
        if not target_categories:
            # Default categories for Data Science and Agentic AI roles
            target_categories = [
                "data_science_fundamentals",
                "machine_learning",
                "python_programming",
                "agentic_ai_systems",
                "prompt_engineering"
            ]
        
        # Get balanced question set
        questions = self.question_bank.get_balanced_question_set(
            count=self.min_questions_per_session,
            target_categories=target_categories
        )
        
        return questions
    
    def submit_answer(self, session_id: str, answer_text: str, 
                     time_taken: int, code_snippet: str = None) -> Dict[str, Any]:
        """Submit an answer and get next question or results."""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session_data = self.active_sessions[session_id]
        session = session_data['session']
        current_question = session.current_question
        
        if not current_question:
            raise ValueError("No current question for this session")
        
        # Create answer object
        answer = Answer(
            question_id=current_question.question_id,
            answer_text=answer_text,
            code_snippet=code_snippet,
            time_taken=time_taken,
            submitted_at=datetime.now(),
            score=0.0,  # Will be calculated
            feedback=""  # Will be generated
        )
        
        # Evaluate answer
        evaluation_result = self._evaluate_answer(answer, current_question)
        answer.score = evaluation_result['score']
        answer.feedback = evaluation_result['feedback']
        
        # Check integrity
        integrity_metrics = self.integrity_monitor.analyze_answer_integrity(
            session_id, answer, current_question.text
        )
        
        # Update session data
        session.answers.append(answer)
        session_data['asked_questions'].append(current_question)
        session_data['performance_history'].append({
            'question_id': current_question.question_id,
            'score': answer.score,
            'difficulty': current_question.difficulty.value,
            'category': current_question.category,
            'time_taken': time_taken,
            'integrity_score': integrity_metrics.overall_integrity_score
        })
        
        # Update category performance
        category = current_question.category
        if category not in session_data['category_performance']:
            session_data['category_performance'][category] = []
        session_data['category_performance'][category].append(answer.score)
        
        # Update session integrity score
        session.integrity_score = integrity_metrics.overall_integrity_score
        session_data['integrity_metrics'].append(integrity_metrics)
        
        # Log answer submission
        self.audit_logger.log_event(
            session_id=session_id,
            event_type="answer_submission",
            description=f"Answer submitted for question {current_question.question_id}",
            metadata={
                'question_id': current_question.question_id,
                'score': answer.score,
                'time_taken': time_taken,
                'integrity_score': integrity_metrics.overall_integrity_score
            }
        )
        
        # Determine next action
        next_action = self._determine_next_action(session_data)
        
        result = {
            'answer_score': answer.score,
            'answer_feedback': answer.feedback,
            'integrity_metrics': integrity_metrics,
            'session_complete': next_action['complete'],
            'next_question': next_action.get('question'),
            'session_progress': self._calculate_session_progress(session_data)
        }
        
        if next_action['complete']:
            # Generate final report
            report = self._generate_interview_report(session_id)
            result['interview_report'] = report
            
            # End session
            self._end_session(session_id)
        
        return result
    
    def _evaluate_answer(self, answer: Answer, question: Question) -> Dict[str, Any]:
        """Evaluate an answer and provide feedback."""
        evaluation = {
            'score': 0.0,
            'feedback': ""
        }
        
        try:
            if question.type == QuestionType.MULTIPLE_CHOICE:
                evaluation = self._evaluate_multiple_choice(answer, question)
            elif question.type == QuestionType.CODING:
                evaluation = self._evaluate_coding_answer(answer, question)
            elif question.type == QuestionType.CONCEPTUAL:
                evaluation = self._evaluate_conceptual_answer(answer, question)
            elif question.type == QuestionType.PRACTICAL:
                evaluation = self._evaluate_practical_answer(answer, question)
            
        except Exception as e:
            logger.error(f"Error evaluating answer: {e}")
            evaluation['score'] = 0.0
            evaluation['feedback'] = "Error evaluating answer. Please contact support."
        
        return evaluation
    
    def _evaluate_multiple_choice(self, answer: Answer, question: Question) -> Dict[str, Any]:
        """Evaluate multiple choice answer."""
        # Simple keyword matching for multiple choice
        expected_keywords = question.expected_answer.lower().split(',') if question.expected_answer else []
        answer_text = answer.answer_text.lower()
        
        matches = sum(1 for keyword in expected_keywords if keyword.strip() in answer_text)
        score = (matches / len(expected_keywords)) * 100 if expected_keywords else 0
        
        feedback = f"Score: {score:.1f}%. "
        if score >= 80:
            feedback += "Excellent answer!"
        elif score >= 60:
            feedback += "Good answer with room for improvement."
        else:
            feedback += "Answer needs improvement. Review the key concepts."
        
        return {'score': score, 'feedback': feedback}
    
    def _evaluate_coding_answer(self, answer: Answer, question: Question) -> Dict[str, Any]:
        """Evaluate coding answer."""
        score = 0.0
        feedback_parts = []
        
        # Check if code is provided
        code_to_evaluate = answer.code_snippet or answer.answer_text
        
        if not code_to_evaluate.strip():
            return {'score': 0.0, 'feedback': "No code provided."}
        
        # Basic code quality checks
        try:
            # Check for syntax (basic validation)
            if 'def ' in code_to_evaluate or 'class ' in code_to_evaluate:
                score += 30
                feedback_parts.append("Function/class structure present")
            
            # Check for key concepts based on question category
            if question.category == "python_programming":
                if any(keyword in code_to_evaluate.lower() for keyword in ['import', 'return', 'def']):
                    score += 20
                    feedback_parts.append("Proper Python syntax")
            
            elif question.category == "machine_learning":
                if any(keyword in code_to_evaluate.lower() for keyword in ['fit', 'predict', 'transform', 'model']):
                    score += 25
                    feedback_parts.append("ML workflow elements present")
            
            # Check for error handling
            if any(keyword in code_to_evaluate for keyword in ['try:', 'except', 'if', 'else']):
                score += 15
                feedback_parts.append("Error handling implemented")
            
            # Check for comments/documentation
            if '#' in code_to_evaluate or '"""' in code_to_evaluate:
                score += 10
                feedback_parts.append("Code documentation present")
            
            # Length and complexity bonus
            if len(code_to_evaluate.split('\n')) > 5:
                score += 10
                feedback_parts.append("Adequate implementation length")
            
            # Cap at 100
            score = min(100, score)
            
        except Exception as e:
            logger.error(f"Error evaluating code: {e}")
            score = 0
            feedback_parts.append("Code evaluation error")
        
        feedback = "Code evaluation: " + "; ".join(feedback_parts) if feedback_parts else "Basic code structure"
        feedback += f" (Score: {score:.1f}%)"
        
        return {'score': score, 'feedback': feedback}
    
    def _evaluate_conceptual_answer(self, answer: Answer, question: Question) -> Dict[str, Any]:
        """Evaluate conceptual answer using semantic similarity."""
        if not question.expected_answer:
            # Fallback to length-based scoring
            answer_length = len(answer.answer_text.split())
            if answer_length < 10:
                score = 20
                feedback = "Answer too brief"
            elif answer_length < 30:
                score = 50
                feedback = "Answer could be more detailed"
            elif answer_length < 100:
                score = 80
                feedback = "Good detailed answer"
            else:
                score = 90
                feedback = "Comprehensive answer"
            
            return {'score': score, 'feedback': feedback}
        
        # Use semantic similarity for evaluation
        from src.utils.nlp_utils import NLPProcessor
        nlp_processor = NLPProcessor()
        
        similarity = nlp_processor.calculate_semantic_similarity(
            answer.answer_text, question.expected_answer
        )
        
        score = similarity * 100
        
        # Adjust based on answer length
        answer_words = len(answer.answer_text.split())
        if answer_words < 10:
            score = min(score, 30)
        elif answer_words > 200:
            score = min(score + 10, 100)
        
        if score >= 80:
            feedback = "Excellent understanding demonstrated"
        elif score >= 60:
            feedback = "Good understanding with some gaps"
        elif score >= 40:
            feedback = "Partial understanding - needs improvement"
        else:
            feedback = "Limited understanding of the concept"
        
        return {'score': score, 'feedback': feedback}
    
    def _evaluate_practical_answer(self, answer: Answer, question: Question) -> Dict[str, Any]:
        """Evaluate practical/problem-solving answer."""
        score = 0.0
        feedback_parts = []
        
        answer_text = answer.answer_text.lower()
        
        # Check for problem-solving approach
        if any(keyword in answer_text for keyword in ['first', 'then', 'next', 'finally', 'step']):
            score += 25
            feedback_parts.append("Structured approach")
        
        # Check for analytical thinking
        if any(keyword in answer_text for keyword in ['analyze', 'evaluate', 'compare', 'consider']):
            score += 20
            feedback_parts.append("Analytical thinking demonstrated")
        
        # Check for specific technical terms
        if question.category in ["machine_learning", "data_science_fundamentals"]:
            tech_keywords = ['data', 'model', 'algorithm', 'feature', 'training', 'validation']
            matches = sum(1 for keyword in tech_keywords if keyword in answer_text)
            if matches >= 2:
                score += 20
                feedback_parts.append("Technical terminology used correctly")
        
        # Check for completeness
        answer_length = len(answer.answer_text.split())
        if answer_length > 50:
            score += 15
            feedback_parts.append("Comprehensive answer")
        elif answer_length > 20:
            score += 10
            feedback_parts.append("Adequate detail")
        
        # Check for examples
        if any(keyword in answer_text for keyword in ['example', 'instance', 'such as', 'like']):
            score += 10
            feedback_parts.append("Examples provided")
        
        # Check for conclusions
        if any(keyword in answer_text for keyword in ['conclusion', 'therefore', 'thus', 'in summary']):
            score += 10
            feedback_parts.append("Clear conclusion")
        
        score = min(100, score)
        feedback = "Practical answer evaluation: " + "; ".join(feedback_parts) if feedback_parts else "Basic response"
        feedback += f" (Score: {score:.1f}%)"
        
        return {'score': score, 'feedback': feedback}
    
    def _determine_next_action(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Determine whether to ask another question or end the session."""
        session = session_data['session']
        performance_history = session_data['performance_history']
        
        # Check if session should end
        if len(performance_history) >= self.max_questions_per_session:
            return {'complete': True}
        
        # Check session timeout
        session_duration = (datetime.now() - session.started_at).total_seconds()
        if session_duration > self.session_timeout:
            return {'complete': True}
        
        # Check if minimum questions reached and performance is very poor or excellent
        if len(performance_history) >= self.min_questions_per_session:
            recent_scores = [p['score'] for p in performance_history[-3:]]
            avg_recent_score = sum(recent_scores) / len(recent_scores)
            
            if avg_recent_score < 30 or avg_recent_score > 90:
                return {'complete': True}
        
        # Get next question
        next_question = self._select_next_question(session_data)
        
        if next_question:
            session.current_question = next_question
            session_data['remaining_questions'] = [
                q for q in session_data['remaining_questions'] if q.question_id != next_question.question_id
            ]
            return {'complete': False, 'question': next_question}
        else:
            return {'complete': True}
    
    def _select_next_question(self, session_data: Dict[str, Any]) -> Optional[Question]:
        """Select the next question based on adaptive algorithm."""
        session = session_data['session']
        performance_history = session_data['performance_history']
        
        if not performance_history:
            # First question already selected
            return None
        
        # Get recent performance
        recent_performance = performance_history[-3:]  # Last 3 answers
        avg_recent_score = sum(p['score'] for p in recent_performance) / len(recent_performance)
        
        # Adjust difficulty based on performance
        current_difficulty = session.difficulty_level
        new_difficulty = self._adjust_difficulty(current_difficulty, avg_recent_score)
        
        # Identify weak areas
        weak_categories = self._identify_weak_categories(session_data['category_performance'])
        
        # Select next question
        if weak_categories:
            # Focus on weak areas
            category_questions = self.question_bank.get_questions_by_category(
                weak_categories[0], new_difficulty
            )
        else:
            # Get questions for new difficulty
            category_questions = self.question_bank.get_questions_by_difficulty(new_difficulty)
        
        # Filter out already asked questions
        asked_question_ids = {q.question_id for q in session_data['asked_questions']}
        available_questions = [q for q in category_questions if q.question_id not in asked_question_ids]
        
        if available_questions:
            session.difficulty_level = new_difficulty
            return available_questions[0]
        
        # Fallback to any remaining question
        if session_data['remaining_questions']:
            return session_data['remaining_questions'][0]
        
        return None
    
    def _adjust_difficulty(self, current_difficulty: DifficultyLevel, avg_score: float) -> DifficultyLevel:
        """Adjust difficulty based on performance."""
        difficulty_order = [
            DifficultyLevel.BEGINNER,
            DifficultyLevel.INTERMEDIATE,
            DifficultyLevel.ADVANCED,
            DifficultyLevel.EXPERT
        ]
        
        current_index = difficulty_order.index(current_difficulty)
        
        if avg_score > 85 and current_index < len(difficulty_order) - 1:
            # Increase difficulty
            return difficulty_order[current_index + self.difficulty_step_up]
        elif avg_score < 40 and current_index > 0:
            # Decrease difficulty
            return difficulty_order[current_index - self.difficulty_step_down]
        
        return current_difficulty
    
    def _identify_weak_categories(self, category_performance: Dict[str, List[float]]) -> List[str]:
        """Identify categories where candidate is performing poorly."""
        weak_categories = []
        
        for category, scores in category_performance.items():
            if scores:
                avg_score = sum(scores) / len(scores)
                if avg_score < 60:  # Below 60% is considered weak
                    weak_categories.append((category, avg_score))
        
        # Sort by worst performance
        weak_categories.sort(key=lambda x: x[1])
        return [cat[0] for cat in weak_categories]
    
    def _calculate_session_progress(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate session progress metrics."""
        session = session_data['session']
        performance_history = session_data['performance_history']
        
        progress = {
            'questions_asked': len(performance_history),
            'max_questions': self.max_questions_per_session,
            'current_difficulty': session.difficulty_level.value,
            'average_score': 0.0,
            'time_elapsed': (datetime.now() - session.started_at).total_seconds(),
            'integrity_score': session.integrity_score
        }
        
        if performance_history:
            progress['average_score'] = sum(p['score'] for p in performance_history) / len(performance_history)
        
        return progress
    
    def _generate_interview_report(self, session_id: str) -> InterviewReport:
        """Generate comprehensive interview report."""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session_data = self.active_sessions[session_id]
        session = session_data['session']
        performance_history = session_data['performance_history']
        category_performance = session_data['category_performance']
        
        # Calculate overall score
        overall_score = sum(p['score'] for p in performance_history) / len(performance_history) if performance_history else 0
        
        # Calculate domain scores
        domain_scores = {}
        for category, scores in category_performance.items():
            if scores:
                domain_scores[category] = sum(scores) / len(scores)
        
        # Generate question results
        question_results = []
        for perf in performance_history:
            question = next(q for q in session_data['asked_questions'] if q.question_id == perf['question_id'])
            question_results.append({
                'question_text': question.text,
                'question_category': question.category,
                'question_difficulty': question.difficulty.value,
                'score': perf['score'],
                'time_taken': perf['time_taken']
            })
        
        # Identify strengths and weaknesses
        strengths = []
        weaknesses = []
        
        for category, avg_score in domain_scores.items():
            if avg_score >= 80:
                strengths.append(f"Strong performance in {category.replace('_', ' ')}")
            elif avg_score < 50:
                weaknesses.append(f"Needs improvement in {category.replace('_', ' ')}")
        
        # Generate recommendations
        recommendations = self._generate_recommendations(domain_scores, overall_score)
        
        # Get integrity metrics
        integrity_summary = self._summarize_integrity_metrics(session_data['integrity_metrics'])
        
        # Compliance summary
        compliance_summary = {
            'overall_status': 'compliant' if session.integrity_score > Config.INTEGRITY_SCORE_THRESHOLD else 'flagged',
            'integrity_score': session.integrity_score,
            'violations': len([m for m in session_data['integrity_metrics'] if m.overall_integrity_score < 50])
        }
        
        report = InterviewReport(
            session_id=session_id,
            candidate_id=session.candidate_id,
            overall_score=overall_score,
            domain_scores=domain_scores,
            question_results=question_results,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            integrity_metrics=integrity_summary,
            compliance_summary=compliance_summary,
            generated_at=datetime.now()
        )
        
        # Log report generation
        self.audit_logger.log_event(
            session_id=session_id,
            event_type="interview_report_generated",
            description=f"Generated interview report with overall score {overall_score:.2f}",
            metadata={
                'overall_score': overall_score,
                'domain_scores': domain_scores,
                'integrity_score': session.integrity_score
            }
        )
        
        return report
    
    def _generate_recommendations(self, domain_scores: Dict[str, float], overall_score: float) -> List[str]:
        """Generate personalized recommendations."""
        recommendations = []
        
        if overall_score < 50:
            recommendations.append("Consider additional training and practice before advancing to technical roles")
        elif overall_score < 70:
            recommendations.append("Focus on strengthening fundamental concepts")
        
        # Category-specific recommendations
        for category, score in domain_scores.items():
            if score < 60:
                if category == "python_programming":
                    recommendations.append("Practice Python programming with focus on data structures and algorithms")
                elif category == "machine_learning":
                    recommendations.append("Study machine learning fundamentals and practical implementations")
                elif category == "agentic_ai_systems":
                    recommendations.append("Learn about agent architectures and coordination patterns")
                elif category == "prompt_engineering":
                    recommendations.append("Practice prompt design and LLM interaction patterns")
        
        if not recommendations:
            recommendations.append("Strong performance across all areas. Consider advanced topics and specialization")
        
        return recommendations
    
    def _summarize_integrity_metrics(self, integrity_metrics: List[IntegrityMetrics]) -> Dict[str, Any]:
        """Summarize integrity metrics across the session."""
        if not integrity_metrics:
            return {
                'average_integrity_score': 100.0,
                'copy_paste_incidents': 0,
                'timing_anomalies': 0,
                'browser_anomalies': 0
            }
        
        summary = {
            'average_integrity_score': sum(m.overall_integrity_score for m in integrity_metrics) / len(integrity_metrics),
            'copy_paste_incidents': sum(1 for m in integrity_metrics if m.copy_paste_detected),
            'timing_anomalies': sum(1 for m in integrity_metrics if m.unusual_timing_patterns),
            'browser_anomalies': sum(1 for m in integrity_metrics if m.browser_anomalies),
            'total_flags': sum(len(m.flags) for m in integrity_metrics)
        }
        
        return summary
    
    def _end_session(self, session_id: str):
        """End an interview session and clean up."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]['session']
            session.is_active = False
            
            # Log session end
            self.audit_logger.log_event(
                session_id=session_id,
                event_type="interview_session_end",
                description=f"Ended interview session for candidate {session.candidate_id}",
                metadata={
                    'candidate_id': session.candidate_id,
                    'duration_seconds': (datetime.now() - session.started_at).total_seconds(),
                    'final_integrity_score': session.integrity_score
                }
            )
            
            # Clean up monitoring
            self.integrity_monitor.cleanup_session_data(session_id)
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            logger.info(f"Ended interview session {session_id}")
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current status of an interview session."""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session_data = self.active_sessions[session_id]
        session = session_data['session']
        
        return {
            'session_id': session_id,
            'candidate_id': session.candidate_id,
            'is_active': session.is_active,
            'current_question': session.current_question.text if session.current_question else None,
            'questions_asked': len(session.answers),
            'current_difficulty': session.difficulty_level.value,
            'integrity_score': session.integrity_score,
            'session_duration': (datetime.now() - session.started_at).total_seconds()
        }
