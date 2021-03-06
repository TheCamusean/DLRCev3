## PLACING WITH KALMAN




import time
import cv2
from ev3control.rpc import Robot
from rick.controllers import *
from rick.A_star_planning import *
from rick.core import State
from rick.core import main_loop
from rick.async import AsyncCamera
from rick.utils import TrackerWrapper
#from nn_object_detection.object_detectors import NNObjectDetector
from rick.live_plotting import MapRenderer

from detection.marker_localization import get_marker_pose, load_camera_params
import cv2.aruco as aruco


from detection.marker_localization import get_specific_marker_pose, load_camera_params
import numpy as np
from rick.mc_please_github_donot_fuck_with_this_ones import A_star_path_planning_control,compute_A_star_path, A_star_control
from math import pi


from detection.opencv import get_lego_boxes



from rick.motion_control import euclidian_kalman , kalman_filter , kalman_filter2 , robot_control, odom_estimation

import sys

sys.path.append("../slam/")

import mapping

import matplotlib.pyplot as plt

from detection.opencv import detect_purple

PATH_TO_CKPT = "/home/dlrc/projects/DLRCev3/object_detection/nn_object_detection/tf_train_dir/models/faster_rcnn_resnet_lego_v1/train/frozen_inference_graph.pb"
PATH_TO_LABELS = "/home/dlrc/projects/DLRCev3/object_detection/nn_object_detection/tf_train_dir/data/label_map.pbtxt"


print("Creating robot...")


data = np.load('Homographygood.npz')
H=data["arr_0"]

map_renderer = MapRenderer()


def plot_mapa(mapa,robot_traj):


    mapa1 = np.array(mapa)
    rob = np.array(robot_traj)
    print("Before stop")
    if mapa1.size:
        print("In")
        plt.scatter(mapa1[:,0],mapa1[:,1])
        print("Out")
    if rob.size > 100:
        plt.plot(rob[:,0],rob[:,1])
        plt.axis([-100, 150, -100, 150])
        plt.legend(["Lego", "path"])
        plt.show(block=False)
    print("After stop")


def search_control(state_search,mapa, pos_rob, t_old):

    t1 = 0
    if state_search ==1:

        target = [0.1,0.1]# THE POINT REPRESENTS THE MIDDLE OF THE WORKSPACE
        vel_wheels = robot_control(pos_rob,target, K_x=1,K_y=1,K_an=1)

        distance = np.sqrt(np.power(pos_rob[0]-target[0],2) + np.power(pos_rob[1]-target[1],2))

        if distance < 10:
            state_search = 2
            t1 = time.time()
    
    elif state_search ==2:

        vel_wheels = [-100,100]

    return vel_wheels,state_search,t1

def index23(BB_legos,BB_target):
    index=1000
    i=0
    for box in BB_legos:
        if box[0]==BB_target[0][0] and box[1] == BB_target[0][1]:

            index = i
        i+=1
    return index



def search_box(robot, frame, ltrack_pos=0, rtrack_pos=0, P=np.identity(3), marker_list = [], delete_countdown = 0 , mapa = [], robot_trajectory = [],R=[],state_search = 2 , t1=0):


    mtx,dist=load_camera_params()
    frame,box_coords = get_specific_marker_pose(frame=frame,mtx=mtx,dist=dist,marker_id=0)
    if box_coords:
        #robot.left_track.stop(stop_action="brake")
        #robot.right_track.stop(stop_action="brake")
        print("BOX_COORDINATES:",box_coords[0],box_coords[1],box_coords[2])
        return ("COMPUTE_PATH", frame, {
                        "box_coords": box_coords
                    })
    else:
        robot.rotate(100)
        return "SEARCH_TARGET", frame, {}


def compute_path(robot,frame,box_coords, ltrack_pos = 0, rtrack_pos = 0, mapa = [], R = []):
    x=box_coords[0]
    y=box_coords[1]
    yaw=box_coords[2]
    if (y>0 and yaw>-80) or (y<0 and yaw< -100):
        print("NICE PATH")
    thm=40
    thobj=50


    x2=x+thm*np.sin(yaw*np.pi/180.)
    y2=y-thm*np.cos(yaw*np.pi/180.)
    yaw2=0
    xobj=x+thobj*np.sin(yaw*np.pi/180.)
    yobj=y-thobj*np.cos(yaw*np.pi/180.)

    obj=[x,y]
    obslist=[[50,0]]
    Map=create_map(obslist)
    path=A_star([0,0],obj, Map)
    robot.grip.close()
    R=R
    
    return ("MOVE_TO_BOX",frame, {"Map": Map, "obj":obj,  "ltrack_pos": ltrack_pos,
                "rtrack_pos": rtrack_pos,
                "TIME": time.time(), "R":R})


