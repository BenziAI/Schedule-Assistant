from typing import List, Dict, Any
import datetime
from dataclasses import dataclass
from scheduler_agency import Task

class TaskOptimizerAgent:
    def __init__(self):
        self.workload_threshold = 8  # hours per day
        self.priority_weights = {
            "high": 3,
            "medium": 2,
            "low": 1
        }
    
    def analyze_workload(self, tasks: List[Task]) -> Dict[str, Any]:
        """Analyze the workload distribution and identify potential bottlenecks"""
        workload_analysis = {
            "total_tasks": len(tasks),
            "priority_distribution": {},
            "overloaded_days": [],
            "recommendations": []
        }
        
        # Analyze priority distribution
        for task in tasks:
            priority = str(task.priority)
            workload_analysis["priority_distribution"][priority] = \
                workload_analysis["priority_distribution"].get(priority, 0) + 1
        
        return workload_analysis
    
    def optimize_task_sequence(self, tasks: List[Task]) -> List[Task]:
        """Optimize the sequence of tasks based on dependencies and priorities"""
        # Sort tasks by priority and dependencies
        dependency_graph = self._build_dependency_graph(tasks)
        sorted_tasks = self._topological_sort(dependency_graph)
        return sorted_tasks
    
    def _build_dependency_graph(self, tasks: List[Task]) -> Dict[str, List[str]]:
        """Build a graph of task dependencies"""
        graph = {}
        for task in tasks:
            graph[task.id] = task.dependencies
        return graph
    
    def _topological_sort(self, graph: Dict[str, List[str]]) -> List[str]:
        """Perform topological sort on tasks based on dependencies"""
        visited = set()
        temp = set()
        order = []
        
        def visit(task_id: str):
            if task_id in temp:
                raise ValueError("Circular dependency detected")
            if task_id in visited:
                return
            
            temp.add(task_id)
            for dep in graph.get(task_id, []):
                visit(dep)
            temp.remove(task_id)
            visited.add(task_id)
            order.append(task_id)
        
        for task_id in graph:
            if task_id not in visited:
                visit(task_id)
                
        return order[::-1]
    
    def suggest_task_redistribution(self, tasks: List[Task], agents: List[str]) -> Dict[str, List[Task]]:
        """Suggest optimal task redistribution among agents"""
        workload = {agent: [] for agent in agents}
        sorted_tasks = sorted(tasks, key=lambda x: x.priority, reverse=True)
        
        # Simple round-robin distribution weighted by priority
        for task in sorted_tasks:
            # Find agent with minimum current workload
            min_agent = min(workload.items(), key=lambda x: sum(t.priority for t in x[1]))[0]
            workload[min_agent].append(task)
        
        return workload 