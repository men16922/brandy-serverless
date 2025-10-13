"""
Session Manager for DynamoDB operations
Handles session CRUD operations and state management
"""

import boto3
import json
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from botocore.exceptions import ClientError

from .models import WorkflowSession, BusinessInfo, SessionStatus, WorkflowStep, AgentLog


class SessionManager:
    """Manages workflow sessions in DynamoDB"""
    
    def __init__(self, table_name: str = None, endpoint_url: str = None):
        """Initialize session manager
        
        Args:
            table_name: DynamoDB table name (defaults to env var)
            endpoint_url: DynamoDB endpoint URL (for local development)
        """
        self.table_name = table_name or os.getenv('DYNAMODB_TABLE_NAME', 'branding-chatbot-sessions-local')
        
        # Configure DynamoDB client
        dynamodb_config = {
            'region_name': os.getenv('AWS_REGION', 'us-east-1')
        }
        
        if endpoint_url or os.getenv('DYNAMODB_ENDPOINT'):
            dynamodb_config['endpoint_url'] = endpoint_url or os.getenv('DYNAMODB_ENDPOINT')
            # For local development
            dynamodb_config['aws_access_key_id'] = 'dummy'
            dynamodb_config['aws_secret_access_key'] = 'dummy'
        
        self.dynamodb = boto3.client('dynamodb', **dynamodb_config)
        self.table = boto3.resource('dynamodb', **dynamodb_config).Table(self.table_name)
    
    def create_session(self, business_info: BusinessInfo) -> WorkflowSession:
        """Create a new workflow session
        
        Args:
            business_info: Business information for the session
            
        Returns:
            Created workflow session
            
        Raises:
            ValueError: If business info is invalid
            ClientError: If DynamoDB operation fails
        """
        if not business_info.validate():
            raise ValueError("Invalid business information provided")
        
        session = WorkflowSession.create_new(business_info)
        
        try:
            # Store in DynamoDB
            item = session.to_dict()
            self.table.put_item(Item=item)
            
            return session
            
        except ClientError as e:
            raise ClientError(f"Failed to create session: {e}")
    
    def get_session(self, session_id: str) -> Optional[WorkflowSession]:
        """Get workflow session by ID
        
        Args:
            session_id: Session identifier
            
        Returns:
            Workflow session or None if not found
        """
        try:
            response = self.table.get_item(Key={'sessionId': session_id})
            
            if 'Item' not in response:
                return None
            
            session = WorkflowSession.from_dict(response['Item'])
            
            # Check if session is expired
            if session.is_expired():
                session.status = SessionStatus.EXPIRED.value
                self.update_session(session)
                return session
            
            return session
            
        except ClientError as e:
            print(f"Error getting session {session_id}: {e}")
            return None
    
    def update_session(self, session: WorkflowSession) -> bool:
        """Update workflow session
        
        Args:
            session: Session to update
            
        Returns:
            True if successful, False otherwise
        """
        if not session.validate():
            raise ValueError("Invalid session data")
        
        try:
            # Update timestamp
            session.updated_at = datetime.utcnow().isoformat()
            
            # Store in DynamoDB
            item = session.to_dict()
            self.table.put_item(Item=item)
            
            return True
            
        except ClientError as e:
            print(f"Error updating session {session.session_id}: {e}")
            return False
    
    def update_session_step(self, session_id: str, step: WorkflowStep) -> bool:
        """Update session workflow step
        
        Args:
            session_id: Session identifier
            step: New workflow step
            
        Returns:
            True if successful, False otherwise
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.update_step(step)
        return self.update_session(session)
    
    def add_agent_log(self, session_id: str, agent_log: AgentLog) -> bool:
        """Add agent execution log to session
        
        Args:
            session_id: Session identifier
            agent_log: Agent log entry
            
        Returns:
            True if successful, False otherwise
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.add_agent_log(agent_log)
        return self.update_session(session)
    
    def mark_session_completed(self, session_id: str) -> bool:
        """Mark session as completed
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful, False otherwise
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.mark_completed()
        return self.update_session(session)
    
    def mark_session_failed(self, session_id: str, error_message: str = None) -> bool:
        """Mark session as failed
        
        Args:
            session_id: Session identifier
            error_message: Optional error message
            
        Returns:
            True if successful, False otherwise
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.mark_failed(error_message)
        return self.update_session(session)
    
    def get_sessions_by_status(self, status: SessionStatus, limit: int = 50) -> List[WorkflowSession]:
        """Get sessions by status (for Supervisor Agent monitoring)
        
        Args:
            status: Session status to filter by
            limit: Maximum number of sessions to return
            
        Returns:
            List of workflow sessions
        """
        try:
            response = self.table.query(
                IndexName='StatusIndex',
                KeyConditionExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': status.value},
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            
            sessions = []
            for item in response.get('Items', []):
                session = WorkflowSession.from_dict(item)
                sessions.append(session)
            
            return sessions
            
        except ClientError as e:
            print(f"Error querying sessions by status {status.value}: {e}")
            return []
    
    def get_sessions_by_step(self, step: WorkflowStep, limit: int = 50) -> List[WorkflowSession]:
        """Get sessions by current step (for workflow monitoring)
        
        Args:
            step: Workflow step to filter by
            limit: Maximum number of sessions to return
            
        Returns:
            List of workflow sessions
        """
        try:
            response = self.table.query(
                IndexName='StepIndex',
                KeyConditionExpression='currentStep = :step',
                ExpressionAttributeValues={':step': step.value},
                ScanIndexForward=False,  # Most recent first
                Limit=limit
            )
            
            sessions = []
            for item in response.get('Items', []):
                session = WorkflowSession.from_dict(item)
                sessions.append(session)
            
            return sessions
            
        except ClientError as e:
            print(f"Error querying sessions by step {step.value}: {e}")
            return []
    
    def get_active_sessions(self, limit: int = 100) -> List[WorkflowSession]:
        """Get all active sessions (for Supervisor Agent monitoring)
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of active workflow sessions
        """
        return self.get_sessions_by_status(SessionStatus.ACTIVE, limit)
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions (manual cleanup for local dev)
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            # Scan for expired sessions
            response = self.table.scan(
                FilterExpression='#ttl < :now',
                ExpressionAttributeNames={'#ttl': 'ttl'},
                ExpressionAttributeValues={':now': int(datetime.utcnow().timestamp())}
            )
            
            cleaned_count = 0
            for item in response.get('Items', []):
                session_id = item['sessionId']
                
                # Mark as expired and update
                session = WorkflowSession.from_dict(item)
                session.status = SessionStatus.EXPIRED.value
                self.update_session(session)
                
                cleaned_count += 1
            
            return cleaned_count
            
        except ClientError as e:
            print(f"Error cleaning up expired sessions: {e}")
            return 0
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """Get session statistics for monitoring
        
        Returns:
            Dictionary with session statistics
        """
        try:
            # Get counts by status
            stats = {
                'total_sessions': 0,
                'active_sessions': 0,
                'completed_sessions': 0,
                'failed_sessions': 0,
                'expired_sessions': 0,
                'sessions_by_step': {
                    'analysis': 0,
                    'naming': 0,
                    'signboard': 0,
                    'interior': 0,
                    'report': 0
                }
            }
            
            # Scan all sessions (for small datasets)
            response = self.table.scan()
            
            for item in response.get('Items', []):
                stats['total_sessions'] += 1
                
                status = item.get('status', '')
                if status == SessionStatus.ACTIVE.value:
                    stats['active_sessions'] += 1
                elif status == SessionStatus.COMPLETED.value:
                    stats['completed_sessions'] += 1
                elif status == SessionStatus.FAILED.value:
                    stats['failed_sessions'] += 1
                elif status == SessionStatus.EXPIRED.value:
                    stats['expired_sessions'] += 1
                
                # Count by step
                current_step = item.get('currentStep', 0)
                if current_step == 1:
                    stats['sessions_by_step']['analysis'] += 1
                elif current_step == 2:
                    stats['sessions_by_step']['naming'] += 1
                elif current_step == 3:
                    stats['sessions_by_step']['signboard'] += 1
                elif current_step == 4:
                    stats['sessions_by_step']['interior'] += 1
                elif current_step == 5:
                    stats['sessions_by_step']['report'] += 1
            
            return stats
            
        except ClientError as e:
            print(f"Error getting session statistics: {e}")
            return {}
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for DynamoDB connection
        
        Returns:
            Health check results
        """
        try:
            # Try to describe the table
            response = self.dynamodb.describe_table(TableName=self.table_name)
            
            return {
                'status': 'healthy',
                'table_name': self.table_name,
                'table_status': response['Table']['TableStatus'],
                'item_count': response['Table'].get('ItemCount', 0),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except ClientError as e:
            return {
                'status': 'unhealthy',
                'table_name': self.table_name,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }


# Global session manager instance
_session_manager = None

def get_session_manager() -> SessionManager:
    """Get global session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager