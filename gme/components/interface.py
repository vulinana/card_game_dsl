from abc import abstractmethod, ABC


class Interface(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def initiate(self) -> None:
        pass

