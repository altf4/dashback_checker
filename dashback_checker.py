#!/usr/bin/python3
import argparse
from dataclasses import dataclass
import math
import melee
import os
import tqdm

DEADZONE = 22

parser = argparse.ArgumentParser(description="Example of libmelee in action")
parser.add_argument(
    "--file",
    "-f",
    default="./test_data/",
    help="Directory to SLP files to check",
)
args = parser.parse_args()


def processAnalogStick(x, y):
    magnitude = math.sqrt(x**2 + y**2)
    threshold = 80

    fx = x
    fy = y
    if magnitude > threshold:
        shrinkFactor = threshold / magnitude
        if fx > 0:
            fx = math.floor(fx * shrinkFactor)
            fy = math.floor(fy * shrinkFactor)
        else:
            fx = math.ceil(fx * shrinkFactor)
            fy = math.ceil(fy * shrinkFactor)

    # Deadzone
    if abs(fx) < 23:
        fx = 0
    if abs(fy) < 23:
        fy = 0

    fx = round(fx)
    fy = round(fy)
    return (fx / 80, fy / 80)


@dataclass
class DashBackData(object):
    raw_x = 0
    raw_y = 0
    action = melee.enums.Action.UNKNOWN_ANIMATION
    facing = True

    def __init__(self, x, y, action, facing):
        self.raw_x = x
        self.raw_y = y
        self.action = action
        self.facing = facing


successful_dashbacks = 0
failed_dashbacks = []
for file in tqdm.tqdm(os.listdir(args.file)):
    try:
        console = melee.Console(
            system="file", allow_old_version=False, path=args.file + "/" + file
        )
        console.connect()

        frames = dict()

        # Build the DashBackData lists
        while True:
            gamestate = console.step()
            # step() returns None when the file ends
            if gamestate is None:
                break

            for port, player in gamestate.players.items():
                if port not in frames:
                    frames[port] = []

                frames[port].append(
                    DashBackData(
                        player.controller_state.raw_main_stick[0],
                        player.controller_state.raw_main_stick[1],
                        player.action,
                        player.facing,
                    )
                )

        # To do a UCF dash back, you need to (over two frames, starting from standing):
        # A) move at least 76 raw units
        # B) pass the +-64 raw unit barrier
        # C) move >0.9375 total processed x units
        # D) move past the +/- 0.8 processed barrier
        for player in frames:
            for frame_index, item in enumerate(frames[player]):
                # Start from standing. Do we dash backwards?
                if item.action == melee.Action.STANDING:
                    # look into the future two frames.
                    #   have we met the dashback conditions?
                    if len(frames[player]) > frame_index + 3:
                        raw_distance_traveled = abs(
                            frames[player][frame_index + 2].raw_x - item.raw_x
                        )
                        processed_x, processed_y = processAnalogStick(
                            item.raw_x, item.raw_y
                        )
                        processed_x_future, processed_y_future = processAnalogStick(
                            frames[player][frame_index + 2].raw_x,
                            frames[player][frame_index + 2].raw_y,
                        )
                        processed_distance_traveled = abs(
                            processed_x_future - processed_x
                        )

                        if (
                            raw_distance_traveled > 75
                            and abs(frames[player][frame_index + 2].raw_x) > 64
                            and processed_distance_traveled > 0.9375
                            and abs(processed_x_future) > 0.8
                        ):
                            # There's an exception here. If we have exited the deadzone in frame i+1, then we only care about
                            #   frame i+2 if it's moving in the SAME direction.
                            #   ie: If you do a slow turn in one direction and then fast turn in the other, you won't get a dashback
                            if abs(frames[player][frame_index + 1].raw_x) > DEADZONE:
                                if (frames[player][frame_index + 1].raw_x > 0) != (
                                    frames[player][frame_index + 2].raw_x > 0
                                ):
                                    break

                            # If we're here, then we have input a dash input
                            # BUT. We might not still get a dash. We could get hit, jump, fall off a platform, etc...
                            # So let's check the action state to see what happened in the game
                            # It's a failure only if we get:
                            #   A) Multiple consecutive frames of turning (ie: slow turn)
                            #   B) Slow walk on frame i+2
                            if (
                                frames[player][frame_index + 2].action
                                == melee.Action.WALK_SLOW
                            ):
                                failed_dashbacks.append([file, frame_index])
                                print(file, "Failure B", "port", player)
                                for i in range(20):
                                    print(
                                        frame_index + i,
                                        frames[player][frame_index + i].raw_x,
                                        frames[player][frame_index + i].raw_y,
                                        frames[player][frame_index + i].action,
                                        processAnalogStick(
                                            frames[player][frame_index + i].raw_x,
                                            frames[player][frame_index + i].raw_y,
                                        ),
                                    )

                            # If we get two consecutive turning frames in a row, that's an error
                            if (
                                frames[player][frame_index + 2].action
                                == melee.Action.TURNING
                                and frames[player][frame_index + 3].action
                                == melee.Action.TURNING
                                and frames[player][frame_index + 3].action
                            ):
                                # Exception: If we let go of the dash, it'll give us a pivot-turn (empty pivot)
                                # So ignore any double-turn instances where this happens
                                future_x, _ = processAnalogStick(
                                    frames[player][frame_index + 3].raw_x,
                                    frames[player][frame_index + 3].raw_y,
                                )
                                if future_x < 0.801:
                                    break
                                failed_dashbacks.append([file, frame_index])
                                print(file, "Failure A", "port", player)
                                for i in range(4):
                                    print(
                                        frame_index + i,
                                        frames[player][frame_index + i].raw_x,
                                        frames[player][frame_index + i].raw_y,
                                        frames[player][frame_index + i].action,
                                        processAnalogStick(
                                            frames[player][frame_index + i].raw_x,
                                            frames[player][frame_index + i].raw_y,
                                        ),
                                    )

                            # # Two consecutive frames of turning
                            # consecutive_turn_frames = 0
                            # for i in range(4):
                            #     if (
                            #         frames[player][frame_index + i].action
                            #         == melee.Action.TURNING
                            #     ):
                            #         consecutive_turn_frames += 1

                            # if consecutive_turn_frames > 1:
                            #     failed_dashbacks.append([file, frame_index])
                            #     print(file, "Failure A", "port", player)
                            #     for i in range(4):
                            #         print(
                            #             frame_index + i,
                            #             frames[player][frame_index + i].raw_x,
                            #             frames[player][frame_index + i].raw_y,
                            #             frames[player][frame_index + i].action,
                            #             processAnalogStick(
                            #                 frames[player][frame_index + i].raw_x,
                            #                 frames[player][frame_index + i].raw_y,
                            #             ),
                            #         )
                            if (
                                frames[player][frame_index + 1].action
                                == melee.Action.DASHING
                                or frames[player][frame_index + 2].action
                                == melee.Action.DASHING
                            ):
                                successful_dashbacks += 1
    except Exception as ex:
        print("Error with file:", file, ex)

print("Successful dashbacks:", successful_dashbacks)
print("Failed dashbacks: ", len(failed_dashbacks))
for failure in failed_dashbacks:
    print(failure)