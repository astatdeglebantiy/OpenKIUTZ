class LessonItem:
    def __init__(self, number: int, time_slot: str, name: str, lecturer: str, room: str, link: str, meet: str):
        self.number: int = number
        self.time_slot: str = time_slot
        self.name: str = name
        self.lecturer: str = lecturer
        self.room: str = room
        self.link: str = link
        self.meet: str = meet

    @property
    def is_empty(self) -> bool:
        return not self.name
