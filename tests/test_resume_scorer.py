"""
Test suite for Resume Scoring Module

This module contains unit tests for the resume scoring functionality
including parsing, scoring, and compliance checking.
"""

import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.resume_scorer.parser import ResumeParser
from src.resume_scorer.scorer import ResumeScorer
from src.resume_scorer.compliance import ResumeComplianceChecker
from src.utils.data_models import ResumeData, JobDescription, Skill

class TestResumeParser(unittest.TestCase):
    """Test cases for ResumeParser class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = ResumeParser()
        
    def test_extract_skills_from_text(self):
        """Test skill extraction from text."""
        text = "Experienced Python developer with machine learning and data science skills. Proficient in TensorFlow and scikit-learn."
        
        skills_data = self.parser.nlp_processor.extract_skills(text)
        
        # Check if skills are extracted correctly
        self.assertIn('programming_languages', skills_data)
        self.assertIn('ml_frameworks', skills_data)
        self.assertIn('data_science', skills_data)
        
        # Check for specific skills
        programming_skills = skills_data['programming_languages']
        self.assertTrue(any('python' in skill.lower() for skill in programming_skills))
        
    def test_extract_experience_years(self):
        """Test experience years extraction."""
        text1 = "5 years of experience in software development"
        text2 = "Experience: 3+ years working with data"
        text3 = "No specific experience mentioned"
        
        years1 = self.parser.nlp_processor.extract_experience_years(text1)
        years2 = self.parser.nlp_processor.extract_experience_years(text2)
        years3 = self.parser.nlp_processor.extract_experience_years(text3)
        
        self.assertEqual(years1, 5.0)
        self.assertEqual(years2, 3.0)
        self.assertEqual(years3, 0.0)
        
    def test_parse_job_description(self):
        """Test job description parsing."""
        job_text = """
        Senior Data Scientist Position
        
        We are looking for a Senior Data Scientist with strong Python programming skills
        and experience in machine learning. Requirements include:
        - 5+ years of experience
        - Master's degree in Computer Science or related field
        - Proficiency in TensorFlow and PyTorch
        - Strong statistical analysis skills
        """
        
        job_desc = self.parser.parse_job_description(job_text, "Senior Data Scientist")
        
        self.assertIsInstance(job_desc, JobDescription)
        self.assertEqual(job_desc.title, "Senior Data Scientist")
        self.assertGreater(job_desc.experience_required, 0)
        self.assertGreater(len(job_desc.required_skills), 0)
        
    def test_pii_anonymization(self):
        """Test PII removal from text."""
        text_with_pii = "Contact: john.doe@email.com or call 555-123-4567"
        cleaned_text = self.parser.nlp_processor.extract_text_from_resume(text_with_pii)
        
        self.assertIn('[EMAIL]', cleaned_text)
        self.assertIn('[PHONE]', cleaned_text)
        self.assertNotIn('john.doe@email.com', cleaned_text)
        self.assertNotIn('555-123-4567', cleaned_text)

class TestResumeScorer(unittest.TestCase):
    """Test cases for ResumeScorer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scorer = ResumeScorer()
        
        # Create test resume data
        self.test_resume = ResumeData(
            candidate_id="test-candidate-1",
            skills=[
                Skill(name="Python", category="programming_languages", proficiency_level=4, years_experience=3),
                Skill(name="TensorFlow", category="ml_frameworks", proficiency_level=3, years_experience=2),
                Skill(name="Data Analysis", category="data_science", proficiency_level=4, years_experience=3)
            ],
            experience_years=3.0,
            education=[{"degree": "Master of Science", "field": "Computer Science"}],
            certifications=["AWS Certified Machine Learning"],
            raw_text="Experienced Python developer with ML background",
            processed_at=None
        )
        
        # Create test job description
        self.test_job = JobDescription(
            job_id="test-job-1",
            title="Data Scientist",
            required_skills=[
                Skill(name="Python", category="programming_languages", proficiency_level=3, years_experience=2),
                Skill(name="TensorFlow", category="ml_frameworks", proficiency_level=2, years_experience=1),
                Skill(name="Machine Learning", category="data_science", proficiency_level=3, years_experience=2)
            ],
            experience_required=2.0,
            education_requirements=["Master's degree"],
            responsibilities=["Develop ML models", "Data analysis"],
            raw_text="Looking for Python developer with ML experience"
        )
        
    def test_score_resume_basic(self):
        """Test basic resume scoring."""
        result = self.scorer.score_resume(self.test_resume, self.test_job)
        
        self.assertIsInstance(result, type(self.test_resume))  # Should be ScoringResult
        self.assertGreaterEqual(result.overall_score, 0)
        self.assertLessEqual(result.overall_score, 100)
        self.assertGreaterEqual(result.skill_match_score, 0)
        self.assertLessEqual(result.skill_match_score, 100)
        
    def test_skill_match_calculation(self):
        """Test skill match score calculation."""
        perfect_match_skills = [
            Skill(name="Python", category="programming_languages", proficiency_level=5, years_experience=5)
        ]
        
        job_skills = [
            Skill(name="Python", category="programming_languages", proficiency_level=3, years_experience=2)
        ]
        
        score = self.scorer._calculate_skill_match_score(perfect_match_skills, job_skills)
        self.assertGreater(score, 80)  # Should be high score for perfect match
        
    def test_experience_score_calculation(self):
        """Test experience score calculation."""
        # Test exact match
        score1 = self.scorer._calculate_experience_score(5.0, 5.0)
        self.assertGreater(score1, 80)
        
        # Test insufficient experience
        score2 = self.scorer._calculate_experience_score(2.0, 5.0)
        self.assertLess(score2, 80)
        
        # Test excess experience
        score3 = self.scorer._calculate_experience_score(8.0, 5.0)
        self.assertGreater(score3, 80)
        
    def test_batch_scoring(self):
        """Test batch resume scoring."""
        resumes = [self.test_resume]
        
        results = self.scorer.batch_score_resumes(resumes, self.test_job)
        
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], type(self.test_resume))  # Should be ScoringResult
        
    def test_scoring_statistics(self):
        """Test scoring statistics calculation."""
        # Create mock scoring results
        from src.utils.data_models import ScoringResult
        from datetime import datetime
        
        mock_results = [
            ScoringResult(
                resume_id="1", job_id="1", overall_score=80.0,
                skill_match_score=85.0, experience_score=75.0,
                education_score=80.0, certification_score=70.0,
                matched_skills=["Python"], missing_skills=["R"],
                explanation="Good match", compliance_flags=[],
                scored_at=datetime.now()
            ),
            ScoringResult(
                resume_id="2", job_id="1", overall_score=60.0,
                skill_match_score=65.0, experience_score=55.0,
                education_score=60.0, certification_score=50.0,
                matched_skills=["Python"], missing_skills=["TensorFlow", "R"],
                explanation="Average match", compliance_flags=[],
                scored_at=datetime.now()
            )
        ]
        
        stats = self.scorer.get_scoring_statistics(mock_results)
        
        self.assertEqual(stats['total_resumes'], 2)
        self.assertEqual(stats['average_score'], 70.0)
        self.assertEqual(stats['max_score'], 80.0)
        self.assertEqual(stats['min_score'], 60.0)

