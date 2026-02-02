from typing import List, Dict, Any, Tuple
from datetime import datetime
import uuid
import re
import logging
from src.utils.data_models import ComplianceLog
from src.utils.nlp_utils import NLPProcessor
from config.settings import Config

logger = logging.getLogger(__name__)

class BiasDetector:
    def __init__(self):
        self.nlp_processor = NLPProcessor()
        self.bias_threshold = Config.BIAS_THRESHOLD
        self.protected_attributes = Config.PROTECTED_ATTRIBUTES
        
        # Bias indicators and patterns
        self.gendered_words = {
            'masculine': ['aggressive', 'dominant', 'leader', 'competitive', 'ambitious', 'confident', 'outspoken'],
            'feminine': ['supportive', 'collaborative', 'nurturing', 'communicative', 'empathetic', 'detail-oriented']
        }
        
        self.age_bias_indicators = [
            'young', 'youthful', 'energetic', 'recent graduate', 'entry-level',
            'mature', 'experienced', 'senior-level', 'seasoned', 'veteran'
        ]
        
        self.cultural_bias_indicators = [
            'native speaker', 'western education', 'local candidate', 'cultural fit',
            'team player', 'works well with others', 'good communication skills'
        ]
        
        self.requirement_bias_patterns = {
            'unnecessary_requirements': [
                r'must have.*years.*experience.*specific.*tool',
                r'must.*degree.*from.*top.*university',
                r'must.*work.*on.*site.*full.*time'
            ],
            'discriminatory_language': [
                r'young.*dynamic.*team',
                r'mature.*professional',
                r'native.*speaker',
                r'able.*bodied'
            ]
        }
    
    def detect_bias_in_text(self, text: str, text_type: str = "general") -> Dict[str, Any]:
        """Detect various types of bias in text."""
        bias_results = {
            'overall_bias_score': 0.0,
            'gender_bias': {'score': 0.0, 'indicators': [], 'details': {}},
            'age_bias': {'score': 0.0, 'indicators': [], 'details': {}},
            'cultural_bias': {'score': 0.0, 'indicators': [], 'details': {}},
            'requirement_bias': {'score': 0.0, 'indicators': [], 'details': {}},
            'protected_attributes': [],
            'recommendations': []
        }
        
        try:
            text_lower = text.lower()
            
            # Detect gender bias
            gender_bias = self._detect_gender_bias(text_lower)
            bias_results['gender_bias'] = gender_bias
            
            # Detect age bias
            age_bias = self._detect_age_bias(text_lower)
            bias_results['age_bias'] = age_bias
            
            # Detect cultural bias
            cultural_bias = self._detect_cultural_bias(text_lower)
            bias_results['cultural_bias'] = cultural_bias
            
            # Detect requirement bias
            requirement_bias = self._detect_requirement_bias(text_lower)
            bias_results['requirement_bias'] = requirement_bias
            
            # Detect protected attributes
            protected_attrs = self.nlp_processor.detect_protected_attributes(text)
            bias_results['protected_attributes'] = protected_attrs
            
            # Calculate overall bias score
            bias_scores = [
                gender_bias['score'],
                age_bias['score'],
                cultural_bias['score'],
                requirement_bias['score']
            ]
            bias_results['overall_bias_score'] = max(bias_scores)
            
            # Generate recommendations
            bias_results['recommendations'] = self._generate_bias_recommendations(bias_results)
            
            # Log bias detection
            self._log_bias_detection(text_type, bias_results)
            
        except Exception as e:
            logger.error(f"Error detecting bias: {e}")
            bias_results['overall_bias_score'] = 1.0  # Conservative approach
            bias_results['recommendations'].append("Bias detection failed - manual review required")
        
        return bias_results
    
    def _detect_gender_bias(self, text: str) -> Dict[str, Any]:
        """Detect gender-coded language."""
        result = {'score': 0.0, 'indicators': [], 'details': {}}
        
        masculine_count = sum(1 for word in self.gendered_words['masculine'] if word in text)
        feminine_count = sum(1 for word in self.gendered_words['feminine'] if word in text)
        
        total_gendered_words = masculine_count + feminine_count
        
        if total_gendered_words > 0:
            masculine_ratio = masculine_count / total_gendered_words
            feminine_ratio = feminine_count / total_gendered_words
            
            # Score based on imbalance
            imbalance = abs(masculine_ratio - feminine_ratio)
            result['score'] = imbalance
            
            result['details'] = {
                'masculine_words': masculine_count,
                'feminine_words': feminine_count,
                'masculine_ratio': masculine_ratio,
                'feminine_ratio': feminine_ratio,
                'imbalance': imbalance
            }
            
            if masculine_count > 0:
                result['indicators'].append(f"Masculine-coded language detected: {masculine_count} instances")
            if feminine_count > 0:
                result['indicators'].append(f"Feminine-coded language detected: {feminine_count} instances")
            
            if imbalance > 0.3:
                result['indicators'].append(f"Significant gender imbalance detected ({imbalance:.2f})")
        
        return result
    
    def _detect_age_bias(self, text: str) -> Dict[str, Any]:
        """Detect age-related bias."""
        result = {'score': 0.0, 'indicators': [], 'details': {}}
        
        age_indicators_found = []
        
        for indicator in self.age_bias_indicators:
            if indicator in text:
                age_indicators_found.append(indicator)
        
        if age_indicators_found:
            result['score'] = min(1.0, len(age_indicators_found) * 0.3)
            result['indicators'] = [f"Age bias indicator: '{indicator}'" for indicator in age_indicators_found]
            result['details'] = {'indicators_found': age_indicators_found}
        
        # Check for specific age requirements
        age_patterns = [
            r'(\d+)\s*[-+]?\s*years?\s*(?:old|of age)',
            r'age\s*(?:requirement|restriction|limit)',
            r'young\s*(?:professional|graduate|talent)',
            r'mature\s*(?:professional|candidate)'
        ]
        
        for pattern in age_patterns:
            if re.search(pattern, text):
                result['score'] = max(result['score'], 0.8)
                result['indicators'].append(f"Specific age requirement detected: {pattern}")
                break
        
        return result
    
    def _detect_cultural_bias(self, text: str) -> Dict[str, Any]:
        """Detect cultural and nationality bias."""
        result = {'score': 0.0, 'indicators': [], 'details': {}}
        
        cultural_indicators_found = []
        
        for indicator in self.cultural_bias_indicators:
            if indicator in text:
                cultural_indicators_found.append(indicator)
        
        if cultural_indicators_found:
            result['score'] = min(1.0, len(cultural_indicators_found) * 0.25)
            result['indicators'] = [f"Cultural bias indicator: '{indicator}'" for indicator in cultural_indicators_found]
            result['details'] = {'indicators_found': cultural_indicators_found}
        
        # Check for nationality-specific requirements
        nationality_patterns = [
            r'(?:must|require|prefer).*\b(citizen|national|resident)\b',
            r'\b(american|british|indian|chinese)\b.*\b(candidate|professional)\b',
            r'native\s*speaker',
            r'local\s*candidate'
        ]
        
        for pattern in nationality_patterns:
            if re.search(pattern, text):
                result['score'] = max(result['score'], 0.7)
                result['indicators'].append(f"Nationality bias detected: {pattern}")
                break
        
        return result
    
    def _detect_requirement_bias(self, text: str) -> Dict[str, Any]:
        """Detect bias in job requirements."""
        result = {'score': 0.0, 'indicators': [], 'details': {}}
        
        violations_found = []
        
        for category, patterns in self.requirement_bias_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text):
                    violations_found.append(f"{category}: {pattern}")
        
        if violations_found:
            result['score'] = min(1.0, len(violations_found) * 0.4)
            result['indicators'] = violations_found
            result['details'] = {'violations': violations_found}
        
        # Check for excessive experience requirements
        experience_pattern = r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)'
        matches = re.findall(experience_pattern, text)
        
        for match in matches:
            years = int(match)
            if years > 10:
                result['score'] = max(result['score'], 0.6)
                result['indicators'].append(f"Excessive experience requirement: {years}+ years")
            elif years > 7:
                result['score'] = max(result['score'], 0.3)
                result['indicators'].append(f"High experience requirement: {years}+ years")
        
        return result
    
    def _generate_bias_recommendations(self, bias_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations to reduce bias."""
        recommendations = []
        
        if bias_results['gender_bias']['score'] > self.bias_threshold:
            recommendations.append("Use gender-neutral language in job descriptions")
            recommendations.append("Balance masculine and feminine-coded words")
        
        if bias_results['age_bias']['score'] > self.bias_threshold:
            recommendations.append("Remove age-specific language and requirements")
            recommendations.append("Focus on skills and experience rather than age")
        
        if bias_results['cultural_bias']['score'] > self.bias_threshold:
            recommendations.append("Remove nationality and cultural fit requirements")
            recommendations.append("Focus on professional qualifications only")
        
        if bias_results['requirement_bias']['score'] > self.bias_threshold:
            recommendations.append("Review and simplify job requirements")
            recommendations.append("Remove unnecessary barriers to entry")
        
        if bias_results['protected_attributes']:
            recommendations.append("Remove all references to protected characteristics")
            recommendations.append("Focus solely on job-related qualifications")
        
        if bias_results['overall_bias_score'] > self.bias_threshold:
            recommendations.append("Consider using standardized, bias-free job description templates")
            recommendations.append("Have job descriptions reviewed by diversity and inclusion team")
        
        return recommendations
    
    def _log_bias_detection(self, text_type: str, results: Dict[str, Any]):
        """Log bias detection results for audit purposes."""
        log_entry = ComplianceLog(
            log_id=str(uuid.uuid4()),
            session_id=None,
            event_type="bias_detection",
            description=f"Bias analysis for {text_type}",
            severity="high" if results['overall_bias_score'] > self.bias_threshold else "low",
            metadata={
                'text_type': text_type,
                'overall_bias_score': results['overall_bias_score'],
                'bias_types_detected': [
                    key for key, value in results.items() 
                    if isinstance(value, dict) and value.get('score', 0) > self.bias_threshold
                ],
                'protected_attributes': results['protected_attributes']
            },
            timestamp=datetime.now()
        )
        
        logger.info(f"Bias detection log created: {log_entry.log_id}")
    
    def compare_texts_for_bias(self, text1: str, text2: str, labels: Tuple[str, str] = ("Text 1", "Text 2")) -> Dict[str, Any]:
        """Compare two texts for bias differences."""
        bias1 = self.detect_bias_in_text(text1, labels[0])
        bias2 = self.detect_bias_in_text(text2, labels[1])
        
        comparison = {
            'text1': {'label': labels[0], 'bias_score': bias1['overall_bias_score']},
            'text2': {'label': labels[1], 'bias_score': bias2['overall_bias_score']},
            'difference': abs(bias1['overall_bias_score'] - bias2['overall_bias_score']),
            'improvement_areas': []
        }
        
        # Identify areas where text2 is better than text1
        for bias_type in ['gender_bias', 'age_bias', 'cultural_bias', 'requirement_bias']:
            if bias2[bias_type]['score'] < bias1[bias_type]['score']:
                comparison['improvement_areas'].append(bias_type)
        
        return comparison
    
    def generate_bias_report(self, analysis_results: Dict[str, Any]) -> str:
        """Generate a human-readable bias analysis report."""
        report_lines = [
            "BIAS ANALYSIS REPORT",
            "=" * 40,
            f"Overall Bias Score: {analysis_results['overall_bias_score']:.2f}/1.0",
            f"Risk Level: {'HIGH' if analysis_results['overall_bias_score'] > self.bias_threshold else 'LOW'}",
            "",
            "DETAILED ANALYSIS:",
            "-" * 20
        ]
        
        bias_types = {
            'gender_bias': 'Gender Bias',
            'age_bias': 'Age Bias',
            'cultural_bias': 'Cultural Bias',
            'requirement_bias': 'Requirement Bias'
        }
        
        for bias_key, bias_label in bias_types.items():
            bias_data = analysis_results[bias_key]
            report_lines.extend([
                f"\n{bias_label}:",
                f"  Score: {bias_data['score']:.2f}/1.0",
                f"  Risk Level: {'HIGH' if bias_data['score'] > self.bias_threshold else 'LOW'}"
            ])
            
            if bias_data['indicators']:
                report_lines.append("  Indicators:")
                for indicator in bias_data['indicators']:
                    report_lines.append(f"    • {indicator}")
        
        if analysis_results['protected_attributes']:
            report_lines.extend([
                "\nProtected Attributes Detected:",
                *[f"  • {attr}" for attr in analysis_results['protected_attributes']]
            ])
        
        if analysis_results['recommendations']:
            report_lines.extend([
                "\nRECOMMENDATIONS:",
                "-" * 15,
                *[f"• {rec}" for rec in analysis_results['recommendations']]
            ])
        
        return "\n".join(report_lines)
