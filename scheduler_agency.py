from typing import List, Dict, Any, Optional
import datetime
from dataclasses import dataclass
import json

@dataclass
class Task:
    id: str
    title: str
    description: str
    priority: int
    due_date: datetime.datetime
    status: str
    assigned_to: str
    dependencies: List[str]
    scheduled_start: Optional[datetime.datetime] = None
    scheduled_end: Optional[datetime.datetime] = None
    calendar_event_id: Optional[str] = None

class SchedulerAgent:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.agents: List[str] = []
        self.current_schedule: Dict[str, List[Task]] = {}
    
    def add_task(self, task: Task) -> bool:
        """Add a new task to the system"""
        if task.id in self.tasks:
            return False
        self.tasks[task.id] = task
        return True
    
    def assign_task(self, task_id: str, agent_id: str) -> bool:
        """Assign a task to a specific agent"""
        if task_id not in self.tasks or agent_id not in self.agents:
            return False
        self.tasks[task_id].assigned_to = agent_id
        return True
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """Update the status of a task"""
        if task_id not in self.tasks:
            return False
        self.tasks[task_id].status = status
        return True
    
    def optimize_schedule(self) -> Dict[str, List[Task]]:
        """Optimize the schedule based on priorities and dependencies"""
        # Implementation of scheduling algorithm
        schedule = {}
        for agent in self.agents:
            agent_tasks = [task for task in self.tasks.values() if task.assigned_to == agent]
            # Sort by priority and due date
            agent_tasks.sort(key=lambda x: (x.priority, x.due_date))
            schedule[agent] = agent_tasks
        self.current_schedule = schedule
        return schedule
    
    def get_agent_schedule(self, agent_id: str) -> List[Task]:
        """Get the schedule for a specific agent"""
        return self.current_schedule.get(agent_id, []) 