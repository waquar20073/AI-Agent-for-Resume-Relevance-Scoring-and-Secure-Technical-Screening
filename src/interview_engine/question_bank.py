import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from src.utils.data_models import Question, QuestionType, DifficultyLevel

logger = logging.getLogger(__name__)

class QuestionBank:
    def __init__(self, question_bank_file: str = "data/question_bank.json"):
        self.question_bank_file = question_bank_file
        self.questions = {}
        self.categories = [
            "data_science_fundamentals",
            "statistics_probability", 
            "machine_learning",
            "deep_learning",
            "natural_language_processing",
            "computer_vision",
            "python_programming",
            "sql_databases",
            "cloud_platforms",
            "mlops_devops",
            "agentic_ai_systems",
            "prompt_engineering",
            "llm_fundamentals",
            "multi_agent_coordination",
            "ai_workflow_automation",
            "reinforcement_learning",
            "ethics_ai_safety"
        ]
        
        self.load_questions()
    
    def load_questions(self):
        """Load questions from file or create default questions."""
        try:
            with open(self.question_bank_file, 'r', encoding='utf-8') as f:
                questions_data = json.load(f)
                
            for q_data in questions_data:
                question = Question(
                    question_id=q_data['question_id'],
                    text=q_data['text'],
                    type=QuestionType(q_data['type']),
                    difficulty=DifficultyLevel(q_data['difficulty']),
                    category=q_data['category'],
                    topics=q_data['topics'],
                    expected_answer=q_data.get('expected_answer'),
                    code_template=q_data.get('code_template'),
                    time_limit=q_data['time_limit'],
                    points=q_data['points']
                )
                self.questions[question.question_id] = question
                
            logger.info(f"Loaded {len(self.questions)} questions from {self.question_bank_file}")
            
        except FileNotFoundError:
            logger.info("Question bank file not found. Creating default questions.")
            self.create_default_questions()
            self.save_questions()
        except Exception as e:
            logger.error(f"Error loading questions: {e}")
            self.create_default_questions()
    
    def create_default_questions(self):
        """Create a comprehensive set of default questions."""
        default_questions = [
            # Data Science Fundamentals
            {
                "question_id": str(uuid.uuid4()),
                "text": "Explain the difference between supervised, unsupervised, and reinforcement learning. Provide real-world examples for each.",
                "type": "conceptual",
                "difficulty": "beginner",
                "category": "data_science_fundamentals",
                "topics": ["machine_learning_types", "fundamentals"],
                "expected_answer": "Should explain the three main types of ML with examples like classification (supervised), clustering (unsupervised), and game playing (reinforcement)",
                "time_limit": 10,
                "points": 10
            },
            {
                "question_id": str(uuid.uuid4()),
                "text": "Write a Python function to calculate the mean, median, and mode of a list of numbers without using built-in statistical functions.",
                "type": "coding",
                "difficulty": "intermediate",
                "category": "data_science_fundamentals",
                "topics": ["statistics", "python_programming"],
                "code_template": "def calculate_statistics(numbers):\n    # Your code here\n    pass",
                "time_limit": 20,
                "points": 15
            },
            
            # Statistics & Probability
            {
                "question_id": str(uuid.uuid4()),
                "text": "Explain the Central Limit Theorem and its importance in statistical inference. How does it relate to hypothesis testing?",
                "type": "conceptual",
                "difficulty": "intermediate",
                "category": "statistics_probability",
                "topics": ["central_limit_theorem", "hypothesis_testing"],
                "expected_answer": "Should explain CLT, sampling distributions, and its role in enabling parametric tests",
                "time_limit": 15,
                "points": 12
            },
            {
                "question_id": str(uuid.uuid4()),
                "text": "A/B test results: Version A has 150 conversions out of 1000 users, Version B has 180 conversions out of 1000 users. Is Version B significantly better? Use appropriate statistical test.",
                "type": "practical",
                "difficulty": "intermediate",
                "category": "statistics_probability",
                "topics": ["ab_testing", "statistical_significance"],
                "expected_answer": "Should perform chi-square test or z-test for proportions and interpret p-value",
                "time_limit": 20,
                "points": 15
            },
            
            # Machine Learning
            {
                "question_id": str(uuid.uuid4()),
                "text": "Describe the bias-variance tradeoff in machine learning. How does it relate to model complexity and overfitting?",
                "type": "conceptual",
                "difficulty": "intermediate",
                "category": "machine_learning",
                "topics": ["bias_variance", "model_complexity"],
                "expected_answer": "Should explain the tradeoff, underfitting vs overfitting, and regularization techniques",
                "time_limit": 12,
                "points": 10
            },
            {
                "question_id": str(uuid.uuid4()),
                "text": "Implement a simple decision tree classifier from scratch in Python. Include methods for fitting and prediction.",
                "type": "coding",
                "difficulty": "advanced",
                "category": "machine_learning",
                "topics": ["decision_trees", "algorithms"],
                "code_template": "class SimpleDecisionTree:\n    def __init__(self, max_depth=3):\n        self.max_depth = max_depth\n    \n    def fit(self, X, y):\n        # Your code here\n        pass\n    \n    def predict(self, X):\n        # Your code here\n        pass",
                "time_limit": 30,
                "points": 20
            },
            
            # Deep Learning
            {
                "question_id": str(uuid.uuid4()),
                "text": "Explain the architecture of a Transformer model. How does attention mechanism work and why is it important?",
                "type": "conceptual",
                "difficulty": "advanced",
                "category": "deep_learning",
                "topics": ["transformers", "attention_mechanism"],
                "expected_answer": "Should explain multi-head attention, positional encoding, and advantages over RNNs",
                "time_limit": 15,
                "points": 15
            },
            {
                "question_id": str(uuid.uuid4()),
                "text": "Implement a simple neural network with backpropagation from scratch using only NumPy. Include forward and backward pass.",
                "type": "coding",
                "difficulty": "expert",
                "category": "deep_learning",
                "topics": ["neural_networks", "backpropagation"],
                "code_template": "import numpy as np\n\nclass NeuralNetwork:\n    def __init__(self, input_size, hidden_size, output_size):\n        # Initialize weights and biases\n        pass\n    \n    def forward(self, X):\n        # Forward propagation\n        pass\n    \n    def backward(self, X, y, output):\n        # Backward propagation\n        pass",
                "time_limit": 45,
                "points": 25
            },
            
            # Natural Language Processing
            {
                "question_id": str(uuid.uuid4()),
                "text": "Compare and contrast traditional NLP approaches (like TF-IDF, Bag of Words) with modern embedding-based approaches (like Word2Vec, BERT).",
                "type": "conceptual",
                "difficulty": "intermediate",
                "category": "natural_language_processing",
                "topics": ["feature_extraction", "embeddings"],
                "expected_answer": "Should discuss semantic understanding, context, and performance differences",
                "time_limit": 12,
                "points": 12
            },
            
            # Python Programming
            {
                "question_id": str(uuid.uuid4()),
                "text": "Write a Python decorator that measures execution time of any function and logs the results.",
                "type": "coding",
                "difficulty": "intermediate",
                "category": "python_programming",
                "topics": ["decorators", "performance"],
                "code_template": "import time\nimport functools\n\ndef timing_decorator(func):\n    @functools.wraps(func)\n    def wrapper(*args, **kwargs):\n        # Your code here\n        pass\n    return wrapper",
                "time_limit": 15,
                "points": 12
            },
            
            # Agentic AI Systems
            {
                "question_id": str(uuid.uuid4()),
                "text": "Design an architecture for a multi-agent system that can collaboratively solve complex data analysis tasks. Describe the agent roles and communication protocols.",
                "type": "conceptual",
                "difficulty": "advanced",
                "category": "agentic_ai_systems",
                "topics": ["multi_agent_systems", "architecture_design"],
                "expected_answer": "Should describe specialized agents, coordination mechanisms, and communication patterns",
                "time_limit": 20,
                "points": 18
            },
            {
                "question_id": str(uuid.uuid4()),
                "text": "Implement a simple agent that can use tools to answer questions about data. Include at least 3 tools: data loader, analyzer, and visualizer.",
                "type": "coding",
                "difficulty": "expert",
                "category": "agentic_ai_systems",
                "topics": ["agent_framework", "tool_usage"],
                "code_template": "class DataAnalysisAgent:\n    def __init__(self):\n        self.tools = {\n            'load_data': self.load_data,\n            'analyze_data': self.analyze_data,\n            'visualize_data': self.visualize_data\n        }\n    \n    def process_query(self, query):\n        # Your code here\n        pass",
                "time_limit": 40,
                "points": 25
            },
            
            # Prompt Engineering
            {
                "question_id": str(uuid.uuid4()),
                "text": "Explain the principles of effective prompt engineering for LLMs. Provide examples of good vs bad prompts for a specific task.",
                "type": "conceptual",
                "difficulty": "intermediate",
                "category": "prompt_engineering",
                "topics": ["prompt_design", "llm_interaction"],
                "expected_answer": "Should discuss clarity, context, examples, and iterative refinement",
                "time_limit": 12,
                "points": 10
            },
            {
                "question_id": str(uuid.uuid4()),
                "text": "Design a prompt template system that can dynamically generate prompts for different types of data analysis tasks. Include examples.",
                "type": "practical",
                "difficulty": "advanced",
                "category": "prompt_engineering",
                "topics": ["prompt_templates", "dynamic_generation"],
                "expected_answer": "Should show template structure, variable substitution, and task-specific adaptations",
                "time_limit": 25,
                "points": 15
            },
            
            # LLM Fundamentals
            {
                "question_id": str(uuid.uuid4()),
                "text": "How do Large Language Models handle context windows and what are the implications for long-document processing?",
                "type": "conceptual",
                "difficulty": "intermediate",
                "category": "llm_fundamentals",
                "topics": ["context_windows", "document_processing"],
                "expected_answer": "Should explain token limits, sliding windows, and chunking strategies",
                "time_limit": 10,
                "points": 10
            },
            
            # Multi-Agent Coordination
            {
                "question_id": str(uuid.uuid4()),
                "text": "Describe different coordination mechanisms for multi-agent systems (centralized, decentralized, hierarchical). Compare their advantages and disadvantages.",
                "type": "conceptual",
                "difficulty": "advanced",
                "category": "multi_agent_coordination",
                "topics": ["coordination_patterns", "system_architecture"],
                "expected_answer": "Should compare communication overhead, scalability, and fault tolerance",
                "time_limit": 15,
                "points": 15
            },
            
            # AI Workflow Automation
            {
                "question_id": str(uuid.uuid4()),
                "text": "Design an automated ML pipeline that can handle data preprocessing, model training, evaluation, and deployment. Include error handling and monitoring.",
                "type": "practical",
                "difficulty": "expert",
                "category": "ai_workflow_automation",
                "topics": ["mlops", "automation"],
                "expected_answer": "Should describe pipeline stages, orchestration, and monitoring strategies",
                "time_limit": 30,
                "points": 20
            },
            
            # Ethics & AI Safety
            {
                "question_id": str(uuid.uuid4()),
                "text": "Discuss the ethical considerations in deploying AI systems for hiring. What safeguards should be implemented to ensure fairness?",
                "type": "conceptual",
                "difficulty": "intermediate",
                "category": "ethics_ai_safety",
                "topics": ["ai_ethics", "fairness"],
                "expected_answer": "Should discuss bias mitigation, transparency, and accountability measures",
                "time_limit": 15,
                "points": 12
            }
        ]
        
        for q_data in default_questions:
            question = Question(
                question_id=q_data['question_id'],
                text=q_data['text'],
                type=QuestionType(q_data['type']),
                difficulty=DifficultyLevel(q_data['difficulty']),
                category=q_data['category'],
                topics=q_data['topics'],
                expected_answer=q_data.get('expected_answer'),
                code_template=q_data.get('code_template'),
                time_limit=q_data['time_limit'],
                points=q_data['points']
            )
            self.questions[question.question_id] = question
    
    def save_questions(self):
        """Save questions to file."""
        try:
            questions_data = []
            for question in self.questions.values():
                q_data = {
                    'question_id': question.question_id,
                    'text': question.text,
                    'type': question.type.value,
                    'difficulty': question.difficulty.value,
                    'category': question.category,
                    'topics': question.topics,
                    'time_limit': question.time_limit,
                    'points': question.points
                }
                
                if question.expected_answer:
                    q_data['expected_answer'] = question.expected_answer
                if question.code_template:
                    q_data['code_template'] = question.code_template
                    
                questions_data.append(q_data)
            
            with open(self.question_bank_file, 'w', encoding='utf-8') as f:
                json.dump(questions_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(questions_data)} questions to {self.question_bank_file}")
            
        except Exception as e:
            logger.error(f"Error saving questions: {e}")
    
    def get_question_by_id(self, question_id: str) -> Optional[Question]:
        """Get a specific question by ID."""
        return self.questions.get(question_id)
    
    def get_questions_by_category(self, category: str, difficulty: Optional[DifficultyLevel] = None) -> List[Question]:
        """Get questions filtered by category and optionally difficulty."""
        filtered_questions = []
        
        for question in self.questions.values():
            if question.category == category:
                if difficulty is None or question.difficulty == difficulty:
                    filtered_questions.append(question)
        
        return filtered_questions
    
    def get_questions_by_difficulty(self, difficulty: DifficultyLevel) -> List[Question]:
        """Get all questions of a specific difficulty level."""
        return [q for q in self.questions.values() if q.difficulty == difficulty]
    
    def get_questions_by_topics(self, topics: List[str]) -> List[Question]:
        """Get questions that contain any of the specified topics."""
        filtered_questions = []
        
        for question in self.questions.values():
            if any(topic in question.topics for topic in topics):
                filtered_questions.append(question)
        
        return filtered_questions
    
    def get_random_questions(self, count: int, categories: Optional[List[str]] = None, 
                           difficulty: Optional[DifficultyLevel] = None) -> List[Question]:
        """Get random questions with optional filtering."""
        import random
        
        candidates = []
        
        for question in self.questions.values():
            if categories and question.category not in categories:
                continue
            if difficulty and question.difficulty != difficulty:
                continue
            candidates.append(question)
        
        if len(candidates) < count:
            logger.warning(f"Requested {count} questions but only {len(candidates)} available")
            return candidates
        
        return random.sample(candidates, count)
    
    def get_balanced_question_set(self, count: int, target_categories: List[str]) -> List[Question]:
        """Get a balanced set of questions across categories."""
        questions_per_category = max(1, count // len(target_categories))
        selected_questions = []
        
        for category in target_categories:
            category_questions = self.get_questions_by_category(category)
            if category_questions:
                # Get a mix of difficulties
                difficulties = [DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE, 
                              DifficultyLevel.ADVANCED, DifficultyLevel.EXPERT]
                
                for diff in difficulties:
                    diff_questions = [q for q in category_questions if q.difficulty == diff]
                    if diff_questions and len(selected_questions) < count:
                        selected_questions.append(diff_questions[0])
        
        # Fill remaining slots if needed
        while len(selected_questions) < count:
            remaining_questions = [q for q in self.questions.values() if q not in selected_questions]
            if remaining_questions:
                selected_questions.append(remaining_questions[0])
            else:
                break
        
        return selected_questions[:count]
    
    def add_question(self, question: Question) -> bool:
        """Add a new question to the bank."""
        try:
            self.questions[question.question_id] = question
            self.save_questions()
            logger.info(f"Added question {question.question_id} to question bank")
            return True
        except Exception as e:
            logger.error(f"Error adding question: {e}")
            return False
    
    def update_question(self, question: Question) -> bool:
        """Update an existing question."""
        if question.question_id not in self.questions:
            logger.error(f"Question {question.question_id} not found")
            return False
        
        try:
            self.questions[question.question_id] = question
            self.save_questions()
            logger.info(f"Updated question {question.question_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating question: {e}")
            return False
    
    def delete_question(self, question_id: str) -> bool:
        """Delete a question from the bank."""
        if question_id not in self.questions:
            logger.error(f"Question {question_id} not found")
            return False
        
        try:
            del self.questions[question_id]
            self.save_questions()
            logger.info(f"Deleted question {question_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting question: {e}")
            return False
    
    def get_question_statistics(self) -> Dict[str, Any]:
        """Get statistics about the question bank."""
        stats = {
            'total_questions': len(self.questions),
            'by_difficulty': {},
            'by_category': {},
            'by_type': {},
            'average_time_limit': 0,
            'total_points': 0
        }
        
        total_time = 0
        total_points = 0
        
        for question in self.questions.values():
            # Count by difficulty
            diff_key = question.difficulty.value
            stats['by_difficulty'][diff_key] = stats['by_difficulty'].get(diff_key, 0) + 1
            
            # Count by category
            stats['by_category'][question.category] = stats['by_category'].get(question.category, 0) + 1
            
            # Count by type
            type_key = question.type.value
            stats['by_type'][type_key] = stats['by_type'].get(type_key, 0) + 1
            
            total_time += question.time_limit
            total_points += question.points
        
        stats['average_time_limit'] = total_time / len(self.questions) if self.questions else 0
        stats['total_points'] = total_points
        
        return stats
    
    def validate_question(self, question: Question) -> List[str]:
        """Validate a question and return list of issues."""
        issues = []
        
        if not question.text or len(question.text.strip()) < 10:
            issues.append("Question text is too short or empty")
        
        if question.time_limit <= 0 or question.time_limit > 120:
            issues.append("Time limit should be between 1 and 120 minutes")
        
        if question.points <= 0 or question.points > 50:
            issues.append("Points should be between 1 and 50")
        
        if question.category not in self.categories:
            issues.append(f"Unknown category: {question.category}")
        
        if not question.topics:
            issues.append("Question should have at least one topic")
        
        if question.type == QuestionType.CODING and not question.code_template:
            issues.append("Coding questions should have a code template")
        
        return issues
