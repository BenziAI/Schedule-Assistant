from datetime import datetime, timezone, timedelta
from scheduler_orchestrator import SchedulerOrchestrator

def create_and_verify_task(orchestrator: SchedulerOrchestrator):
    """Create a task and verify its creation"""
    task = orchestrator.create_task(
        title="High Priority Task",
        description="Important task that needs immediate attention",
        priority=1,
        due_date=datetime.now(timezone.utc) + timedelta(days=1),
        dependencies=[]
    )
    
    if task:
        print(f"\nTask created: {task.title}")
        print(f"Task ID: {task.id}")
        print(f"Initial Status: {task.status}")
        return task
    print("\nFailed to create task")
    return None

def display_schedule(schedule):
    """Display the optimized schedule"""
    print("\nOptimized Schedule:")
    for agent, tasks in schedule.items():
        print(f"\nAgent: {agent}")
        for task in tasks:
            print(f"  - {task.title} (Priority: {task.priority}, Due: {task.due_date})")

def process_available_slot(orchestrator: SchedulerOrchestrator, task, available_slot):
    """Process and display available time slot information"""
    if not available_slot:
        print("\nNo available time slot found")
        return False
        
    print(f"\nTask scheduled for:")
    print(f"Start: {available_slot.start_time}")
    print(f"End: {available_slot.end_time}")
    return True

def display_agent_schedule(agent_schedule):
    """Display agent schedule details"""
    print("\nAgent 1 Schedule Details:")
    print(f"Task Count: {agent_schedule['task_count']}")
    print("Tasks:")
    for task in agent_schedule['tasks']:
        print(f"  - {task.title} (Status: {task.status})")
    print("Recent Notifications:")
    for notification in agent_schedule['notifications']:
        print(f"  - {notification['message']}")

def main():
    # Initialize the orchestrator and system
    orchestrator = SchedulerOrchestrator()
    orchestrator.initialize_system(["agent_1", "agent_2", "agent_3"])
    
    # Create and verify task
    task = create_and_verify_task(orchestrator)
    if not task:
        return
    
    # Test task assignment and optimization
    schedule = orchestrator.assign_and_optimize_tasks()
    display_schedule(schedule)
    
    # Test calendar scheduling
    available_slot = orchestrator.find_available_time_for_task(task)
    if process_available_slot(orchestrator, task, available_slot):
        # Test notifications and updates
        orchestrator.email_agent.send_task_assignment_email(task, "joeblackabcd1234@gmail.com")
        orchestrator.update_task_status(task.id, "in_progress")
        print(f"\nNew Status: {task.status}")
        
        # Process notifications
        orchestrator.check_deadlines()
        print("\nProcessing notifications...")
        orchestrator.process_pending_notifications()
        
        # Display agent schedule
        agent_schedule = orchestrator.get_agent_schedule("agent_1")
        display_agent_schedule(agent_schedule)

if __name__ == "__main__":
    main()