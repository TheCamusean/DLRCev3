import cv2
from ev3control.rpc import Robot
from rick.controllers import move_to_brick_simple, \
    move_to_brick_blind_and_grip, rotation_search_brick, rotation_search_box, move_to_box_simple
from rick.core import State
from rick.core import main_loop
from rick.async import AsyncCamera


print("Creating robot...")

with Robot(AsyncCamera(1)) as robot:
    robot.map = [(100, 100)]
    print("These are the robot motor positions before planning:", robot.left_track.position, robot.right_track.position)
    # Define the state graph, we can do this better, currently each method
    # returns the next state name
    states = [
        State(
            name="SEARCH",
            act=rotation_search_brick,
            default_args={}),
        State(
            name="MOVE_TO_BRICK",
            act=move_to_brick_simple,
            default_args={}
        ),
        State(
            name="MOVE_TO_BRICK_BLIND_AND_GRIP",
            act=move_to_brick_blind_and_grip,
            default_args={}
        ),
        State(

        )
    ]
    print(states[0])
    state_dict = {}
    for state in states:
        state_dict[state.name] = state

    start_state = states[0]

    main_loop(robot, start_state, state_dict, delay=0.03)
