import json
import serial
import time
import pickle
import os
import ast
import itertools
import random
import RPi.GPIO as GPIO


from http.server import BaseHTTPRequestHandler, HTTPServer
from utils.pathing import Graph
from utils.ultrasonic import Rangefinder

DEBUG_MODE = 1

MOVEMENT_ITERATIONS = 5
MINIMAL_DISTANCE = 15
RANGEFINDER_DELTA = 1.5
TURNING_DELTA = 0.01
GPIO.setmode(GPIO.BCM)

TRIGGER_PINS = [18, 17, 12, 16, 20]
ECHO_PINS = [24, 27, 13, 19, 26]
RANGE_NAMES = ["left_60", "left_30", "fwd", "rgt_30", "rgt_60"]


class RobotState:
    def __init__(self):
        self.direction = "N"
        self.position = None
        self.move_time = 0.0
        self.turn_time = 0.0

    def change_dir_lft(self):
        if self.direction == "N":
            self.direction = "W"
        elif self.direction == "W":
            self.direction = "S"
        elif self.direction == "S":
            self.direction = "E"
        elif self.direction == "E":
            self.direction = "N"

    def change_dir_rgt(self):
        if self.direction == "N":
            self.direction = "E"
        elif self.direction == "E":
            self.direction = "S"
        elif self.direction == "S":
            self.direction = "W"
        elif self.direction == "W":
            self.direction = "N"

    def calibrate(self, conn, rangefinders):
        start = rangefinders["fwd"].get_distance()
        print(start)
        self.prepare(conn)
        # Moving forward
        send_cmd(conn, b"FWD\n")
        time.sleep(2)
        send_cmd(conn, b"STP\n")
        finish = rangefinders["fwd"].get_distance()
        print(finish)
        self.move_fwd_time = round(20.0 / abs(finish - start), 4)
        print(self.move_fwd_time)
        # Returning back
        send_cmd(conn, b"BCK\n")
        time.sleep(2)
        send_cmd(conn, b"STP\n")
        time.sleep(2)

        start = rangefinders["fwd"].get_distance()
        distance = 0.0
        # Turning right
        start_time = time.time()
        send_cmd(conn, b"RGT\n")
        time.sleep(1)
        while distance > (start + RANGEFINDER_DELTA) or distance < (
            start - RANGEFINDER_DELTA
        ):
            distance = rangefinders["fwd"].get_distance()
            time.sleep(0.01)
        stop_time = time.time()
        # Divide the time of 360 turn by 12 to get 30 turn
        self.turn_rgt_time = round((stop_time - start_time) / 12, 4)
        send_cmd(conn, b"STP\n")

        time.sleep(2)

        start = rangefinders["fwd"].get_distance()
        distance = 0.0
        # Turning left
        start_time = time.time()
        send_cmd(conn, b"LFT\n")
        time.sleep(1)
        while distance > (start + RANGEFINDER_DELTA) or distance < (
            start - RANGEFINDER_DELTA
        ):
            distance = rangefinders["fwd"].get_distance()
            time.sleep(0.01)
        stop_time = time.time()
        # Divide the time of 360 turn by 12 to get 30 turn
        self.turn_lft_time = round((stop_time - start_time) / 12, 4)
        send_cmd(conn, b"STP\n")
        return

    def prepare(self, conn):
        time.sleep(1)
        send_cmd(conn, b"FWD\n")
        time.sleep(0.1)
        send_cmd(conn, b"BCK\n")
        time.sleep(0.1)
        send_cmd(conn, b"STP\n")

    def print_state(self):
        print(
            {
                "Direction": self.direction,
                "Position": self.position,
                "Move Forward Time": self.move_fwd_time,
                "Turn Right Time": self.turn_rgt_time,
                "Turn Left Time": self.turn_lft_time,
            }
        )


def float_range(start, end, step):
    while start <= end:
        yield start
        start += step


def send_cmd(conn, cmd: str):
    conn.write(cmd)
    return


html = """<html>
              <style>html{font-family: Helvetica; display:inline-block; margin: 0px auto; text-align: center;}
                 .button_led {display: inline-block; background-color: #e7bd3b; border: none; border-radius: 4px; color: white; padding: 16px 40px; text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}
              </style>
              <script type="text/javascript" charset="utf-8">
                    function httpPostAsync(method, params, callback) {
                        var xmlHttp = new XMLHttpRequest();
                        xmlHttp.onreadystatechange = function() { 
                            if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
                                callback(xmlHttp.responseText);
                            else
                                callback(`In progress`)
                        }
                        xmlHttp.open("POST", window.location.href + method, true);
                        xmlHttp.setRequestHeader("Content-Type", "application/json");
                        xmlHttp.send(params);
                    }

                    function Calibrate() {
                        document.getElementById("textstatus").textContent = "Calibrating...";
                        httpPostAsync("cal", JSON.stringify({}), function(resp) { 
                            document.getElementById("textstatus").textContent = `Calibrate: ${resp}`;
                        });
                    }

                    function MoveRandom() {
                        document.getElementById("textstatus").textContent = "Moving...";
                        httpPostAsync("move", JSON.stringify({}), function(resp) { 
                            document.getElementById("textstatus").textContent = `Movement: ${resp}`;
                        });
                    }                            
              </script>
              <body>
                 <h2>Hello from the Robot!</h2>
                 <p><button class="button button_led" onclick="Calibrate();">Calibrate</button></p>
                 <p><button class="button button_led" onclick="MoveRandom();">Random Move</button></p>
                 <span id="textstatus">Status: Waiting</span>
              </body>
            </html>"""

