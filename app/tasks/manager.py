"""Background Tasks Manager"""
import asyncio
from typing import List
import logging

logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.tasks: List[asyncio.Task] = []
        
    async def start(self):
        """Start task manager"""
        logger.info(f"Task manager started with {self.max_workers} workers")
        
    async def stop(self):
        """Stop task manager"""
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        logger.info("Task manager stopped")
    
    def create_task(self, coro):
        """Create a new task"""
        task = asyncio.create_task(coro)
        self.tasks.append(task)
        return task
