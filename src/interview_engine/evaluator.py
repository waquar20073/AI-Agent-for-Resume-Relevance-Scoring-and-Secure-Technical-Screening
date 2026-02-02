from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from src.utils.data_models import InterviewReport, Question, Answer, ScoringResult
from src.utils.nlp_utils import NLPProcessor
from src.compliance.bias_detector import BiasDetector

logger = logging.getLogger(__name__)

class InterviewEvaluator:
    def __init__(self):
        self.nlp_processor = NLPProcessor()
        self.bias_detector = BiasDetector()
        
        # Evaluation criteria weights
        self.evaluation_weights = {
            'technical_accuracy': 0.4,
            'communication_clarity': 0.2,
            'problem_solving_approach': 0.2,
            'depth_of_understanding': 0.2
        }
        
        # Scoring rubrics for different question types
        self.scoring_rubrics = {
            'conceptual': {
                'excellent': {'range': (90, 100), 'description': 'Comprehensive understanding with examples'},
                'good': {'range': (70, 89), 'description': 'Solid understanding with minor gaps'},
                'satisfactory': {'range': (50, 69), 'description': 'Basic understanding with significant gaps'},
                'poor': {'range': (0, 49), 'description': 'Limited or incorrect understanding'}
            },
            'coding': {
                'excellent': {'range': (90, 100), 'description': 'Correct, efficient, well-structured code'},
                'good': {'range': (70, 89), 'description': 'Functional code with minor issues'},
                'satisfactory': {'range': (50, 69), 'description': 'Partially working code with logical errors'},
                'poor': {'range': (0, 49), 'description': 'Non-functional or incorrect code'}
            },
            'practical': {
                'excellent': {'range': (90, 100), 'description': 'Well-reasoned solution with multiple approaches'},
                'good': {'range': (70, 89), 'description': 'Logical solution with good reasoning'},
                'satisfactory': {'range': (50, 69), 'description': 'Basic solution with limited reasoning'},
                'poor': {'range': (0, 49), 'description': 'Illogical or incomplete solution'}
            }
        }
    
    def evaluate_candidate_performance(self, interview_report: InterviewReport) -> Dict[str, Any]:
        """Comprehensive evaluation of candidate performance."""
        evaluation = {
            'overall_assessment': self._get_overall_assessment(interview_report.overall_score),
            'technical_competence': self._evaluate_technical_competence(interview_report),
            'communication_skills': self._evaluate_communication_skills(interview_report),
            'problem_solving_ability': self._evaluate_problem_solving(interview_report),
            'learning_potential': self._assess_learning_potential(interview_report),
            'role_suitability': self._assess_role_suitability(interview_report),
            'detailed_feedback': self._generate_detailed_feedback(interview_report),
            'recommendations': self._generate_hiring_recommendations(interview_report)
        }
        
        return evaluation
    
    def _get_overall_assessment(self, overall_score: float) -> Dict[str, Any]:
        """Get overall assessment based on score."""
        if overall_score >= 90:
            return {
                'level': 'Exceptional',
                'description': 'Outstanding performance across all areas',
                'recommendation': 'Strong Hire'
            }
        elif overall_score >= 80:
            return {
                'level': 'Excellent',
                'description': 'Strong performance with minor areas for improvement',
                'recommendation': 'Hire'
            }
        elif overall_score >= 70:
            return {
                'level': 'Good',
                'description': 'Solid performance with some gaps',
                'recommendation': 'Consider Hire'
            }
        elif overall_score >= 60:
            return {
                'level': 'Satisfactory',
                'description': 'Meets basic requirements but needs development',
                'recommendation': 'Consider for Junior Role'
            }
        elif overall_score >= 50:
            return {
                'level': 'Needs Improvement',
                'description': 'Significant gaps in knowledge',
                'recommendation': 'Not Recommended'
            }
        else:
            return {
                'level': 'Poor',
                'description': 'Does not meet requirements',
                'recommendation': 'Not Recommended'
            }
    
    def _evaluate_technical_competence(self, report: InterviewReport) -> Dict[str, Any]:
        """Evaluate technical competence across domains."""
        domain_scores = report.domain_scores
        
        # Calculate technical competence score
        technical_domains = [
            'data_science_fundamentals', 'statistics_probability', 'machine_learning',
            'deep_learning', 'python_programming', 'sql_databases'
        ]
        
        technical_scores = [score for domain, score in domain_scores.items() 
                           if domain in technical_domains]
        
        avg_technical_score = sum(technical_scores) / len(technical_scores) if technical_scores else 0
        
        # Identify technical strengths and weaknesses
        technical_strengths = []
        technical_weaknesses = []
        
        for domain, score in domain_scores.items():
            if domain in technical_domains:
                if score >= 80:
                    technical_strengths.append(domain.replace('_', ' ').title())
                elif score < 60:
                    technical_weaknesses.append(domain.replace('_', ' ').title())
        
        return {
            'score': avg_technical_score,
            'strengths': technical_strengths,
            'weaknesses': technical_weaknesses,
            'assessment': self._get_competence_level(avg_technical_score)
        }
    
    def _evaluate_communication_skills(self, report: InterviewReport) -> Dict[str, Any]:
        """Evaluate communication skills based on answer quality."""
        # Analyze answer patterns for communication indicators
        total_questions = len(report.question_results)
        if total_questions == 0:
            return {'score': 0, 'assessment': 'Insufficient data'}
        
        # Check for clarity indicators (simplified heuristic)
        clarity_indicators = []
        for result in report.question_results:
            # In a real implementation, this would analyze the actual answer text
            # For now, we'll use the score as a proxy
            if result['score'] >= 70:
                clarity_indicators.append(1)
            else:
                clarity_indicators.append(0)
        
        clarity_score = (sum(clarity_indicators) / len(clarity_indicators)) * 100
        
        # Assess communication based on score distribution
        consistent_performance = all(50 <= score <= 90 for score in [r['score'] for r in report.question_results])
        
        if clarity_score >= 80 and consistent_performance:
            assessment = 'Excellent communicator'
        elif clarity_score >= 60:
            assessment = 'Good communicator'
        elif clarity_score >= 40:
            assessment = 'Adequate communicator'
        else:
            assessment = 'Needs communication improvement'
        
        return {
            'score': clarity_score,
            'assessment': assessment,
            'consistency': consistent_performance
        }
    
    def _evaluate_problem_solving(self, report: InterviewReport) -> Dict[str, Any]:
        """Evaluate problem-solving approach and methodology."""
        # Focus on practical and coding questions
        problem_solving_questions = [
            result for result in report.question_results
            if any(category in result['question_category'] 
                  for category in ['practical', 'coding', 'machine_learning'])
        ]
        
        if not problem_solving_questions:
            return {'score': 0, 'assessment': 'No problem-solving questions evaluated'}
        
        # Calculate problem-solving score
        ps_scores = [result['score'] for result in problem_solving_questions]
        avg_ps_score = sum(ps_scores) / len(ps_scores)
        
        # Analyze approach consistency
        score_variance = max(ps_scores) - min(ps_scores)
        consistent_approach = score_variance < 30
        
        # Time analysis (if available)
        avg_time = sum(result.get('time_taken', 0) for result in problem_solving_questions) / len(problem_solving_questions)
        appropriate_timing = 60 <= avg_time <= 600  # 1-10 minutes per question
        
        assessment = self._get_problem_solving_assessment(avg_ps_score, consistent_approach, appropriate_timing)
        
        return {
            'score': avg_ps_score,
            'assessment': assessment,
            'consistency': consistent_approach,
            'timing_appropriateness': appropriate_timing,
            'questions_evaluated': len(problem_solving_questions)
        }
    
    def _assess_learning_potential(self, report: InterviewReport) -> Dict[str, Any]:
        """Assess candidate's learning and growth potential."""
        # Look for improvement patterns across difficulty levels
        difficulty_progression = {}
        for result in report.question_results:
            difficulty = result['question_difficulty']
            if difficulty not in difficulty_progression:
                difficulty_progression[difficulty] = []
            difficulty_progression[difficulty].append(result['score'])
        
        # Calculate improvement indicators
        improvement_score = 0
        total_indicators = 0
        
        # Check if performance improves with familiarity
        if len(report.question_results) >= 3:
            first_half = report.question_results[:len(report.question_results)//2]
            second_half = report.question_results[len(report.question_results)//2:]
            
            first_avg = sum(r['score'] for r in first_half) / len(first_half)
            second_avg = sum(r['score'] for r in second_half) / len(second_half)
            
            if second_avg > first_avg:
                improvement_score += 20
        
        # Check adaptability across categories
        category_scores = list(report.domain_scores.values())
        if category_scores:
            score_std_dev = (sum((x - sum(category_scores)/len(category_scores))**2 for x in category_scores) / len(category_scores)) ** 0.5
            balanced_performance = score_std_dev < 20
            if balanced_performance:
                improvement_score += 15
        
        # Check handling of difficult questions
        difficult_scores = difficulty_progression.get('advanced', []) + difficulty_progression.get('expert', [])
        if difficult_scores:
            difficult_avg = sum(difficult_scores) / len(difficult_scores)
            if difficult_avg >= 60:
                improvement_score += 25
        
        total_indicators = 3  # Maximum possible indicators
        learning_score = min(100, improvement_score)
        
        if learning_score >= 80:
            assessment = 'High learning potential'
        elif learning_score >= 60:
            assessment = 'Good learning potential'
        elif learning_score >= 40:
            assessment = 'Moderate learning potential'
        else:
            assessment = 'Limited learning potential'
        
        return {
            'score': learning_score,
            'assessment': assessment,
            'improvement_indicators': improvement_score,
            'max_indicators': total_indicators
        }
    
    def _assess_role_suitability(self, report: InterviewReport) -> Dict[str, Any]:
        """Assess suitability for different roles."""
        role_requirements = {
            'Data Scientist': {
                'critical_domains': ['data_science_fundamentals', 'statistics_probability', 'machine_learning'],
                'preferred_domains': ['python_programming', 'sql_databases'],
                'min_overall_score': 70
            },
            'ML Engineer': {
                'critical_domains': ['machine_learning', 'python_programming', 'deep_learning'],
                'preferred_domains': ['mlops_devops', 'cloud_platforms'],
                'min_overall_score': 75
            },
            'Agentic AI Developer': {
                'critical_domains': ['agentic_ai_systems', 'prompt_engineering', 'llm_fundamentals'],
                'preferred_domains': ['python_programming', 'machine_learning'],
                'min_overall_score': 80
            },
            'Data Analyst': {
                'critical_domains': ['data_science_fundamentals', 'sql_databases', 'python_programming'],
                'preferred_domains': ['statistics_probability'],
                'min_overall_score': 65
            }
        }
        
        suitability_scores = {}
        
        for role, requirements in role_requirements.items():
            score = 0
            max_score = 0
            
            # Critical domains (40% weight)
            for domain in requirements['critical_domains']:
                max_score += 40
                if domain in report.domain_scores:
                    score += (report.domain_scores[domain] / 100) * 40
            
            # Preferred domains (20% weight)
            for domain in requirements['preferred_domains']:
                max_score += 20
                if domain in report.domain_scores:
                    score += (report.domain_scores[domain] / 100) * 20
            
            # Overall score (40% weight)
            max_score += 40
            if report.overall_score >= requirements['min_overall_score']:
                score += (report.overall_score / 100) * 40
            
            # Calculate suitability percentage
            suitability = (score / max_score) * 100 if max_score > 0 else 0
            suitability_scores[role] = suitability
        
        # Find best fit role
        best_role = max(suitability_scores, key=suitability_scores.get) if suitability_scores else None
        
        return {
            'role_scores': suitability_scores,
            'best_fit_role': best_role,
            'best_fit_score': suitability_scores.get(best_role, 0) if best_role else 0
        }
    
    def _generate_detailed_feedback(self, report: InterviewReport) -> Dict[str, Any]:
        """Generate detailed feedback for the candidate."""
        feedback = {
            'strengths': report.strengths.copy(),
            'areas_for_improvement': report.weaknesses.copy(),
            'specific_recommendations': []
        }
        
        # Add specific recommendations based on performance
        for domain, score in report.domain_scores.items():
            if score < 60:
                domain_name = domain.replace('_', ' ').title()
                if domain == 'python_programming':
                    feedback['specific_recommendations'].append(
                        f"Practice Python programming with focus on data structures and algorithms"
                    )
                elif domain == 'machine_learning':
                    feedback['specific_recommendations'].append(
                        f"Study machine learning fundamentals and work on practical projects"
                    )
                elif domain == 'agentic_ai_systems':
                    feedback['specific_recommendations'].append(
                        f"Learn about agent architectures and multi-agent coordination patterns"
                    )
                elif domain == 'prompt_engineering':
                    feedback['specific_recommendations'].append(
                        f"Practice prompt design and learn advanced LLM interaction techniques"
                    )
                else:
                    feedback['specific_recommendations'].append(
                        f"Strengthen knowledge in {domain_name}"
                    )
        
        # Add performance pattern feedback
        if report.overall_score >= 80:
            feedback['specific_recommendations'].append(
                "Excellent performance! Consider advanced topics and specialization"
            )
        elif report.overall_score >= 60:
            feedback['specific_recommendations'].append(
                "Good foundation. Focus on addressing the identified gaps"
            )
        else:
            feedback['specific_recommendations'].append(
                "Significant study needed in core areas before advancing"
            )
        
        return feedback
    
    def _generate_hiring_recommendations(self, report: InterviewReport) -> Dict[str, Any]:
        """Generate hiring recommendations."""
        recommendations = {
            'hire_decision': '',
            'confidence_level': 0,
            'next_steps': [],
            'concerns': []
        }
        
        # Determine hire decision
        if report.overall_score >= 85:
            recommendations['hire_decision'] = 'Strong Hire'
            recommendations['confidence_level'] = 0.9
            recommendations['next_steps'] = [
                'Proceed to final interview round',
                'Schedule technical deep-dive with senior team',
                'Consider for immediate start date'
            ]
        elif report.overall_score >= 75:
            recommendations['hire_decision'] = 'Hire'
            recommendations['confidence_level'] = 0.8
            recommendations['next_steps'] = [
                'Schedule final interview with hiring manager',
                'Review portfolio/projects if available',
                'Consider for team fit assessment'
            ]
        elif report.overall_score >= 65:
            recommendations['hire_decision'] = 'Consider Hire'
            recommendations['confidence_level'] = 0.6
            recommendations['next_steps'] = [
                'Additional technical assessment recommended',
                'Consider for junior or training position',
                'Evaluate learning potential and attitude'
            ]
        elif report.overall_score >= 50:
            recommendations['hire_decision'] = 'Hold for Consideration'
            recommendations['confidence_level'] = 0.3
            recommendations['next_steps'] = [
                'Significant skill gaps identified',
                'Consider for different role or training program',
                'Re-evaluate after 3-6 months of skill development'
            ]
        else:
            recommendations['hire_decision'] = 'Not Recommended'
            recommendations['confidence_level'] = 0.9
            recommendations['next_steps'] = [
                'Does not meet minimum requirements',
                'Consider for different career track',
                'Provide constructive feedback for improvement'
            ]
        
        # Identify concerns
        if report.integrity_metrics.get('average_integrity_score', 100) < 70:
            recommendations['concerns'].append('Integrity concerns during interview')
        
        if report.compliance_summary.get('violations', 0) > 0:
            recommendations['concerns'].append('Compliance violations detected')
        
        # Check for critical domain weaknesses
        critical_domains = ['machine_learning', 'python_programming', 'data_science_fundamentals']
        for domain in critical_domains:
            if domain in report.domain_scores and report.domain_scores[domain] < 40:
                recommendations['concerns'].append(f'Critical weakness in {domain.replace("_", " ")}')
        
        return recommendations
    
    def _get_competence_level(self, score: float) -> str:
        """Get competence level based on score."""
        if score >= 90:
            return 'Expert'
        elif score >= 80:
            return 'Advanced'
        elif score >= 70:
            return 'Proficient'
        elif score >= 60:
            return 'Intermediate'
        elif score >= 50:
            return 'Basic'
        else:
            return 'Novice'
    
    def _get_problem_solving_assessment(self, score: float, consistent: bool, timing: bool) -> str:
        """Get problem-solving assessment."""
        if score >= 80 and consistent and timing:
            return 'Excellent problem solver'
        elif score >= 70:
            return 'Good problem solver'
        elif score >= 60:
            return 'Adequate problem solver'
        else:
            return 'Needs problem-solving development'
    
    def compare_candidates(self, reports: List[InterviewReport]) -> Dict[str, Any]:
        """Compare multiple candidates."""
        if not reports:
            return {'error': 'No reports provided'}
        
        comparison = {
            'candidate_rankings': [],
            'comparison_metrics': {},
            'recommendations': {}
        }
        
        # Rank candidates by overall score
        ranked_candidates = sorted(reports, key=lambda x: x.overall_score, reverse=True)
        
        for i, report in enumerate(ranked_candidates, 1):
            comparison['candidate_rankings'].append({
                'rank': i,
                'candidate_id': report.candidate_id,
                'overall_score': report.overall_score,
                'strengths_count': len(report.strengths),
                'weaknesses_count': len(report.weaknesses)
            })
        
        # Calculate comparison metrics
        all_scores = [r.overall_score for r in reports]
        comparison['comparison_metrics'] = {
            'average_score': sum(all_scores) / len(all_scores),
            'highest_score': max(all_scores),
            'lowest_score': min(all_scores),
            'score_range': max(all_scores) - min(all_scores)
        }
        
        # Generate recommendations
        top_candidates = ranked_candidates[:3] if len(ranked_candidates) >= 3 else ranked_candidates
        comparison['recommendations'] = {
            'top_candidates': [r.candidate_id for r in top_candidates],
            'recommended_for_hire': [r.candidate_id for r in ranked_candidates if r.overall_score >= 70],
            'needs_improvement': [r.candidate_id for r in ranked_candidates if r.overall_score < 60]
        }
        
        return comparison
    
    def generate_evaluation_summary(self, evaluation: Dict[str, Any]) -> str:
        """Generate human-readable evaluation summary."""
        summary_parts = [
            "CANDIDATE EVALUATION SUMMARY",
            "=" * 40,
            f"Overall Assessment: {evaluation['overall_assessment']['level']}",
            f"Recommendation: {evaluation['overall_assessment']['recommendation']}",
            "",
            "TECHNICAL COMPETENCE:",
            f"Score: {evaluation['technical_competence']['score']:.1f}/100",
            f"Level: {evaluation['technical_competence']['assessment']}",
        ]
        
        if evaluation['technical_competence']['strengths']:
            summary_parts.append("Strengths: " + ", ".join(evaluation['technical_competence']['strengths']))
        
        if evaluation['technical_competence']['weaknesses']:
            summary_parts.append("Areas for Improvement: " + ", ".join(evaluation['technical_competence']['weaknesses']))
        
        summary_parts.extend([
            "",
            "COMMUNICATION SKILLS:",
            f"Score: {evaluation['communication_skills']['score']:.1f}/100",
            f"Assessment: {evaluation['communication_skills']['assessment']}",
            "",
            "PROBLEM SOLVING:",
            f"Score: {evaluation['problem_solving_ability']['score']:.1f}/100",
            f"Assessment: {evaluation['problem_solving_ability']['assessment']}",
            "",
            "LEARNING POTENTIAL:",
            f"Score: {evaluation['learning_potential']['score']:.1f}/100",
            f"Assessment: {evaluation['learning_potential']['assessment']}",
            "",
            "ROLE SUITABILITY:",
        ])
        
        role_scores = evaluation['role_suitability']['role_scores']
        for role, score in role_scores.items():
            summary_parts.append(f"{role}: {score:.1f}%")
        
        summary_parts.extend([
            f"Best Fit: {evaluation['role_suitability']['best_fit_role']}",
            "",
            "HIRING RECOMMENDATION:",
            f"Decision: {evaluation['hiring_recommendations']['hire_decision']}",
            f"Confidence: {evaluation['hiring_recommendations']['confidence_level']*100:.0f}%",
        ])
        
        if evaluation['hiring_recommendations']['concerns']:
            summary_parts.append("Concerns:")
            for concern in evaluation['hiring_recommendations']['concerns']:
                summary_parts.append(f"  • {concern}")
        
        summary_parts.extend([
            "",
            "NEXT STEPS:",
        ])
        
        for step in evaluation['hiring_recommendations']['next_steps']:
            summary_parts.append(f"  • {step}")
        
        return "\n".join(summary_parts)