conn = serial.Serial("/dev/ttyACM0", 9600, timeout=1)
conn.flush()
robot = RobotState()
time.sleep(1)
# Establishing connection

rangefinders = {}
for trigger, echo, name in zip(TRIGGER_PINS, ECHO_PINS, RANGE_NAMES):
    rangefinders[name] = Rangefinder(trigger, echo)

robot.move_fwd_time = 0.448
robot.turn_rgt_time = 0.3293
robot.turn_lft_time = 0.4621
robot.direction = "S"

obst = []
graph = Graph(12, 15, obst)
graph_nodes = list(
    itertools.chain.from_iterable([[node for node in row] for row in graph.nodes])
)
robot.position = graph.get_node_by_id(16)


class ServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print("GET request, path:", self.path)
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_error(404, "Page Not Found {}".format(self.path))

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        body = self.rfile.read(content_length)
        try:
            print("POST request, path:", self.path, "body:", body.decode("utf-8"))
            if self.path == "/cal":
                print("Recieved Calibrate")
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                robot.calibrate(conn, rangefinders)
                self.wfile.write(b"Finished")
            elif self.path == "/move":
                print("Recieved Move Command")
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                destination = random.choice(graph_nodes)
                while destination.id == -1:
                    destination = random.choice(graph_nodes)
                path = graph.build_path(robot.position, destination)
                cmd_list = graph.create_command_sequence(path, initial_direction="S")
                robot_is_at_finish = False
                robot.prepare(conn)
                while not robot_is_at_finish:
                    print("Starting new route")
                    for cmd in cmd_list:
                        if cmd == "fwd":
                            if (
                                rangefinders["fwd"].get_distance() <= MINIMAL_DISTANCE
                                or rangefinders["left_30"].get_distance()
                                <= MINIMAL_DISTANCE
                                or rangefinders["rgt_30"].get_distance()
                                <= MINIMAL_DISTANCE
                            ) and path[1] in graph_nodes:
                                send_cmd(conn, b"STP\n")
                                print(graph.mark_as_obstacle(path[1], robot.direction))
                                path = graph.build_path(robot.position, destination)
                                cmd_list = graph.create_command_sequence(
                                    path, robot.direction
                                )
                                print("Found obstacle")
                                break
                            send_cmd(conn, b"FWD\n")
                            for i in float_range(
                                0,
                                robot.move_fwd_time,
                                robot.move_fwd_time / MOVEMENT_ITERATIONS,
                            ):
                                if (
                                    rangefinders["left_60"].get_distance()
                                    <= MINIMAL_DISTANCE / 2
                                ):
                                    send_cmd(conn, b"RGT\n")
                                    time.sleep(robot.turn_rgt_time / 2)
                                    send_cmd(conn, b"FWD\n")
                                if (
                                    rangefinders["rgt_60"].get_distance()
                                    <= MINIMAL_DISTANCE / 2
                                ):
                                    send_cmd(conn, b"LFT\n")
                                    time.sleep(robot.turn_lft_time / 2)
                                    send_cmd(conn, b"FWD\n")
                                time.sleep(robot.move_fwd_time / MOVEMENT_ITERATIONS)
                            path.remove(robot.position)
                            robot.position = path[0]
                            send_cmd(conn, b"STP\n")
                        elif cmd == "rgt":
                            send_cmd(conn, b"RGT\n")
                            time.sleep(3 * robot.turn_rgt_time)
                            robot.change_dir_rgt()
                            send_cmd(conn, b"STP\n")
                        elif cmd == "lft":
                            send_cmd(conn, b"LFT\n")
                            time.sleep(3 * robot.turn_lft_time)
                            robot.change_dir_lft()
                            send_cmd(conn, b"STP\n")

                        print([node.id for node in path], len(path))
                    send_cmd(conn, b"STP\n")
                    if len(path) < 2:
                        robot_is_at_finish = True
                self.wfile.write(b"Finished")

            else:
                self.send_response(400, "Bad Request: Method does not exist")
                self.send_header("Content-Type", "application/json")
                self.end_headers()
        except Exception as err:
            print("do_POST exception: %s" % str(err))


def server_thread(port):
    server_address = ("", port)
    httpd = HTTPServer(server_address, ServerHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()


if __name__ == "__main__":

    port = 8000
    print("Starting server at port %d" % port)

    server_thread(port)
    GPIO.cleanup()
