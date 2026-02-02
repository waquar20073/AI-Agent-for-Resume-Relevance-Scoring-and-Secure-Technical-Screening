from typing import List, Dict, Any
from datetime import datetime
import uuid
import logging
from src.utils.data_models import ResumeData, JobDescription, ComplianceLog
from src.utils.nlp_utils import NLPProcessor
from config.settings import Config

logger = logging.getLogger(__name__)

class ResumeComplianceChecker:
    def __init__(self):
        self.nlp_processor = NLPProcessor()
        self.protected_attributes = Config.PROTECTED_ATTRIBUTES
        self.bias_threshold = Config.BIAS_THRESHOLD
    
    def check_resume_compliance(self, resume_data: ResumeData, job_description: JobDescription) -> Dict[str, Any]:
        """Perform comprehensive compliance check on resume scoring."""
        compliance_results = {
            'is_compliant': True,
            'bias_flags': [],
            'privacy_flags': [],
            'fairness_flags': [],
            'explainability_flags': [],
            'overall_compliance_score': 100.0,
            'recommendations': []
        }
        
        try:
            # Check for protected attributes
            bias_flags = self._check_protected_attributes(resume_data.raw_text)
            compliance_results['bias_flags'] = bias_flags
            
            # Check privacy compliance
            privacy_flags = self._check_privacy_compliance(resume_data)
            compliance_results['privacy_flags'] = privacy_flags
            
            # Check fairness
            fairness_flags = self._check_fairness_compliance(resume_data, job_description)
            compliance_results['fairness_flags'] = fairness_flags
            
            # Check explainability
            explainability_flags = self._check_explainability_compliance(resume_data)
            compliance_results['explainability_flags'] = explainability_flags
            
            # Calculate overall compliance score
            total_flags = len(bias_flags) + len(privacy_flags) + len(fairness_flags) + len(explainability_flags)
            compliance_results['overall_compliance_score'] = max(0, 100 - (total_flags * 10))
            
            # Determine overall compliance
            compliance_results['is_compliant'] = compliance_results['overall_compliance_score'] >= 70
            
            # Generate recommendations
            compliance_results['recommendations'] = self._generate_compliance_recommendations(compliance_results)
            
            # Log compliance check
            self._log_compliance_check(resume_data.candidate_id, job_description.job_id, compliance_results)
            
            logger.info(f"Compliance check completed for resume {resume_data.candidate_id}: {compliance_results['overall_compliance_score']:.2f}")
            
        except Exception as e:
            logger.error(f"Error in compliance check: {e}")
            compliance_results['is_compliant'] = False
            compliance_results['overall_compliance_score'] = 0.0
            compliance_results['recommendations'].append("Compliance check failed - manual review required")
        
        return compliance_results
    
    def _check_protected_attributes(self, text: str) -> List[str]:
        """Check for presence of protected attributes in text."""
        flags = []
        detected_attributes = self.nlp_processor.detect_protected_attributes(text)
        
        for attribute in detected_attributes:
            if attribute in self.protected_attributes:
                flags.append(f"Protected attribute detected: {attribute}")
        
        return flags
    
    def _check_privacy_compliance(self, resume_data: ResumeData) -> List[str]:
        """Check for privacy compliance issues."""
        flags = []
        
        # Check for PII in raw text
        pii_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'address': r'\d+\s+[\w\s]+,\s*[\w\s]+,\s*[A-Z]{2}\s*\d{5}'
        }
        
        import re
        for pii_type, pattern in pii_patterns.items():
            if re.search(pattern, resume_data.raw_text):
                flags.append(f"PII detected: {pii_type}")
        
        # Check if PII was properly removed in processed data
        if '[EMAIL]' not in resume_data.raw_text and '@' in resume_data.raw_text:
            flags.append("Email addresses not properly anonymized")
        
        if '[PHONE]' not in resume_data.raw_text and re.search(r'\d{3}[-.]?\d{3}[-.]?\d{4}', resume_data.raw_text):
            flags.append("Phone numbers not properly anonymized")
        
        return flags
    
    def _check_fairness_compliance(self, resume_data: ResumeData, job_description: JobDescription) -> List[str]:
        """Check for fairness compliance issues."""
        flags = []
        
        # Check skill extraction fairness
        if not resume_data.skills:
            flags.append("No skills extracted - potential bias in skill recognition")
        
        # Check for demographic bias in job description
        job_bias = self.nlp_processor.detect_protected_attributes(job_description.raw_text)
        if job_bias:
            flags.append(f"Job description contains potentially biased language: {', '.join(job_bias)}")
        
        # Check experience requirements for reasonableness
        if job_description.experience_required > 10:
            flags.append("Experience requirement may be excessive - potential age discrimination")
        
        # Check education requirements for necessity
        if not job_description.education_requirements:
            flags.append("No clear education requirements - may lead to inconsistent evaluation")
        
        return flags
    
    def _check_explainability_compliance(self, resume_data: ResumeData) -> List[str]:
        """Check for explainability compliance."""
        flags = []
        
        # Check if sufficient data was extracted
        if len(resume_data.skills) < 3:
            flags.append("Insufficient skill data extracted - low explainability")
        
        if resume_data.experience_years == 0 and len(resume_data.raw_text) > 100:
            flags.append("Experience not detected despite substantial content - extraction issue")
        
        if not resume_data.education:
            flags.append("No education information extracted - incomplete profile")
        
        # Check for processing errors
        if len(resume_data.raw_text) < 50:
            flags.append("Very little text extracted - potential parsing error")
        
        return flags
    
    def _generate_compliance_recommendations(self, compliance_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on compliance issues."""
        recommendations = []
        
        if compliance_results['bias_flags']:
            recommendations.append("Review and remove protected attributes from resume processing")
        
        if compliance_results['privacy_flags']:
            recommendations.append("Implement stronger PII anonymization in text processing")
        
        if compliance_results['fairness_flags']:
            recommendations.append("Review job description for biased language and unreasonable requirements")
        
        if compliance_results['explainability_flags']:
            recommendations.append("Improve text extraction and parsing algorithms for better explainability")
        
        if compliance_results['overall_compliance_score'] < 80:
            recommendations.append("Manual review recommended due to compliance concerns")
        
        return recommendations
    
    def _log_compliance_check(self, candidate_id: str, job_id: str, results: Dict[str, Any]):
        """Log compliance check results for audit purposes."""
        log_entry = ComplianceLog(
            log_id=str(uuid.uuid4()),
            session_id=None,
            event_type="resume_compliance_check",
            description=f"Compliance check for candidate {candidate_id} against job {job_id}",
            severity="low" if results['is_compliant'] else "high",
            metadata={
                'candidate_id': candidate_id,
                'job_id': job_id,
                'compliance_score': results['overall_compliance_score'],
                'is_compliant': results['is_compliant'],
                'flags_count': len(results['bias_flags']) + len(results['privacy_flags']) + 
                              len(results['fairness_flags']) + len(results['explainability_flags'])
            },
            timestamp=datetime.now()
        )
        
        # In a real implementation, this would be saved to database
        logger.info(f"Compliance log created: {log_entry.log_id}")
    
    def check_batch_compliance(self, resumes_data: List[ResumeData], job_description: JobDescription) -> Dict[str, Any]:
        """Check compliance for a batch of resumes."""
        batch_results = {
            'total_resumes': len(resumes_data),
            'compliant_resumes': 0,
            'non_compliant_resumes': 0,
            'average_compliance_score': 0.0,
            'common_issues': {},
            'individual_results': []
        }
        
        total_score = 0.0
        all_flags = []
        
        for resume_data in resumes_data:
            result = self.check_resume_compliance(resume_data, job_description)
            batch_results['individual_results'].append({
                'candidate_id': resume_data.candidate_id,
                'compliance_score': result['overall_compliance_score'],
                'is_compliant': result['is_compliant']
            })
            
            if result['is_compliant']:
                batch_results['compliant_resumes'] += 1
            else:
                batch_results['non_compliant_resumes'] += 1
            
            total_score += result['overall_compliance_score']
            
            # Collect all flags for analysis
            for flag_type in ['bias_flags', 'privacy_flags', 'fairness_flags', 'explainability_flags']:
                all_flags.extend(result[flag_type])
        
        batch_results['average_compliance_score'] = total_score / len(resumes_data) if resumes_data else 0
        
        # Analyze common issues
        from collections import Counter
        flag_counts = Counter(all_flags)
        batch_results['common_issues'] = dict(flag_counts.most_common(5))
        
        return batch_results
    
    def generate_compliance_report(self, batch_results: Dict[str, Any]) -> str:
        """Generate a human-readable compliance report."""
        report_lines = [
            "COMPLIANCE AUDIT REPORT",
            "=" * 50,
            f"Total Resumes Processed: {batch_results['total_resumes']}",
            f"Compliant Resumes: {batch_results['compliant_resumes']} ({batch_results['compliant_resumes']/batch_results['total_resumes']*100:.1f}%)",
            f"Non-Compliant Resumes: {batch_results['non_compliant_resumes']} ({batch_results['non_compliant_resumes']/batch_results['total_resumes']*100:.1f}%)",
            f"Average Compliance Score: {batch_results['average_compliance_score']:.2f}/100",
            "",
            "MOST COMMON COMPLIANCE ISSUES:",
            "-" * 30
        ]
        
        for issue, count in batch_results['common_issues'].items():
            report_lines.append(f"• {issue}: {count} occurrences")
        
        if batch_results['average_compliance_score'] < 80:
            report_lines.extend([
                "",
                "RECOMMENDATIONS:",
                "-" * 15,
                "• Review and improve PII anonymization processes",
                "• Enhance skill extraction algorithms",
                "• Implement bias detection in job descriptions",
                "• Consider manual review for low-scoring resumes"
            ])
        
        return "\n".join(report_lines)
