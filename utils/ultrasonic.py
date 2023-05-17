#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time

# GPIO Mode (BOARD / BCM)
GPIO.setmode(GPIO.BCM)

TRIGGER_PINS = [18, 17, 12, 16, 20]
ECHO_PINS = [24, 27, 13, 19, 26]
RANGE_NAMES = ["left_60", "left_30", "fwd", "rgt_30", "rgt_60"]


class Rangefinder:
    def __init__(self, trigger: int, echo: int):
        self.trigger = trigger
        self.echo = echo
        GPIO.setup(self.trigger, GPIO.OUT)
        GPIO.setup(self.echo, GPIO.IN)

    def get_distance(self) -> float:
        # set Trigger to HIGH
        GPIO.output(self.trigger, True)

        # set Trigger after 0.01ms to LOW
        time.sleep(0.00001)
        GPIO.output(self.trigger, False)

        start_time = time.time()
        stop_time = time.time()

        # save start_time
        while GPIO.input(self.echo) == 0:
            start_time = time.time()

        # save time of arrival
        while GPIO.input(self.echo) == 1:
            stop_time = time.time()

        # time difference between start and arrival
        TimeElapsed = stop_time - start_time
        # multiply with the sonic speed (34300 cm/s)
        # and divide by 2, because there and back
        distance = (TimeElapsed * 34300) / 2

        return distance


# set GPIO Pins
# GPIO_TRIGGER = 18
# GPIO_ECHO = 24

# set GPIO direction (IN / OUT)
# GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
# GPIO.setup(GPIO_ECHO, GPIO.IN)

if __name__ == "__main__":
    try:
        rangefinders = {}
        for trigger, echo, name in zip(TRIGGER_PINS, ECHO_PINS, RANGE_NAMES):
            rangefinders[name] = Rangefinder(trigger, echo)
        while True:
            start = time.time()
            dist = [
                (key, round(rangefinder.get_distance(), 3))
                for key, rangefinder in rangefinders.items()
            ]
            print(f"Measured Distances: {dist}")
            print(round(time.time() - start, 4))
            time.sleep(3)

        # Reset by pressing CTRL + C
    except KeyboardInterrupt:
        print("Measurement stopped by User")
        GPIO.cleanup()