def A_star_move_to_box_blind(robot, frame, Map,obj, replan=1,
                            path=[], iteration=0, ltrack_pos=0, rtrack_pos=0, TIME=0, P = np.identity(3),R=[]):
    mtx,dist=load_camera_params()
    frame,box_coords = get_specific_marker_pose(frame=frame,mtx=mtx,dist=dist,marker_id=0,markerLength=8.6)
    old_path=path
    #REPLANNING

    new_ltrack_pos = robot.left_track.position
    new_rtrack_pos = robot.right_track.position
    odom_l, odom_r = new_ltrack_pos - ltrack_pos, new_rtrack_pos - rtrack_pos
    
    marker_list = []
    if box_coords:
        print("REPLANNNIG")
        x=box_coords[0]
        y=box_coords[1]
        yaw=box_coords[2]
        thobj=50
        xobj=x+thobj*np.sin(yaw*np.pi/180.)
        yobj=y-thobj*np.cos(yaw*np.pi/180.)
        obj=[xobj+robot.position[0],yobj+robot.position[1]]

        angle = np.arctan2(yobj,xobj)
        distance = np.sqrt(np.power(xobj,2) + np.power(yobj,2))
        marker_list.append([angle,distance,(yaw+90)*pi/180])
        print("MARKER POSITION X AND Y: ", x , y)

    
    marker_map = np.array([[150,0,0]])
    marker_map_obj = np.array([[110,0,0]])

    Ts = 0.3
    estim_rob_pos, P  = kalman_filter2(odom_r,odom_l,robot.position,marker_list, marker_map_obj,Ts,P)


    d = np.ones(3)
    d[0] = estim_rob_pos[0] + 28 *np.cos(estim_rob_pos[2] * pi/180)
    d[1] = estim_rob_pos[1] + 28* np.sin(estim_rob_pos[2]*pi/180)
    d[2] = estim_rob_pos[2]

    R.append(d)
    mapa=[]

    map_renderer.plot_bricks_and_trajectory(mapa, R)
    robot.position= estim_rob_pos
    print("robot_estim_pos_Astar: ", robot.position)



    #update map
    path=A_star(robot.position[0:2], marker_map_obj[0,:], Map)
    
    replan=1
    goal_pos=marker_map_obj[0,:]

    t0 = time.time()

    vel_wheels, new_path = A_star_control(robot.position,goal_pos,
    									Map, robot.sampling_rate,
                                             odom_r= odom_r,odom_l=odom_l,
                                        iteration=iteration, path=path)
    
    

    #print("DIFFERENTCE WITH THE GOAL:",abs(estim_rob_pos[0]-goal_pos[0]),abs(estim_rob_pos[1]-goal_pos[1]))
    
    #CONDITION FOR EXITTING

    distance_to_target = np.sqrt(np.power(estim_rob_pos[0]-marker_map_obj[0,0],2)+ np.power(estim_rob_pos[1]-marker_map_obj[0,1],2))

    print("###########################################################################################################")
    print("disatnce to target: ", distance_to_target)
    print("estimated vs goal", estim_rob_pos[0:2],goal_pos)
    print("###########################################################################################################")
    
    if abs(estim_rob_pos[0]-marker_map_obj[0,0]) < 10 and abs(estim_rob_pos[1]-marker_map_obj[0,1]) < 10:
        return ("MOVE_TO_BOX_BY_VISION", frame, {"replan":replan,"iteration" : iteration, "path" : new_path, "ltrack_pos": new_ltrack_pos, "rtrack_pos": new_rtrack_pos, "TIME": t0})

    robot.move(vel_left=vel_wheels[1], vel_right=vel_wheels[0])
    iteration += 1
   
    return ("MOVE_TO_BOX", frame, {"replan":replan,"Map":Map,"obj":goal_pos,"iteration" : iteration, "path" : new_path, "ltrack_pos": new_ltrack_pos, "rtrack_pos": new_rtrack_pos, "TIME": t0,"R":R,"P":P})

