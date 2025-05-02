from __future__ import annotations

import random
import time
from typing import Any, Callable, Dict, List

from colorama import Fore, Style


class Task:
    def __init__(self, task_id: int, dependencies: List[Task], extra_info: Any = None):
        self.task_id = task_id
        self.extra_info = extra_info
        self.dependencies = dependencies
        self.status = 0


class TaskManager:
    def __init__(self):
        self.task_dict: Dict[int, Task] = {}
        self.now_id = 0
        self.query_id = 0

    @property
    def all_success(self) -> bool:
        return len(self.task_dict) == 0

    def add_task(self, dependency_task_id: List[int], extra=None) -> int:
        depend_tasks = [self.task_dict[task_id] for task_id in dependency_task_id]
        self.task_dict[self.now_id] = Task(
            task_id=self.now_id, dependencies=depend_tasks, extra_info=extra
        )
        self.now_id += 1
        return self.now_id - 1

    def get_next_task(self):
        self.query_id += 1
        for task_id in self.task_dict.keys():
            ready = (
                len(self.task_dict[task_id].dependencies) == 0
            ) and self.task_dict[task_id].status == 0
            if ready:
                self.task_dict[task_id].status = 1
                print(
                    f"{Fore.RED}[process]{Style.RESET_ALL}: get task({task_id}), remain({len(self.task_dict)})"
                )
                return self.task_dict[task_id], task_id
        return None, -1

    def mark_completed(self, task_id: int):
        target_task = self.task_dict[task_id]
        for task in self.task_dict.values():
            if target_task in task.dependencies:
                task.dependencies.remove(target_task)
        self.task_dict.pop(task_id)


def worker(task_manager, handler: Callable):
    while True:
        if task_manager.all_success:
            return
        task, task_id = task_manager.get_next_task()
        if task is None:
            time.sleep(0.5)
            continue
        handler(task.extra_info)
        task_manager.mark_completed(task.task_id)


if __name__ == "__main__":
    task_manager = TaskManager()

    def some_function():
        time.sleep(random.random() * 3)

    i1 = task_manager.add_task(some_function, [])  # type: ignore
    i2 = task_manager.add_task(some_function, [])  # type: ignore
    i3 = task_manager.add_task(some_function, [i1])  # type: ignore
    i4 = task_manager.add_task(some_function, [i2, i3])  # type: ignore
    i5 = task_manager.add_task(some_function, [i2, i3])  # type: ignore
    i6 = task_manager.add_task(some_function, [i1])  # type: ignore

    worker(task_manager, some_function)