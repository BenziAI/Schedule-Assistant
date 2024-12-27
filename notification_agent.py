from typing import List, Dict, Any
import datetime
from dataclasses import dataclass
from scheduler_agency import Task

class NotificationAgent:
    def __init__(self):
        self.notification_queue: List[Dict[str, Any]] = []
        self.notification_history: List[Dict[str, Any]] = []
        self.notification_settings = {
            "task_assignment": True,
            "status_update": True,
            "deadline_reminder": True,
            "priority_change": True
        }
    
    def create_notification(self, 
                          notification_type: str,
                          message: str,
                          recipient: str,
                          priority: str = "normal",
                          related_task: Task = None) -> Dict[str, Any]:
        """Create a new notification"""
        notification = {
            "id": f"notif_{len(self.notification_history) + 1}",
            "type": notification_type,
            "message": message,
            "recipient": recipient,
            "priority": priority,
            "timestamp": datetime.datetime.now(),
            "related_task": related_task.id if related_task else None,
            "status": "pending"
        }
        self.notification_queue.append(notification)
        return notification
    
    def send_task_assignment_notification(self, task: Task, agent: str) -> None:
        """Send notification for new task assignment"""
        if not self.notification_settings["task_assignment"]:
            return
            
        message = f"New task assigned: {task.title}\nPriority: {task.priority}\nDue: {task.due_date}"
        self.create_notification(
            notification_type="task_assignment",
            message=message,
            recipient=agent,
            priority="high" if task.priority > 2 else "normal",
            related_task=task
        )
    
    def send_deadline_reminder(self, task: Task) -> None:
        """Send deadline reminder notification"""
        if not self.notification_settings["deadline_reminder"]:
            return
            
        current_time = datetime.datetime.now(datetime.timezone.utc)
        if task.due_date.tzinfo is None:
            task_due = task.due_date.replace(tzinfo=datetime.timezone.utc)
        else:
            task_due = task.due_date
            
        time_until_due = task_due - current_time
        if time_until_due.days <= 2:  # 2 days threshold
            message = f"Deadline approaching for task: {task.title}\nDue in {time_until_due.days} days"
            self.create_notification(
                notification_type="deadline_reminder",
                message=message,
                recipient=task.assigned_to,
                priority="high",
                related_task=task
            )
    
    def process_notifications(self) -> List[Dict[str, Any]]:
        """Process and send pending notifications"""
        processed = []
        while self.notification_queue:
            notification = self.notification_queue.pop(0)
            # Here you would implement actual notification sending logic
            # (e.g., email, SMS, system notification)
            notification["status"] = "sent"
            self.notification_history.append(notification)
            processed.append(notification)
        return processed
    
    def get_notification_history(self, recipient: str = None) -> List[Dict[str, Any]]:
        """Get notification history, optionally filtered by recipient"""
        if recipient:
            return [n for n in self.notification_history if n["recipient"] == recipient]
        return self.notification_history 