def PID_control(robot, marker_map, box_coords,hist):
    vel_st=100
    vel_rot=60
    lat_tol=4
    yshift=6
    er_x = marker_map[0,0] - robot[0]
    er_y = marker_map[0,1] - robot[1]
    er_angle = np.arctan2(er_y, er_x) - robot[2]*pi/180
    er_angle = np.arctan2(er_y, er_x) - robot[2]*pi/180
    print("ANGLES WITH MARKER AND ERROR",np.arctan2(er_y, er_x)*180/pi,robot[2])

    if er_angle > pi:
        er_angle = er_angle - 2*pi
    if er_angle < -pi:
        er_angle = er_angle + 2*pi

    distance = np.sqrt(np.power(er_x,2)+np.power(er_y,2))

    if box_coords:

        if abs(box_coords[1]+yshift)>lat_tol:
            vel_wheels=np.asarray([-vel_rot,vel_rot])*np.sign(-box_coords[1])
            print("GUIDDE BY VISION")
        elif box_coords[0]>35:
            vel_wheels=np.asarray([vel_st,vel_st])
            print("GUIDDE BY VISION")
        else:
            vel_wheels=np.asarray([0,0])
            hist = 0
            print("STOP")


    else:
        if hist == 0:
            vel_wheels=np.asarray([0,0])
        elif er_angle > 0.4:
            vel_wheels=np.asarray([vel_rot,-vel_rot])
            hist = 1
        elif er_angle <-0.4:
            vel_wheels=np.asarray([-vel_rot,vel_rot])
            hist = -1
        elif hist ==1 : 
            vel_wheels=np.asarray([vel_rot,-vel_rot])
        else : 
            vel_wheels=np.asarray([-vel_rot,vel_rot])
        print("CORRECTING ANGLE",er_angle)
    return vel_wheels, hist






def move_to_box_by_vision(robot, frame, replan=1,
                            path=[], iteration=0, ltrack_pos=0, rtrack_pos=0, TIME=0, P = np.identity(3),
                            histeresis = 1):
    mtx,dist=load_camera_params()
    frame,box_coords = get_specific_marker_pose(frame=frame,mtx=mtx,dist=dist,marker_id=0,markerLength=8.6)

    new_ltrack_pos = robot.left_track.position
    new_rtrack_pos = robot.right_track.position
    odom_l, odom_r = new_ltrack_pos - ltrack_pos, new_rtrack_pos - rtrack_pos
    


    marker_list = []
    if box_coords:
        x=box_coords[0]
        y=box_coords[1]
        yaw=box_coords[2]
        thobj=40
        xobj=x+thobj*np.sin(yaw*np.pi/180.)
        yobj=y-thobj*np.cos(yaw*np.pi/180.)
        obj=[xobj+robot.position[0],yobj+robot.position[1]]
        angle = np.arctan2(yobj,xobj)
        distance = np.sqrt(np.power(xobj,2) + np.power(yobj,2))
        marker_list.append([angle,distance,(yaw+90)*pi/180])
        print("MARKER POSITION X AND Y: ", x , y)



    marker_map = np.array([[150,0,0]])
    marker_map_obj = np.array([[110,0,0]])

    Ts = 0.3
    estim_rob_pos, P  = kalman_filter2(odom_r,odom_l,robot.position,marker_list, marker_map_obj,Ts,P)

    robot.position= estim_rob_pos
    print("robot_estim_pos_PID: ", robot.position)

    
    vel_wheels, hist = PID_control(estim_rob_pos, marker_map,box_coords, histeresis)
    if hist==0:
        return "PLACE_OBJECT_IN_THE_BOX",frame,{}
    
    robot.move(vel_wheels[0],vel_wheels[1])
    return ("MOVE_TO_BOX_BY_VISION", frame, {"ltrack_pos": new_ltrack_pos, "rtrack_pos" : new_rtrack_pos, "histeresis" : hist})

def place_object_in_the_box(robot,frame):
    robot.move(vel_left=100,vel_right=100,time=2000)
    print("MOVING")
    robot.left_track.wait_until_not_moving(timeout=3000)
    robot.reset()
    robot.grip.wait_until_not_moving(timeout=3000)
    print("finish")
    return "FINAL_STATE"

with Robot(AsyncCamera(1), tracker=TrackerWrapper(cv2.TrackerKCF_create), object_detector=None ) as robot:
    robot.map = [(200, 0)]
    robot.sampling_rate = 0.1
    print("These are the robot motor positions before planning:", robot.left_track.position, robot.right_track.position)
    # Define the state graph, we can do this better, currently each method
    # returns the next state name
    states = [
        State(
            name="SEARCH_TARGET",
            act=search_box,
            default_args={
                "ltrack_pos": robot.left_track.position,
                "rtrack_pos": robot.right_track.position,
            }
        ),
        State(
             name="COMPUTE_PATH",
             act=compute_path,
         ),
         State(
             name="MOVE_TO_BOX",
             act=A_star_move_to_box_blind,
            default_args={
                "ltrack_pos": robot.left_track.position,
                "rtrack_pos": robot.right_track.position,
                "TIME": time.time()
            }
         ),
        State(
             name="MOVE_TO_BOX_BY_VISION",
             act=move_to_box_by_vision,
         ),
        State(
             name="PLACE_OBJECT_IN_THE_BOX",
             act=place_object_in_the_box,
         ),
        State(
            name="FINAL_STATE",
            act=lambda robot, frame, **args: time.sleep(.5)
        )
    ]
    state_dict = {}
    for state in states:
        state_dict[state.name] = state

    start_state = states[0]

    main_loop(robot, start_state, state_dict, delay=0)