from abc import ABC, abstractmethod
from backend.view.data_summary_box import DataSummaryBox


class DataViewChanger(ABC):
    @abstractmethod
    def change_data_view(self, new_view: DataSummaryBox):
        pass

    @abstractmethod
    def change_back(self):
        pass

    @abstractmethod
    def change_forward(self):
        pass

    @abstractmethod
    def view_deleted(self, view: DataSummaryBox):
        pass
