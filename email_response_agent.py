from typing import List, Dict, Any, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64
from dataclasses import dataclass
from datetime import datetime
from scheduler_agency import Task

@dataclass
class EmailTemplate:
    subject: str
    body: str
    
class EmailResponseAgent:
    def __init__(self, google_auth_manager):
        self.credentials = google_auth_manager.get_credentials()
        self.gmail_service = build('gmail', 'v1', credentials=self.credentials)
        self.templates = self._initialize_templates()
        
    def _initialize_templates(self) -> Dict[str, EmailTemplate]:
        """Initialize email templates for different scenarios"""
        return {
            "task_assignment": EmailTemplate(
                subject="New Task Assignment",
                body="You have been assigned a new task:\n\nTitle: {title}\nPriority: {priority}\nDue Date: {due_date}\n\nDescription: {description}"
            ),
            "deadline_reminder": EmailTemplate(
                subject="Task Deadline Reminder",
                body="Reminder: The following task is due soon:\n\nTitle: {title}\nDue Date: {due_date}\nTime Remaining: {time_remaining}"
            ),
            "status_update": EmailTemplate(
                subject="Task Status Update",
                body="Task status has been updated:\n\nTitle: {title}\nNew Status: {status}\nUpdated at: {timestamp}"
            )
        }
    
    def send_email(self, 
                  to: str, 
                  subject: str, 
                  body: str, 
                  template_key: str = None, 
                  template_data: Dict[str, Any] = None) -> bool:
        """Send an email using Gmail API"""
        try:
            if template_key and template_data:
                template = self.templates[template_key]
                subject = template.subject
                body = template.body.format(**template_data)
            
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode('utf-8')
            
            self.gmail_service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    def send_task_assignment_email(self, task: 'Task', agent_email: str) -> bool:
        """Send task assignment notification email"""
        template_data = {
            "title": task.title,
            "priority": task.priority,
            "due_date": task.due_date.strftime("%Y-%m-%d %H:%M"),
            "description": task.description
        }
        
        return self.send_email(
            to=agent_email,
            subject="",  # Will be populated from template
            body="",     # Will be populated from template
            template_key="task_assignment",
            template_data=template_data
        )
    
    def send_deadline_reminder_email(self, task: 'Task', time_remaining: str) -> bool:
        """Send deadline reminder email"""
        template_data = {
            "title": task.title,
            "due_date": task.due_date.strftime("%Y-%m-%d %H:%M"),
            "time_remaining": time_remaining
        }
        
        return self.send_email(
            to=task.assigned_to,
            subject="",
            body="",
            template_key="deadline_reminder",
            template_data=template_data
        )
    
    def send_status_update_email(self, task: 'Task', new_status: str) -> bool:
        """Send status update email"""
        template_data = {
            "title": task.title,
            "status": new_status,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        return self.send_email(
            to=task.assigned_to,
            subject="",
            body="",
            template_key="status_update",
            template_data=template_data
        ) 