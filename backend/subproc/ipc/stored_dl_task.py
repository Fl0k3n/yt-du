from backend.model.dl_task import DlTask


class StoredDlTask:
    def __init__(self, task: DlTask, task_id: int):
        self.task = task
        self.task_id = task_id

    def __eq__(self, other) -> bool:
        if isinstance(other, StoredDlTask):
            return self.task_id == other.task_id
        return False

    def __hash__(self) -> int:
        return hash(self.task_id)
