from typing import List, Dict, Any, Optional
import datetime
from scheduler_agency import SchedulerAgent, Task
from task_optimizer_agent import TaskOptimizerAgent
from notification_agent import NotificationAgent
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path
import pickle
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64
from datetime import datetime, timezone, timedelta
from calendar_checking_agent import CalendarCheckingAgent, TimeSlot
from email_response_agent import EmailResponseAgent

class GoogleAuthManager:
    def __init__(self):
        self.SCOPES = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/gmail.send'
        ]
        self.credentials_file = 'credentials.json'
        self.token_file = 'token.pickle'

    def get_credentials(self):
        """Get and refresh Google OAuth2 credentials."""
        credentials = None

        if not os.path.exists(self.credentials_file):
            raise FileNotFoundError(
                f"No credentials.json file found. Please:\n"
                f"1. Go to Google Cloud Console\n"
                f"2. Create a project and enable Calendar and Gmail APIs\n"
                f"3. Create OAuth 2.0 credentials\n"
                f"4. Download the credentials and save as {self.credentials_file}\n"
                f"Note: Never commit credentials.json to version control!"
            )

        # Load existing token if it exists
        if os.path.exists(self.token_file):
            try:
                with open(self.token_file, 'rb') as token:
                    credentials = pickle.load(token)
            except Exception as e:
                print(f"Error loading token: {e}")
                if os.path.exists(self.token_file):
                    os.remove(self.token_file)

        # If no valid credentials available, let the user log in
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                try:
                    credentials.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing credentials: {e}")
                    credentials = None
            
            if not credentials:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES)
                    credentials = flow.run_local_server(port=0)
                except Exception as e:
                    raise RuntimeError(f"Failed to authenticate: {e}")

            # Save the credentials for the next run
            try:
                with open(self.token_file, 'wb') as token:
                    pickle.dump(credentials, token)
            except Exception as e:
                print(f"Warning: Could not save token: {e}")

        return credentials

class SchedulerOrchestrator:
    def __init__(self):
        self.scheduler_agent = SchedulerAgent()
        self.task_optimizer = TaskOptimizerAgent()
        self.notification_agent = NotificationAgent()
        self.google_auth = GoogleAuthManager()
        self.calendar_checker = CalendarCheckingAgent(self.google_auth)
        self.email_agent = EmailResponseAgent(self.google_auth)
        
    def initialize_system(self, agents: List[str]) -> None:
        """Initialize the scheduling system with a list of agents"""
        self.scheduler_agent.agents = agents
    
    def create_task(self, 
                   title: str,
                   description: str,
                   priority: int,
                   due_date: datetime,
                   dependencies: List[str] = None) -> Optional[Task]:
        """Create a new task in the system"""
        # Ensure due_date is timezone-aware
        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=timezone.utc)
            
        task = Task(
            id=f"task_{len(self.scheduler_agent.tasks) + 1}",
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            status="pending",
            assigned_to="",
            dependencies=dependencies or []
        )
        
        if self.scheduler_agent.add_task(task):
            return task
        return None
    
    def assign_and_optimize_tasks(self) -> Dict[str, List[Task]]:
        """Assign tasks to agents and optimize the schedule"""
        # Get workload analysis
        all_tasks = list(self.scheduler_agent.tasks.values())
        workload_analysis = self.task_optimizer.analyze_workload(all_tasks)
        
        # Log the workload analysis
        print("Workload Analysis:", workload_analysis)
        
        # Get optimal task distribution
        task_distribution = self.task_optimizer.suggest_task_redistribution(
            all_tasks,
            self.scheduler_agent.agents
        )
        
        # Apply the assignments
        for agent, tasks in task_distribution.items():
            for task in tasks:
                self.scheduler_agent.assign_task(task.id, agent)
                self.notification_agent.send_task_assignment_notification(task, agent)
        
        # Optimize the schedule
        return self.scheduler_agent.optimize_schedule()
    
    def update_task_status(self, task_id: str, new_status: str) -> bool:
        """Update task status and send notifications"""
        if self.scheduler_agent.update_task_status(task_id, new_status):
            task = self.scheduler_agent.tasks[task_id]
            
            # Create system notification
            message = f"Task '{task.title}' status updated to: {new_status}"
            self.notification_agent.create_notification(
                notification_type="status_update",
                message=message,
                recipient=task.assigned_to
            )
            
            # Send email notification
            self.email_agent.send_status_update_email(task, new_status)
            
            return True
        return False
    
    def check_deadlines(self) -> None:
        """Check for approaching deadlines and send reminders"""
        for task in self.scheduler_agent.tasks.values():
            self.notification_agent.send_deadline_reminder(task)
    
    def get_agent_schedule(self, agent_id: str) -> Dict[str, Any]:
        """Get detailed schedule for an agent"""
        tasks = self.scheduler_agent.get_agent_schedule(agent_id)
        return {
            "agent_id": agent_id,
            "task_count": len(tasks),
            "tasks": tasks,
            "notifications": self.notification_agent.get_notification_history(agent_id)
        }
    
    def process_pending_notifications(self) -> None:
        """Process any pending notifications"""
        self.notification_agent.process_notifications() 
    
    def find_available_time_for_task(self, task: Task) -> Optional[TimeSlot]:
        """Find available time slot for a task"""
        # Ensure all datetime objects are timezone-aware
        now = datetime.now(timezone.utc)
        estimated_duration = timedelta(hours=2 * task.priority)
        
        # Find next available slot
        available_slot = self.calendar_checker.find_next_available_slot(
            duration=estimated_duration,
            start_from=now
        )
        
        if available_slot:
            # Format datetime strings properly for Google Calendar API
            start_time = available_slot.start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            end_time = available_slot.end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            event = {
                'summary': task.title,
                'description': task.description,
                'start': {
                    'dateTime': start_time,
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time,
                    'timeZone': 'UTC',
                }
            }
            
            # Update task with scheduled time
            task.scheduled_start = available_slot.start_time
            task.scheduled_end = available_slot.end_time
        
        return available_slot 