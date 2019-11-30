import datetime
from threading import Thread
from time import sleep
from typing import Optional


class Scheduler(Thread):

    def __init__(self, target, args: tuple, second=5, daemon: Optional[bool] = ...) -> None:

        super().__init__(daemon=daemon)
        self.args = args
        self.target = target
        self.second = second
        self._init_update()

    def _init_update(self) -> None:
        self.update_time = datetime.datetime.today() + datetime.timedelta(seconds=self.second)

    def run(self) -> None:
        while True:
            time_to_sleep = (self.update_time - datetime.datetime.today()).seconds
            while time_to_sleep > 0:
                sleep(time_to_sleep)
                time_to_sleep = (self.update_time - datetime.datetime.today()).seconds
            Thread(target=self.target, args=self.args).run()
            sleep(1)  # Is used to prevent target to run several times during update_time == today()
            self._init_update()
