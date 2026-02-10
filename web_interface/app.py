from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import os
import uuid
import json
from datetime import datetime
import logging

# Import our modules
from src.resume_scorer.parser import ResumeParser
from src.resume_scorer.scorer import ResumeScorer
from src.resume_scorer.compliance import ResumeComplianceChecker
from src.interview_engine.adaptive_interview import AdaptiveInterviewEngine
from src.compliance.audit_logger import AuditLogger
from src.interview_engine.evaluator import InterviewEvaluator
from config.settings import Config

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize components
resume_parser = ResumeParser()
resume_scorer = ResumeScorer()
compliance_checker = ResumeComplianceChecker()
interview_engine = AdaptiveInterviewEngine()
audit_logger = AuditLogger()
interview_evaluator = InterviewEvaluator()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Home page."""
    return render_template('index.html')

@app.route('/resume_upload')
def resume_upload_page():
    """Resume upload page."""
    return render_template('resume_upload.html')

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    """Handle resume upload and scoring."""
    try:
        if 'resume' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['resume']
        job_description = request.form.get('job_description', '')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                # Parse resume
                resume_data = resume_parser.parse_resume(filepath)
                
                # Parse job description
                job_desc = resume_parser.parse_job_description(job_description, "Uploaded Position")
                
                # Score resume
                scoring_result = resume_scorer.score_resume(resume_data, job_desc)
                
                # Check compliance
                compliance_results = compliance_checker.check_resume_compliance(resume_data, job_desc)
                
                # Store results in session
                session['scoring_result'] = {
                    'overall_score': scoring_result.overall_score,
                    'skill_match_score': scoring_result.skill_match_score,
                    'experience_score': scoring_result.experience_score,
                    'education_score': scoring_result.education_score,
                    'certification_score': scoring_result.certification_score,
                    'matched_skills': scoring_result.matched_skills,
                    'missing_skills': scoring_result.missing_skills,
                    'explanation': scoring_result.explanation,
                    'compliance_score': compliance_results['overall_compliance_score'],
                    'compliance_flags': compliance_results['bias_flags'] + compliance_results['privacy_flags']
                }
                
                session['candidate_id'] = resume_data.candidate_id
                
                return jsonify({
                    'success': True,
                    'redirect': url_for('scoring_results')
                })
            finally:
                # Clean up uploaded file
                if os.path.exists(filepath):
                    os.remove(filepath)
        
        return jsonify({'error': 'File type not allowed'}), 400
        
    except Exception as e:
        logger.error(f"Error uploading resume: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/scoring_results')
def scoring_results():
    """Display resume scoring results."""
    if 'scoring_result' not in session:
        flash('No scoring results available. Please upload a resume first.', 'error')
        return redirect(url_for('resume_upload_page'))
    
    results = session['scoring_result']
    return render_template('results.html', results=results)

@app.route('/interview')
def interview_page():
    """Interview page."""
    if 'candidate_id' not in session:
        flash('Please complete resume scoring first.', 'error')
        return redirect(url_for('resume_upload_page'))
    
    return render_template('interview.html', candidate_id=session['candidate_id'])

@app.route('/start_interview', methods=['POST'])
def start_interview():
    """Start an interview session."""
    try:
        data = request.get_json()
        candidate_id = data.get('candidate_id')
        job_id = data.get('job_id', str(uuid.uuid4()))
        target_categories = data.get('categories', [])
        
        # Start interview session
        interview_session = interview_engine.start_interview_session(
            candidate_id, job_id, target_categories
        )
        
        # Store session ID in user session
        session['interview_session_id'] = interview_session.session_id
        
        return jsonify({
            'success': True,
            'session_id': interview_session.session_id,
            'first_question': {
                'text': interview_session.current_question.text,
                'type': interview_session.current_question.type.value,
                'difficulty': interview_session.current_question.difficulty.value,
                'category': interview_session.current_question.category,
                'time_limit': interview_session.current_question.time_limit,
                'code_template': interview_session.current_question.code_template
            }
        })
        
    except Exception as e:
        logger.error(f"Error starting interview: {e}")
        return jsonify({'error': 'Failed to start interview'}), 500

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    """Submit an answer to the current question."""
    try:
        data = request.get_json()
        session_id = session.get('interview_session_id')
        
        if not session_id:
            return jsonify({'error': 'No active interview session'}), 400
        
        answer_text = data.get('answer', '')
        time_taken = data.get('time_taken', 0)
        code_snippet = data.get('code_snippet', '')
        
        # Submit answer
        result = interview_engine.submit_answer(
            session_id, answer_text, time_taken, code_snippet
        )
        
        response_data = {
            'answer_score': result['answer_score'],
            'answer_feedback': result['answer_feedback'],
            'session_complete': result['session_complete'],
            'session_progress': result['session_progress']
        }
        
        if not result['session_complete'] and result['next_question']:
            response_data['next_question'] = {
                'text': result['next_question'].text,
                'type': result['next_question'].type.value,
                'difficulty': result['next_question'].difficulty.value,
                'category': result['next_question'].category,
                'time_limit': result['next_question'].time_limit,
                'code_template': result['next_question'].code_template
            }
        else:
            response_data['interview_report'] = result['interview_report']
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error submitting answer: {e}")
        return jsonify({'error': 'Failed to submit answer'}), 500

@app.route('/interview_report')
def interview_report():
    """Display interview report."""
    if 'interview_session_id' not in session:
        flash('No interview session found.', 'error')
        return redirect(url_for('interview_page'))
    
    try:
        # Get session status
        session_id = session['interview_session_id']
        status = interview_engine.get_session_status(session_id)
        
        if status['is_active']:
            flash('Interview session is still active. Please complete the interview first.', 'warning')
            return redirect(url_for('interview_page'))
        
        # For demo purposes, create a mock report
        # In a real implementation, this would come from the completed session
        mock_report = {
            'session_id': session_id,
            'candidate_id': status['candidate_id'],
            'overall_score': 75.5,
            'domain_scores': {
                'data_science_fundamentals': 80.0,
                'machine_learning': 70.0,
                'python_programming': 85.0,
                'agentic_ai_systems': 65.0
            },
            'strengths': [
                'Strong programming skills',
                'Good understanding of data science fundamentals'
            ],
            'weaknesses': [
                'Limited experience with agentic AI systems',
                'Needs improvement in advanced ML concepts'
            ],
            'recommendations': [
                'Study multi-agent coordination patterns',
                'Practice advanced machine learning techniques'
            ],
            'integrity_metrics': {
                'average_integrity_score': 95.0,
                'copy_paste_incidents': 0,
                'timing_anomalies': 0,
                'browser_anomalies': 0
            },
            'compliance_summary': {
                'overall_status': 'compliant',
                'integrity_score': 95.0,
                'violations': 0
            }
        }
        
        # Evaluate the performance
        evaluation = interview_evaluator.evaluate_candidate_performance(mock_report)
        
        return render_template('interview_report.html', 
                             report=mock_report, 
                             evaluation=evaluation)
        
    except Exception as e:
        logger.error(f"Error generating interview report: {e}")
        flash('Error generating interview report.', 'error')
        return redirect(url_for('interview_page'))

@app.route('/api/compliance_check', methods=['POST'])
def compliance_check():
    """API endpoint for compliance checking."""
    try:
        data = request.get_json()
        text = data.get('text', '')
        text_type = data.get('type', 'general')
        
        # Check for bias
        from src.compliance.bias_detector import BiasDetector
        bias_detector = BiasDetector()
        bias_results = bias_detector.detect_bias_in_text(text, text_type)
        
        return jsonify({
            'bias_score': bias_results['overall_bias_score'],
            'risk_level': 'HIGH' if bias_results['overall_bias_score'] > Config.BIAS_THRESHOLD else 'LOW',
            'recommendations': bias_results['recommendations']
        })
        
    except Exception as e:
        logger.error(f"Error in compliance check: {e}")
        return jsonify({'error': 'Compliance check failed'}), 500

@app.route('/dashboard')
def dashboard():
    """Admin dashboard."""
    try:
        # Get compliance statistics
        compliance_stats = audit_logger.get_compliance_statistics(days=7)
        
        # Get question bank statistics
        from src.interview_engine.question_bank import QuestionBank
        question_bank = QuestionBank()
        question_stats = question_bank.get_question_statistics()
        
        dashboard_data = {
            'compliance_stats': compliance_stats,
            'question_stats': question_stats,
            'recent_activity': []  # Would be populated from database
        }
        
        return render_template('dashboard.html', data=dashboard_data)
        
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        flash('Error loading dashboard.', 'error')
        return redirect(url_for('index'))

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    flash('File is too large. Maximum size is 16MB.', 'error')
    return redirect(url_for('resume_upload_page'))

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {e}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