class TestResumeComplianceChecker(unittest.TestCase):
    """Test cases for ResumeComplianceChecker class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.compliance_checker = ResumeComplianceChecker()
        
        # Create test resume with potential compliance issues
        self.test_resume_with_issues = ResumeData(
            candidate_id="test-candidate-2",
            skills=[],
            experience_years=0,
            education=[],
            certifications=[],
            raw_text="John Doe, 25 years old, male engineer from USA",
            processed_at=None
        )
        
        self.test_job = JobDescription(
            job_id="test-job-2",
            title="Software Engineer",
            required_skills=[],
            experience_required=0,
            education_requirements=[],
            responsibilities=[],
            raw_text="Looking for young, energetic male candidates"
        )
        
    def test_protected_attribute_detection(self):
        """Test detection of protected attributes."""
        text_with_attributes = "25-year-old female engineer from India"
        detected = self.compliance_checker.nlp_processor.detect_protected_attributes(text_with_attributes)
        
        self.assertIn('age', detected)
        self.assertIn('gender', detected)
        
    def test_compliance_check_basic(self):
        """Test basic compliance checking."""
        result = self.compliance_checker.check_resume_compliance(
            self.test_resume_with_issues, self.test_job
        )
        
        self.assertIn('is_compliant', result)
        self.assertIn('overall_compliance_score', result)
        self.assertIn('bias_flags', result)
        self.assertIn('privacy_flags', result)
        self.assertIn('recommendations', result)
        
        # Should detect issues with the test data
        self.assertLess(result['overall_compliance_score'], 100)
        
    def test_batch_compliance_check(self):
        """Test batch compliance checking."""
        resumes = [self.test_resume_with_issues]
        
        results = self.compliance_checker.check_batch_compliance(resumes, self.test_job)
        
        self.assertIn('total_resumes', results)
        self.assertIn('compliant_resumes', results)
        self.assertIn('non_compliant_resumes', results)
        self.assertIn('average_compliance_score', results)
        
    def test_compliance_report_generation(self):
        """Test compliance report generation."""
        batch_results = {
            'total_resumes': 2,
            'compliant_resumes': 1,
            'non_compliant_resumes': 1,
            'average_compliance_score': 75.0,
            'common_issues': {'Protected attribute detected: age': 1}
        }
        
        report = self.compliance_checker.generate_compliance_report(batch_results)
        
        self.assertIn('COMPLIANCE AUDIT REPORT', report)
        self.assertIn('Total Resumes Processed: 2', report)
        self.assertIn('RECOMMENDATIONS:', report)

class TestIntegration(unittest.TestCase):
    """Integration tests for the resume scoring module."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.parser = ResumeParser()
        self.scorer = ResumeScorer()
        self.compliance_checker = ResumeComplianceChecker()
        
    def test_end_to_end_scoring_workflow(self):
        """Test complete scoring workflow."""
        # Sample resume text
        resume_text = """
        Jane Smith
        Senior Data Scientist
        
        Experience:
        - 5 years of experience in machine learning and data science
        - Proficient in Python, TensorFlow, and scikit-learn
        - Master's degree in Computer Science
        
        Skills:
        - Python programming
        - Machine learning
        - Data analysis
        - TensorFlow
        """
        
        # Sample job description
        job_text = """
        Senior Data Scientist Position
        
        Requirements:
        - 3+ years of experience in data science
        - Strong Python programming skills
        - Experience with machine learning frameworks
        - Bachelor's degree in relevant field
        """
        
        # Parse resume and job description
        resume_data = self.parser.parse_resume_text(resume_text)
        job_desc = self.parser.parse_job_description(job_text, "Senior Data Scientist")
        
        # Score the resume
        scoring_result = self.scorer.score_resume(resume_data, job_desc)
        
        # Check compliance
        compliance_result = self.compliance_checker.check_resume_compliance(resume_data, job_desc)
        
        # Verify results
        self.assertIsInstance(scoring_result, type(resume_data))  # Should be ScoringResult
        self.assertGreater(scoring_result.overall_score, 0)
        self.assertLessEqual(scoring_result.overall_score, 100)
        
        self.assertIsInstance(compliance_result, dict)
        self.assertIn('overall_compliance_score', compliance_result)
        
    @patch('src.resume_scorer.parser.ResumeParser._extract_from_pdf')
    def test_pdf_parsing_integration(self, mock_pdf_extract):
        """Test PDF parsing integration."""
        # Mock PDF extraction
        mock_pdf_extract.return_value = "Sample PDF content with Python and ML skills"
        
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(b"mock pdf content")
            temp_path = temp_file.name
        
        try:
            # Parse the mock PDF
            resume_data = self.parser.parse_resume(temp_path)
            
            # Verify parsing worked
            self.assertIsInstance(resume_data, ResumeData)
            self.assertIsNotNone(resume_data.candidate_id)
            
        finally:
            # Clean up
            os.unlink(temp_path)

if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestResumeParser))
    test_suite.addTest(unittest.makeSuite(TestResumeScorer))
    test_suite.addTest(unittest.makeSuite(TestResumeComplianceChecker))
    test_suite.addTest(unittest.makeSuite(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
