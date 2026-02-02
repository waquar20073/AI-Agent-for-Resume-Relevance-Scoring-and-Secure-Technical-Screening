from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import uuid
import json
import logging
from pathlib import Path
from src.utils.data_models import ComplianceLog

logger = logging.getLogger(__name__)

class AuditLogger:
    def __init__(self, log_file_path: str = "logs/compliance_audit.log"):
        self.log_file_path = Path(log_file_path)
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.session_logs = {}  # In-memory storage for active sessions
        
    def log_event(self, session_id: Optional[str], event_type: str, description: str, 
                  severity: str = "low", metadata: Dict[str, Any] = None) -> str:
        """Log a compliance event."""
        log_entry = ComplianceLog(
            log_id=str(uuid.uuid4()),
            session_id=session_id,
            event_type=event_type,
            description=description,
            severity=severity,
            metadata=metadata or {},
            timestamp=datetime.now()
        )
        
        # Store in memory for active sessions
        if session_id:
            if session_id not in self.session_logs:
                self.session_logs[session_id] = []
            self.session_logs[session_id].append(log_entry)
        
        # Write to file
        self._write_log_to_file(log_entry)
        
        logger.info(f"Audit log created: {log_entry.log_id} - {event_type}")
        return log_entry.log_id
    
    def _write_log_to_file(self, log_entry: ComplianceLog):
        """Write log entry to file."""
        log_data = {
            'log_id': log_entry.log_id,
            'session_id': log_entry.session_id,
            'event_type': log_entry.event_type,
            'description': log_entry.description,
            'severity': log_entry.severity,
            'metadata': log_entry.metadata,
            'timestamp': log_entry.timestamp.isoformat()
        }
        
        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_data) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log to file: {e}")
    
    def get_session_logs(self, session_id: str) -> List[ComplianceLog]:
        """Get all logs for a specific session."""
        return self.session_logs.get(session_id, [])
    
    def get_logs_by_time_range(self, start_time: datetime, end_time: datetime) -> List[ComplianceLog]:
        """Get logs within a time range."""
        logs = []
        
        # Read from file
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_data = json.loads(line.strip())
                        timestamp = datetime.fromisoformat(log_data['timestamp'])
                        
                        if start_time <= timestamp <= end_time:
                            log_entry = ComplianceLog(
                                log_id=log_data['log_id'],
                                session_id=log_data['session_id'],
                                event_type=log_data['event_type'],
                                description=log_data['description'],
                                severity=log_data['severity'],
                                metadata=log_data['metadata'],
                                timestamp=timestamp
                            )
                            logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            logger.warning(f"Audit log file not found: {self.log_file_path}")
        
        return logs
    
    def get_logs_by_event_type(self, event_type: str, limit: int = 100) -> List[ComplianceLog]:
        """Get logs by event type."""
        logs = []
        
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_data = json.loads(line.strip())
                        if log_data['event_type'] == event_type:
                            log_entry = ComplianceLog(
                                log_id=log_data['log_id'],
                                session_id=log_data['session_id'],
                                event_type=log_data['event_type'],
                                description=log_data['description'],
                                severity=log_data['severity'],
                                metadata=log_data['metadata'],
                                timestamp=datetime.fromisoformat(log_data['timestamp'])
                            )
                            logs.append(log_entry)
                            
                            if len(logs) >= limit:
                                break
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            logger.warning(f"Audit log file not found: {self.log_file_path}")
        
        return logs
    
    def get_high_severity_logs(self, hours: int = 24) -> List[ComplianceLog]:
        """Get high severity logs from the last N hours."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        logs = self.get_logs_by_time_range(start_time, end_time)
        return [log for log in logs if log.severity == "high"]
    
    def generate_compliance_report(self, session_id: str) -> Dict[str, Any]:
        """Generate comprehensive compliance report for a session."""
        session_logs = self.get_session_logs(session_id)
        
        if not session_logs:
            return {
                'session_id': session_id,
                'error': 'No logs found for this session'
            }
        
        # Analyze logs
        event_types = {}
        severity_counts = {'low': 0, 'medium': 0, 'high': 0}
        timeline = []
        
        for log in session_logs:
            # Count event types
            event_types[log.event_type] = event_types.get(log.event_type, 0) + 1
            
            # Count severities
            severity_counts[log.severity] += 1
            
            # Build timeline
            timeline.append({
                'timestamp': log.timestamp.isoformat(),
                'event_type': log.event_type,
                'description': log.description,
                'severity': log.severity
            })
        
        # Sort timeline by timestamp
        timeline.sort(key=lambda x: x['timestamp'])
        
        # Calculate compliance metrics
        total_events = len(session_logs)
        high_severity_percentage = (severity_counts['high'] / total_events) * 100 if total_events > 0 else 0
        
        compliance_score = max(0, 100 - (high_severity_percentage * 2))  # Deduct points for high severity events
        
        report = {
            'session_id': session_id,
            'generated_at': datetime.now().isoformat(),
            'total_events': total_events,
            'compliance_score': compliance_score,
            'risk_level': 'HIGH' if compliance_score < 70 else 'MEDIUM' if compliance_score < 90 else 'LOW',
            'event_types': event_types,
            'severity_breakdown': severity_counts,
            'timeline': timeline,
            'recommendations': self._generate_report_recommendations(severity_counts, event_types)
        }
        
        return report
    
    def _generate_report_recommendations(self, severity_counts: Dict[str, int], 
                                        event_types: Dict[str, int]) -> List[str]:
        """Generate recommendations based on log analysis."""
        recommendations = []
        
        # High severity recommendations
        if severity_counts['high'] > 0:
            recommendations.append("Review high severity events - immediate attention required")
        
        # Event type specific recommendations
        if 'bias_detection' in event_types and event_types['bias_detection'] > 2:
            recommendations.append("Multiple bias detection events - review content for discriminatory language")
        
        if 'integrity_analysis' in event_types and event_types['integrity_analysis'] > 5:
            recommendations.append("Frequent integrity issues - consider additional monitoring")
        
        if 'resume_compliance_check' in event_types:
            recommendations.append("Resume compliance checks performed - review scoring fairness")
        
        # General recommendations
        total_events = sum(severity_counts.values())
        if total_events > 20:
            recommendations.append("High number of compliance events - consider process review")
        
        return recommendations
    
    def export_session_logs(self, session_id: str, format: str = "json") -> str:
        """Export session logs in specified format."""
        session_logs = self.get_session_logs(session_id)
        
        if format.lower() == "json":
            return json.dumps([
                {
                    'log_id': log.log_id,
                    'session_id': log.session_id,
                    'event_type': log.event_type,
                    'description': log.description,
                    'severity': log.severity,
                    'metadata': log.metadata,
                    'timestamp': log.timestamp.isoformat()
                }
                for log in session_logs
            ], indent=2)
        
        elif format.lower() == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow(['log_id', 'session_id', 'event_type', 'description', 'severity', 'timestamp'])
            
            # Data
            for log in session_logs:
                writer.writerow([
                    log.log_id,
                    log.session_id,
                    log.event_type,
                    log.description,
                    log.severity,
                    log.timestamp.isoformat()
                ])
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up old log files."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        try:
            # Read existing logs
            current_logs = []
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_data = json.loads(line.strip())
                        timestamp = datetime.fromisoformat(log_data['timestamp'])
                        
                        if timestamp >= cutoff_date:
                            current_logs.append(line)
                    except json.JSONDecodeError:
                        continue
            
            # Write back only recent logs
            with open(self.log_file_path, 'w', encoding='utf-8') as f:
                f.writelines(current_logs)
            
            logger.info(f"Cleaned up audit logs older than {days_to_keep} days")
            
        except FileNotFoundError:
            logger.warning(f"Audit log file not found: {self.log_file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")
    
    def get_compliance_statistics(self, days: int = 7) -> Dict[str, Any]:
        """Get compliance statistics for the last N days."""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        logs = self.get_logs_by_time_range(start_time, end_time)
        
        if not logs:
            return {
                'period': f"Last {days} days",
                'total_events': 0,
                'event_types': {},
                'severity_breakdown': {'low': 0, 'medium': 0, 'high': 0},
                'daily_breakdown': {}
            }
        
        # Analyze logs
        event_types = {}
        severity_counts = {'low': 0, 'medium': 0, 'high': 0}
        daily_breakdown = {}
        
        for log in logs:
            # Count event types
            event_types[log.event_type] = event_types.get(log.event_type, 0) + 1
            
            # Count severities
            severity_counts[log.severity] += 1
            
            # Daily breakdown
            date_key = log.timestamp.date().isoformat()
            if date_key not in daily_breakdown:
                daily_breakdown[date_key] = {'total': 0, 'high': 0}
            daily_breakdown[date_key]['total'] += 1
            if log.severity == 'high':
                daily_breakdown[date_key]['high'] += 1
        
        return {
            'period': f"Last {days} days",
            'total_events': len(logs),
            'event_types': event_types,
            'severity_breakdown': severity_counts,
            'daily_breakdown': daily_breakdown,
            'compliance_trend': self._calculate_compliance_trend(daily_breakdown)
        }
    
    def _calculate_compliance_trend(self, daily_breakdown: Dict[str, Dict]) -> str:
        """Calculate compliance trend based on daily breakdown."""
        if len(daily_breakdown) < 2:
            return "insufficient_data"
        
        dates = sorted(daily_breakdown.keys())
        recent_days = dates[-3:]  # Last 3 days
        earlier_days = dates[-6:-3] if len(dates) >= 6 else dates[:-3]
        
        if not earlier_days:
            return "insufficient_data"
        
        # Calculate average high severity events
        recent_high = sum(daily_breakdown[date]['high'] for date in recent_days) / len(recent_days)
        earlier_high = sum(daily_breakdown[date]['high'] for date in earlier_days) / len(earlier_days)
        
        if recent_high > earlier_high * 1.2:
            return "deteriorating"
        elif recent_high < earlier_high * 0.8:
            return "improving"
        else:
            return "stable"
    
    def archive_session_logs(self, session_id: str, archive_path: str):
        """Archive session logs to a separate file."""
        session_logs = self.get_session_logs(session_id)
        
        if not session_logs:
            logger.warning(f"No logs to archive for session {session_id}")
            return
        
        archive_data = {
            'session_id': session_id,
            'archived_at': datetime.now().isoformat(),
            'logs': [
                {
                    'log_id': log.log_id,
                    'event_type': log.event_type,
                    'description': log.description,
                    'severity': log.severity,
                    'metadata': log.metadata,
                    'timestamp': log.timestamp.isoformat()
                }
                for log in session_logs
            ]
        }
        
        try:
            with open(archive_path, 'w', encoding='utf-8') as f:
                json.dump(archive_data, f, indent=2)
            
            logger.info(f"Archived {len(session_logs)} logs for session {session_id} to {archive_path}")
            
        except Exception as e:
            logger.error(f"Failed to archive session logs: {e}")
    
    def clear_session_logs(self, session_id: str):
        """Clear logs for a specific session from memory."""
        if session_id in self.session_logs:
            del self.session_logs[session_id]
            logger.info(f"Cleared logs for session {session_id} from memory")
