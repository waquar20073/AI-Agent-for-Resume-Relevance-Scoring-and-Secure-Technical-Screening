from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import uuid
import hashlib
import re
import logging
from src.utils.data_models import InterviewSession, Answer, IntegrityMetrics, ComplianceLog
from config.settings import Config

logger = logging.getLogger(__name__)

class IntegrityMonitor:
    def __init__(self):
        self.integrity_threshold = Config.INTEGRITY_SCORE_THRESHOLD
        self.session_data = {}  # In production, this would be a database
        
        # Suspicious patterns for cheating detection
        self.suspicious_patterns = {
            'copy_paste': [
                r'^\s*$',  # Empty answers
                r'^.{1,5}$',  # Very short answers
                r'^(idk|don\'t know|no idea|unsure)\s*$',  # Generic non-answers
                r'^[a-zA-Z]\s*[a-zA-Z]\s*[a-zA-Z]\s*$',  # Random letters
            ],
            'repetition': [
                r'(.{20,})\1{2,}',  # Repeated text
            ],
            'formatting_anomalies': [
                r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\{\}\"\']+',  # Excessive special characters
                r'\s{5,}',  # Excessive whitespace
            ]
        }
        
        # Time-based anomaly thresholds
        self.time_thresholds = {
            'min_answer_time': 5,  # seconds
            'max_answer_time': 1800,  # 30 minutes
            'suspiciously_fast': 10,  # seconds
            'suspiciously_slow': 600  # 10 minutes
        }
    
    def initialize_session_monitoring(self, session_id: str, candidate_id: str) -> Dict[str, Any]:
        """Initialize monitoring for a new interview session."""
        session_data = {
            'session_id': session_id,
            'candidate_id': candidate_id,
            'start_time': datetime.now(),
            'answers': [],
            'time_patterns': [],
            'text_patterns': [],
            'browser_events': [],
            'keystroke_data': [],
            'integrity_flags': [],
            'current_integrity_score': 100.0
        }
        
        self.session_data[session_id] = session_data
        
        logger.info(f"Initialized integrity monitoring for session {session_id}")
        return session_data
    
    def analyze_answer_integrity(self, session_id: str, answer: Answer, question_text: str) -> IntegrityMetrics:
        """Analyze an answer for integrity violations."""
        if session_id not in self.session_data:
            raise ValueError(f"Session {session_id} not found in monitoring data")
        
        session = self.session_data[session_id]
        integrity_flags = []
        
        # Analyze text patterns
        text_analysis = self._analyze_text_integrity(answer.answer_text)
        integrity_flags.extend(text_analysis['flags'])
        
        # Analyze timing patterns
        timing_analysis = self._analyze_timing_integrity(answer.time_taken, question_text)
        integrity_flags.extend(timing_analysis['flags'])
        
        # Analyze consistency with previous answers
        consistency_analysis = self._analyze_answer_consistency(answer, session['answers'])
        integrity_flags.extend(consistency_analysis['flags'])
        
        # Calculate integrity scores
        text_integrity_score = text_analysis['score']
        timing_integrity_score = timing_analysis['score']
        consistency_score = consistency_analysis['score']
        
        # Calculate overall integrity score
        overall_score = (text_integrity_score + timing_integrity_score + consistency_score) / 3
        
        # Update session data
        session['answers'].append({
            'question_id': answer.question_id,
            'answer_text': answer.answer_text,
            'time_taken': answer.time_taken,
            'integrity_score': overall_score,
            'flags': integrity_flags,
            'timestamp': answer.submitted_at
        })
        
        # Update session integrity score
        session['current_integrity_score'] = self._calculate_session_integrity_score(session)
        
        # Create integrity metrics
        metrics = IntegrityMetrics(
            session_id=session_id,
            copy_paste_detected=any('copy_paste' in flag for flag in integrity_flags),
            unusual_timing_patterns=any('timing' in flag for flag in integrity_flags),
            browser_anomalies=any('browser' in flag for flag in integrity_flags),
            answer_consistency_score=consistency_score,
            overall_integrity_score=overall_score,
            flags=integrity_flags
        )
        
        # Log integrity analysis
        self._log_integrity_analysis(session_id, metrics)
        
        return metrics
    
    def _analyze_text_integrity(self, answer_text: str) -> Dict[str, Any]:
        """Analyze answer text for cheating indicators."""
        result = {'score': 100.0, 'flags': []}
        
        if not answer_text or len(answer_text.strip()) < 3:
            result['score'] = 0.0
            result['flags'].append('copy_paste_empty_answer')
            return result
        
        # Check for suspicious patterns
        for pattern_type, patterns in self.suspicious_patterns.items():
            for pattern in patterns:
                if re.search(pattern, answer_text, re.IGNORECASE):
                    result['score'] -= 20
                    result['flags'].append(f'{pattern_type}_detected')
        
        # Check for answer length appropriateness
        answer_length = len(answer_text.strip())
        if answer_length < 10:
            result['score'] -= 30
            result['flags'].append('copy_paste_too_short')
        elif answer_length > 2000:  # Suspiciously long
            result['score'] -= 15
            result['flags'].append('copy_paste_too_long')
        
        # Check for code-like patterns in non-coding questions
        if self._contains_suspicious_code(answer_text):
            result['score'] -= 25
            result['flags'].append('copy_paste_suspicious_code')
        
        # Calculate text similarity with common sources (simplified)
        if self._matches_common_template(answer_text):
            result['score'] -= 20
            result['flags'].append('copy_paste_template_match')
        
        result['score'] = max(0, result['score'])
        return result
    
    def _analyze_timing_integrity(self, time_taken: int, question_text: str) -> Dict[str, Any]:
        """Analyze answer timing for anomalies."""
        result = {'score': 100.0, 'flags': []}
        
        # Check for suspiciously fast answers
        if time_taken < self.time_thresholds['suspiciously_fast']:
            result['score'] -= 40
            result['flags'].append('timing_suspiciously_fast')
        elif time_taken < self.time_thresholds['min_answer_time']:
            result['score'] -= 20
            result['flags'].append('timing_too_fast')
        
        # Check for suspiciously slow answers
        if time_taken > self.time_thresholds['suspiciously_slow']:
            result['score'] -= 30
            result['flags'].append('timing_suspiciously_slow')
        elif time_taken > self.time_thresholds['max_answer_time']:
            result['score'] -= 15
            result['flags'].append('timing_too_slow')
        
        # Adjust based on question complexity (simplified)
        question_complexity = self._estimate_question_complexity(question_text)
        expected_time = question_complexity * 60  # 1 minute per complexity unit
        
        if abs(time_taken - expected_time) > expected_time * 0.8:
            result['score'] -= 15
            result['flags'].append('timing_unexpected_for_complexity')
        
        result['score'] = max(0, result['score'])
        return result
    
    def _analyze_answer_consistency(self, current_answer: Answer, previous_answers: List[Dict]) -> Dict[str, Any]:
        """Analyze consistency of current answer with previous answers."""
        result = {'score': 100.0, 'flags': []}
        
        if not previous_answers:
            return result
        
        # Analyze writing style consistency
        style_consistency = self._analyze_writing_style_consistency(current_answer.answer_text, previous_answers)
        if style_consistency < 0.7:
            result['score'] -= 20
            result['flags'].append('consistency_style_change')
        
        # Analyze knowledge level consistency
        knowledge_consistency = self._analyze_knowledge_consistency(current_answer, previous_answers)
        if knowledge_consistency < 0.6:
            result['score'] -= 25
            result['flags'].append('consistency_knowledge_level_change')
        
        # Check for repeated answers
        if self._is_repeated_answer(current_answer.answer_text, previous_answers):
            result['score'] -= 35
            result['flags'].append('consistency_repeated_answer')
        
        result['score'] = max(0, result['score'])
        return result
    
    def _contains_suspicious_code(self, text: str) -> bool:
        """Check if text contains suspicious code patterns."""
        code_indicators = [
            r'function\s+\w+\s*\(',
            r'class\s+\w+\s*:',
            r'import\s+\w+',
            r'def\s+\w+\s*\(',
            r'print\s*\(',
            r'console\.log\s*\('
        ]
        
        code_matches = sum(1 for pattern in code_indicators if re.search(pattern, text))
        return code_matches > 2  # More than 2 code indicators is suspicious
    
    def _matches_common_template(self, text: str) -> bool:
        """Check if answer matches common online templates."""
        template_phrases = [
            "this is a great question",
            "i would approach this by",
            "the best way to solve this is",
            "in my experience",
            "it depends on the context",
            "there are multiple ways to"
        ]
        
        template_count = sum(1 for phrase in template_phrases if phrase.lower() in text.lower())
        return template_count >= 2
    
    def _estimate_question_complexity(self, question_text: str) -> int:
        """Estimate question complexity on a scale of 1-5."""
        complexity_indicators = {
            1: ['what is', 'define', 'name', 'list'],
            2: ['explain', 'describe', 'how does'],
            3: ['compare', 'contrast', 'analyze'],
            4: ['design', 'implement', 'create'],
            5: ['optimize', 'architect', 'solve complex']
        }
        
        text_lower = question_text.lower()
        max_complexity = 1
        
        for complexity, indicators in complexity_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                max_complexity = max(max_complexity, complexity)
        
        return max_complexity
    
    def _analyze_writing_style_consistency(self, current_text: str, previous_answers: List[Dict]) -> float:
        """Analyze writing style consistency with previous answers."""
        if not previous_answers:
            return 1.0
        
        # Simple style metrics
        def get_style_metrics(text):
            words = text.split()
            sentences = text.split('.')
            return {
                'avg_word_length': sum(len(word) for word in words) / len(words) if words else 0,
                'avg_sentence_length': sum(len(sentence.split()) for sentence in sentences) / len(sentences) if sentences else 0,
                'punctuation_ratio': text.count('.') + text.count(',') + text.count('!') + text.count('?'),
                'capitalization_ratio': sum(1 for c in text if c.isupper()) / len(text) if text else 0
            }
        
        current_style = get_style_metrics(current_text)
        previous_styles = [get_style_metrics(ans['answer_text']) for ans in previous_answers[-5:]]  # Last 5 answers
        
        # Calculate average style metrics from previous answers
        avg_style = {
            key: sum(style[key] for style in previous_styles) / len(previous_styles)
            for key in current_style.keys()
        }
        
        # Calculate consistency score
        consistency_scores = []
        for key in current_style.keys():
            if avg_style[key] > 0:
                diff = abs(current_style[key] - avg_style[key]) / avg_style[key]
                consistency_scores.append(max(0, 1 - diff))
        
        return sum(consistency_scores) / len(consistency_scores) if consistency_scores else 1.0
    
    def _analyze_knowledge_consistency(self, current_answer: Answer, previous_answers: List[Dict]) -> float:
        """Analyze knowledge level consistency."""
        if not previous_answers:
            return 1.0
        
        # Simple heuristic: check if answer quality is consistent
        current_quality = self._assess_answer_quality(current_answer.answer_text)
        previous_qualities = [self._assess_answer_quality(ans['answer_text']) for ans in previous_answers[-3:]]
        
        if not previous_qualities:
            return 1.0
        
        avg_previous_quality = sum(previous_qualities) / len(previous_qualities)
        quality_diff = abs(current_quality - avg_previous_quality)
        
        return max(0, 1 - quality_diff)
    
    def _assess_answer_quality(self, answer_text: str) -> float:
        """Simple answer quality assessment."""
        if not answer_text:
            return 0.0
        
        quality_score = 0.0
        
        # Length factor
        length = len(answer_text.strip())
        if 50 <= length <= 500:
            quality_score += 0.3
        elif 500 < length <= 1000:
            quality_score += 0.4
        elif length > 1000:
            quality_score += 0.2
        
        # Technical content factor
        technical_terms = ['algorithm', 'function', 'method', 'approach', 'implement', 'optimize']
        tech_count = sum(1 for term in technical_terms if term.lower() in answer_text.lower())
        quality_score += min(0.3, tech_count * 0.1)
        
        # Structure factor
        if '.' in answer_text and answer_text.count('.') > 2:
            quality_score += 0.2
        
        # Explanation factor
        explanation_words = ['because', 'therefore', 'however', 'additionally', 'furthermore']
        expl_count = sum(1 for word in explanation_words if word.lower() in answer_text.lower())
        quality_score += min(0.2, expl_count * 0.05)
        
        return min(1.0, quality_score)
    
    def _is_repeated_answer(self, current_text: str, previous_answers: List[Dict]) -> bool:
        """Check if current answer is a repeat of previous answers."""
        current_hash = hashlib.md5(current_text.lower().strip().encode()).hexdigest()
        
        for ans in previous_answers:
            previous_hash = hashlib.md5(ans['answer_text'].lower().strip().encode()).hexdigest()
            if current_hash == previous_hash:
                return True
        
        return False
    
    def _calculate_session_integrity_score(self, session_data: Dict) -> float:
        """Calculate overall integrity score for the session."""
        if not session_data['answers']:
            return 100.0
        
        answer_scores = [ans['integrity_score'] for ans in session_data['answers']]
        return sum(answer_scores) / len(answer_scores)
    
    def record_browser_event(self, session_id: str, event_type: str, details: Dict[str, Any]):
        """Record browser events for integrity monitoring."""
        if session_id not in self.session_data:
            return
        
        event = {
            'type': event_type,
            'details': details,
            'timestamp': datetime.now()
        }
        
        self.session_data[session_id]['browser_events'].append(event)
        
        # Check for suspicious browser activity
        if event_type in ['tab_switch', 'window_focus_lost', 'copy_paste_detected']:
            self.session_data[session_id]['integrity_flags'].append(f'browser_{event_type}')
    
    def get_session_integrity_report(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive integrity report for a session."""
        if session_id not in self.session_data:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.session_data[session_id]
        
        report = {
            'session_id': session_id,
            'candidate_id': session['candidate_id'],
            'overall_integrity_score': session['current_integrity_score'],
            'risk_level': 'HIGH' if session['current_integrity_score'] < self.integrity_threshold else 'LOW',
            'total_answers': len(session['answers']),
            'integrity_flags': session['integrity_flags'],
            'browser_events_count': len(session['browser_events']),
            'session_duration': (datetime.now() - session['start_time']).total_seconds(),
            'answer_analysis': self._analyze_answer_patterns(session['answers']),
            'recommendations': self._generate_integrity_recommendations(session)
        }
        
        return report
    
    def _analyze_answer_patterns(self, answers: List[Dict]) -> Dict[str, Any]:
        """Analyze patterns in answers for integrity assessment."""
        if not answers:
            return {}
        
        times = [ans['time_taken'] for ans in answers]
        scores = [ans['integrity_score'] for ans in answers]
        
        return {
            'average_answer_time': sum(times) / len(times),
            'fastest_answer': min(times),
            'slowest_answer': max(times),
            'average_integrity_score': sum(scores) / len(scores),
            'lowest_integrity_score': min(scores),
            'integrity_score_variance': max(scores) - min(scores)
        }
    
    def _generate_integrity_recommendations(self, session_data: Dict) -> List[str]:
        """Generate recommendations based on integrity analysis."""
        recommendations = []
        
        if session_data['current_integrity_score'] < self.integrity_threshold:
            recommendations.append("Review session for potential integrity violations")
        
        if 'browser_tab_switch' in session_data['integrity_flags']:
            recommendations.append("Candidate switched browser tabs during interview")
        
        if 'copy_paste_detected' in session_data['integrity_flags']:
            recommendations.append("Copy-paste activity detected during interview")
        
        fast_answers = [ans for ans in session_data['answers'] if ans['time_taken'] < 10]
        if len(fast_answers) > len(session_data['answers']) * 0.3:
            recommendations.append("Multiple suspiciously fast answers detected")
        
        low_score_answers = [ans for ans in session_data['answers'] if ans['integrity_score'] < 50]
        if len(low_score_answers) > len(session_data['answers']) * 0.2:
            recommendations.append("Multiple low-integrity answers detected")
        
        return recommendations
    
    def _log_integrity_analysis(self, session_id: str, metrics: IntegrityMetrics):
        """Log integrity analysis for audit purposes."""
        log_entry = ComplianceLog(
            log_id=str(uuid.uuid4()),
            session_id=session_id,
            event_type="integrity_analysis",
            description=f"Integrity analysis for session {session_id}",
            severity="high" if metrics.overall_integrity_score < self.integrity_threshold else "low",
            metadata={
                'overall_integrity_score': metrics.overall_integrity_score,
                'copy_paste_detected': metrics.copy_paste_detected,
                'unusual_timing_patterns': metrics.unusual_timing_patterns,
                'browser_anomalies': metrics.browser_anomalies,
                'answer_consistency_score': metrics.answer_consistency_score,
                'flags_count': len(metrics.flags)
            },
            timestamp=datetime.now()
        )
        
        logger.info(f"Integrity analysis log created: {log_entry.log_id}")
    
    def cleanup_session_data(self, session_id: str):
        """Clean up session data after interview completion."""
        if session_id in self.session_data:
            del self.session_data[session_id]
            logger.info(f"Cleaned up integrity monitoring data for session {session_id}")
