from typing import Dict, List, Tuple
from datetime import datetime
import uuid
import logging
from src.utils.data_models import ResumeData, JobDescription, ScoringResult, Skill
from src.utils.nlp_utils import NLPProcessor
from config.settings import Config

logger = logging.getLogger(__name__)

class ResumeScorer:
    def __init__(self):
        self.nlp_processor = NLPProcessor()
        self.weights = Config.RESUME_SCORE_WEIGHTS
    
    def score_resume(self, resume_data: ResumeData, job_description: JobDescription) -> ScoringResult:
        """Score resume against job description and return detailed results."""
        try:
            # Calculate individual component scores
            skill_match_score = self._calculate_skill_match_score(resume_data.skills, job_description.required_skills)
            experience_score = self._calculate_experience_score(resume_data.experience_years, job_description.experience_required)
            education_score = self._calculate_education_score(resume_data.education, job_description.education_requirements)
            certification_score = self._calculate_certification_score(resume_data.certifications, job_description.required_skills)
            
            # Calculate weighted overall score
            overall_score = (
                skill_match_score * self.weights['skills_match'] +
                experience_score * self.weights['experience_relevance'] +
                education_score * self.weights['education'] +
                certification_score * self.weights['certifications']
            )
            
            # Generate analysis
            matched_skills, missing_skills = self._analyze_skill_match(resume_data.skills, job_description.required_skills)
            explanation = self._generate_explanation(resume_data, job_description, overall_score, matched_skills, missing_skills)
            
            # Check for compliance issues
            compliance_flags = self._check_compliance(resume_data, job_description)
            
            scoring_result = ScoringResult(
                resume_id=resume_data.candidate_id,
                job_id=job_description.job_id,
                overall_score=min(100, max(0, overall_score)),  # Clamp between 0-100
                skill_match_score=skill_match_score,
                experience_score=experience_score,
                education_score=education_score,
                certification_score=certification_score,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                explanation=explanation,
                compliance_flags=compliance_flags,
                scored_at=datetime.now()
            )
            
            logger.info(f"Scored resume {resume_data.candidate_id} against job {job_description.job_id}: {overall_score:.2f}")
            return scoring_result
            
        except Exception as e:
            logger.error(f"Error scoring resume: {e}")
            raise
    
    def _calculate_skill_match_score(self, resume_skills: List[Skill], required_skills: List[Skill]) -> float:
        """Calculate skill match score based on overlap and proficiency."""
        if not required_skills:
            return 0.0
        
        resume_skill_names = {skill.name.lower() for skill in resume_skills}
        required_skill_names = {skill.name.lower() for skill in required_skills}
        
        # Calculate exact matches
        exact_matches = resume_skill_names & required_skill_names
        exact_match_score = len(exact_matches) / len(required_skill_names) * 100
        
        # Calculate semantic similarity for non-exact matches
        semantic_bonus = 0.0
        for req_skill in required_skills:
            if req_skill.name.lower() not in exact_matches:
                # Find best semantic match
                best_similarity = 0.0
                for resume_skill in resume_skills:
                    similarity = self.nlp_processor.calculate_semantic_similarity(
                        req_skill.name, resume_skill.name
                    )
                    best_similarity = max(best_similarity, similarity)
                
                if best_similarity > 0.7:  # Threshold for semantic match
                    semantic_bonus += best_similarity * 20  # Bonus points for semantic match
        
        # Consider proficiency levels
        proficiency_bonus = 0.0
        for skill_name in exact_matches:
            resume_skill = next((s for s in resume_skills if s.name.lower() == skill_name), None)
            if resume_skill:
                proficiency_bonus += resume_skill.proficiency_level * 4  # Max 20 points per skill
        
        total_score = exact_match_score + semantic_bonus + proficiency_bonus
        return min(100, total_score)
    
    def _calculate_experience_score(self, resume_experience: float, required_experience: float) -> float:
        """Calculate experience relevance score."""
        if required_experience == 0:
            return 100.0 if resume_experience > 0 else 50.0
        
        if resume_experience >= required_experience:
            # Bonus for exceeding requirements
            excess_ratio = min(resume_experience / required_experience, 2.0)
            return min(100, 80 + (excess_ratio - 1) * 20)
        else:
            # Penalty for insufficient experience
            ratio = resume_experience / required_experience
            return max(0, ratio * 80)
    
    def _calculate_education_score(self, resume_education: List[Dict], required_education: List[str]) -> float:
        """Calculate education match score."""
        if not required_education:
            return 80.0  # Neutral score if no specific requirements
        
        resume_edu_text = ' '.join([edu.get('context', '').lower() for edu in resume_education])
        required_edu_text = ' '.join(required_education).lower()
        
        # Calculate semantic similarity
        similarity = self.nlp_processor.calculate_semantic_similarity(resume_edu_text, required_edu_text)
        
        # Check for degree level matches
        degree_levels = {
            'phd': 4, 'doctorate': 4,
            'master': 3, 'msc': 3, 'm.s.': 3, 'mba': 3,
            'bachelor': 2, 'bsc': 2, 'b.s.': 2,
            'associate': 1, 'diploma': 1
        }
        
        max_resume_level = 0
        for edu in resume_education:
            for degree, level in degree_levels.items():
                if degree in resume_edu_text:
                    max_resume_level = max(max_resume_level, level)
        
        max_required_level = 0
        for req in required_education:
            for degree, level in degree_levels.items():
                if degree in req.lower():
                    max_required_level = max(max_required_level, level)
        
        # Score based on degree level matching
        if max_resume_level >= max_required_level:
            level_score = 100
        elif max_resume_level > 0:
            level_score = (max_resume_level / max_required_level) * 80
        else:
            level_score = 40
        
        # Combine semantic similarity and level score
        return (similarity * 50 + level_score * 50) / 100
    
    def _calculate_certification_score(self, certifications: List[str], required_skills: List[Skill]) -> float:
        """Calculate certification relevance score."""
        if not certifications:
            return 50.0  # Neutral score
        
        cert_text = ' '.join(certifications).lower()
        score = 50.0  # Base score
        
        # Bonus for relevant certifications
        relevant_cert_keywords = [
            'aws', 'azure', 'gcp', 'google cloud', 'microsoft certified',
            'tensorflow', 'pytorch', 'scikit-learn', 'machine learning',
            'data science', 'python', 'java', 'sql', 'pmp', 'agile'
        ]
        
        for keyword in relevant_cert_keywords:
            if keyword in cert_text:
                score += 10
        
        # Check alignment with required skills
        for skill in required_skills:
            if skill.name.lower() in cert_text:
                score += 15
        
        return min(100, score)
    
    def _analyze_skill_match(self, resume_skills: List[Skill], required_skills: List[Skill]) -> Tuple[List[str], List[str]]:
        """Analyze which skills are matched and missing."""
        resume_skill_names = {skill.name.lower() for skill in resume_skills}
        required_skill_names = {skill.name.lower() for skill in required_skills}
        
        matched_skills = []
        missing_skills = []
        
        for skill in required_skills:
            if skill.name.lower() in resume_skill_names:
                matched_skills.append(skill.name)
            else:
                missing_skills.append(skill.name)
        
        return matched_skills, missing_skills
    
    def _generate_explanation(self, resume_data: ResumeData, job_description: JobDescription, 
                             overall_score: float, matched_skills: List[str], missing_skills: List[str]) -> str:
        """Generate detailed explanation of the scoring."""
        explanation_parts = []
        
        # Overall assessment
        if overall_score >= 80:
            explanation_parts.append("Excellent match with high alignment to job requirements.")
        elif overall_score >= 60:
            explanation_parts.append("Good match with solid alignment to key requirements.")
        elif overall_score >= 40:
            explanation_parts.append("Moderate match with some gaps in key areas.")
        else:
            explanation_parts.append("Low match with significant gaps in requirements.")
        
        # Skills analysis
        if matched_skills:
            explanation_parts.append(f"Key matched skills: {', '.join(matched_skills[:5])}")
        
        if missing_skills:
            explanation_parts.append(f"Missing critical skills: {', '.join(missing_skills[:5])}")
        
        # Experience analysis
        if resume_data.experience_years >= job_description.experience_required:
            explanation_parts.append(f"Experience level ({resume_data.experience_years:.1f} years) meets or exceeds requirements ({job_description.experience_required:.1f} years).")
        else:
            explanation_parts.append(f"Experience level ({resume_data.experience_years:.1f} years) below required ({job_description.experience_required:.1f} years).")
        
        # Education analysis
        if resume_data.education:
            explanation_parts.append("Education background aligns well with requirements.")
        
        # Recommendations
        if missing_skills:
            explanation_parts.append(f"Recommendation: Focus on developing skills in {', '.join(missing_skills[:3])}.")
        
        return " ".join(explanation_parts)
    
    def _check_compliance(self, resume_data: ResumeData, job_description: JobDescription) -> List[str]:
        """Check for compliance issues in the scoring process."""
        compliance_flags = []
        
        # Check for protected attributes in resume text
        protected_attributes = self.nlp_processor.detect_protected_attributes(resume_data.raw_text)
        if protected_attributes:
            compliance_flags.extend([f"Protected attribute detected: {attr}" for attr in protected_attributes])
        
        # Check for potential bias in job description
        protected_in_job = self.nlp_processor.detect_protected_attributes(job_description.raw_text)
        if protected_in_job:
            compliance_flags.extend([f"Protected attribute in job description: {attr}" for attr in protected_in_job])
        
        # Check for explainability
        if not resume_data.skills:
            compliance_flags.append("No skills extracted - low explainability")
        
        return compliance_flags
    
    def batch_score_resumes(self, resumes_data: List[ResumeData], job_description: JobDescription) -> List[ScoringResult]:
        """Score multiple resumes against a single job description."""
        results = []
        for resume_data in resumes_data:
            try:
                result = self.score_resume(resume_data, job_description)
                results.append(result)
            except Exception as e:
                logger.error(f"Error scoring resume {resume_data.candidate_id}: {e}")
                continue
        
        # Sort by overall score descending
        results.sort(key=lambda x: x.overall_score, reverse=True)
        return results
    
    def get_scoring_statistics(self, scoring_results: List[ScoringResult]) -> Dict:
        """Get statistical summary of scoring results."""
        if not scoring_results:
            return {}
        
        scores = [result.overall_score for result in scoring_results]
        
        return {
            'total_resumes': len(scoring_results),
            'average_score': sum(scores) / len(scores),
            'max_score': max(scores),
            'min_score': min(scores),
            'median_score': sorted(scores)[len(scores) // 2],
            'score_distribution': {
                'excellent': len([s for s in scores if s >= 80]),
                'good': len([s for s in scores if 60 <= s < 80]),
                'moderate': len([s for s in scores if 40 <= s < 60]),
                'poor': len([s for s in scores if s < 40])
            }
        }
