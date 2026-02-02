import re
import spacy
import nltk
from typing import List, Dict, Tuple, Set
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from transformers import pipeline
import logging

logger = logging.getLogger(__name__)

class NLPProcessor:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Using basic processing.")
            self.nlp = None
            
        self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.skill_extractor = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english")
        
        # Technical skills dictionary
        self.technical_skills = {
            'programming_languages': [
                'python', 'java', 'javascript', 'c++', 'r', 'sql', 'scala', 'go', 'rust', 'swift'
            ],
            'ml_frameworks': [
                'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'xgboost', 'lightgbm', 'pandas', 'numpy'
            ],
            'deep_learning': [
                'neural networks', 'cnn', 'rnn', 'lstm', 'transformer', 'bert', 'gpt', 'attention mechanism'
            ],
            'data_science': [
                'statistics', 'machine learning', 'data analysis', 'data visualization', 'etl', 'data mining'
            ],
            'agentic_ai': [
                'prompt engineering', 'agent systems', 'multi-agent coordination', 'llm', 'chain of thought',
                'reinforcement learning', 'autonomous systems', 'ai workflow automation'
            ],
            'cloud_platforms': [
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ci/cd'
            ]
        }
    
    def extract_text_from_resume(self, text: str) -> str:
        """Clean and preprocess resume text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove email addresses and phone numbers (PII protection)
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        # Remove special characters but keep important ones
        text = re.sub(r'[^\w\s\.\,\-\+\(\)]', ' ', text)
        return text.strip()
    
    def extract_skills(self, text: str) -> Dict[str, List[str]]:
        """Extract technical skills from text."""
        text_lower = text.lower()
        found_skills = {category: [] for category in self.technical_skills.keys()}
        
        for category, skills in self.technical_skills.items():
            for skill in skills:
                # Check for exact skill mentions
                if skill.lower() in text_lower:
                    found_skills[category].append(skill)
                # Check for variations
                variations = self._get_skill_variations(skill)
                for variation in variations:
                    if variation.lower() in text_lower:
                        found_skills[category].append(skill)
                        break
        
        return found_skills
    
    def _get_skill_variations(self, skill: str) -> List[str]:
        """Get common variations of skill names."""
        variations = [skill]
        skill_lower = skill.lower()
        
        # Common variations
        if skill_lower == 'python':
            variations.extend(['python3', 'python 3'])
        elif skill_lower == 'javascript':
            variations.extend(['js', 'node.js', 'nodejs'])
        elif skill_lower == 'machine learning':
            variations.extend(['ml', 'machine-learning'])
        elif skill_lower == 'deep learning':
            variations.extend(['dl', 'deep-learning'])
        elif skill_lower == 'natural language processing':
            variations.extend(['nlp', 'natural-language-processing'])
        
        return variations
    
    def extract_experience_years(self, text: str) -> float:
        """Extract years of experience from text."""
        # Look for patterns like "5 years experience", "5+ years", etc.
        patterns = [
            r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)',
            r'experience\s*:?\s*(\d+)\+?\s*(?:years?|yrs?)',
            r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s*)?work',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                return float(matches[0])
        
        return 0.0
    
    def extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education information."""
        education_keywords = [
            'bachelor', 'master', 'phd', 'doctorate', 'mba', 'b.s.', 'm.s.', 'b.a.', 'm.a.',
            'computer science', 'data science', 'machine learning', 'artificial intelligence'
        ]
        
        education_entries = []
        text_lower = text.lower()
        
        for keyword in education_keywords:
            if keyword in text_lower:
                # Extract context around the keyword
                index = text_lower.find(keyword)
                start = max(0, index - 50)
                end = min(len(text), index + 100)
                context = text[start:end].strip()
                
                education_entries.append({
                    'degree': keyword,
                    'context': context
                })
        
        return education_entries
    
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts."""
        try:
            embeddings1 = self.sentence_model.encode([text1])
            embeddings2 = self.sentence_model.encode([text2])
            similarity = cosine_similarity(embeddings1, embeddings2)[0][0]
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return 0.0
    
    def extract_key_phrases(self, text: str, max_phrases: int = 20) -> List[str]:
        """Extract key phrases from text using spaCy."""
        if not self.nlp:
            # Fallback to simple noun phrase extraction
            words = text.split()
            return [word for word in words if len(word) > 3][:max_phrases]
        
        doc = self.nlp(text)
        key_phrases = []
        
        # Extract noun phrases
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) <= 3:  # Keep phrases short
                key_phrases.append(chunk.text)
        
        # Extract named entities
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'PRODUCT', 'SKILL']:
                key_phrases.append(ent.text)
        
        return list(set(key_phrases))[:max_phrases]
    
    def assess_skill_proficiency(self, text: str, skill: str) -> int:
        """Assess proficiency level (1-5) for a specific skill."""
        text_lower = text.lower()
        skill_lower = skill.lower()
        
        proficiency_indicators = {
            5: ['expert', 'master', 'advanced', 'senior', 'lead', 'architect'],
            4: ['experienced', 'proficient', 'strong', 'skilled'],
            3: ['intermediate', 'moderate', 'comfortable', 'familiar'],
            2: ['basic', 'beginner', 'learning', 'some'],
            1: ['exposed', 'aware', 'minimal']
        }
        
        for level, indicators in proficiency_indicators.items():
            for indicator in indicators:
                if f"{indicator} {skill_lower}" in text_lower or f"{skill_lower} {indicator}" in text_lower:
                    return level
        
        # Default to intermediate if skill is mentioned but no proficiency indicator
        if skill_lower in text_lower:
            return 3
        
        return 0
    
    def detect_protected_attributes(self, text: str) -> List[str]:
        """Detect potentially protected attributes for compliance."""
        protected_patterns = {
            'gender': [r'\b(male|female|man|woman|he|she|him|her)\b'],
            'age': [r'\b(\d{2})\s*(years?|yrs?)\s*old\b', r'\b(teen|young|middle-aged|senior)\b'],
            'race': [r'\b(caucasian|african american|asian|hispanic|latino|black|white)\b'],
            'religion': [r'\b(christian|muslim|jewish|hindu|buddhist|catholic)\b'],
            'nationality': [r'\b(american|british|indian|chinese|japanese|german)\b']
        }
        
        detected = []
        text_lower = text.lower()
        
        for attribute, patterns in protected_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    detected.append(attribute)
                    break
        
        return detected
