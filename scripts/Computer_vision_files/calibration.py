import numpy as np
import cv2
import glob
import math as m
import cv2.aruco as aruco
from time import time
from time import sleep
# termination criteria
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((9*6,3), np.float32)
objp[:,:2] = np.mgrid[0:9,0:6].T.reshape(-1,2)

# Arrays to store object points and image points from all the images.
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane.

images = glob.glob('*.jpg')
print (len(images))
for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    # Find the chess board corners
    ret, corners = cv2.findChessboardCorners(gray, (9,6),None, 1 | 4)
    print(ret)
    # If found, add object points, image points (after refining them)
    if ret == True:
        objpoints.append(objp)

        corners2 = cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
        imgpoints.append(corners2)

        # Draw and display the corners
        img = cv2.drawChessboardCorners(img, (9,6), corners2,ret)
        cv2.imshow('img',img)
        cv2.waitKey(20)

cv2.destroyAllWindows()

ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1],None,None)
mtx=np.array(mtx)
dist=np.array(dist)
rvecs=np.array(rvecs)
tvecs=np.array(tvecs)
print(mtx.shape,dist.shape,rvecs.shape,tvecs.shape)


## write in a yaml
data = {"camera_matrix": mtx, "dist_coeff": dist}
fname = "data.yaml"
import yaml
with open(fname, "w") as f:
    yaml.dump(data, f)

np.savez("camera_parameters",cam_matrix=mtx,dist_coeff=dist)

# Add image to crop
img = cv2.imread('Chessboard_15.jpg')
h,  w = img.shape[:2]
newcameramtx, roi=cv2.getOptimalNewCameraMatrix(mtx,dist,(w,h),1,(w,h))

print(newcameramtx)

## GET BORDERS
cap = cv2.VideoCapture(1)
#img = cv2.imread('Chessboard_9.jpg')
while True:
    ret,img=cap.read()
    cv2.imshow("actual image",img)
    if cv2.waitKey(10) & 0xFF==32:
        break

gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
# Find the chess board corners
ret, corners = cv2.findChessboardCorners(gray, (9,6),None, 1 | 4)

board_w = 10;
board_h = 7;
imgPts = np.zeros([4,2],dtype= "float32")
objPts = np.zeros([4,2],dtype= "float32")

imgPts[0,:] = corners[0,:];
imgPts[1,:] = corners[board_w-2,:];
imgPts[2,:] = corners[(board_h-2)*(board_w-1),:];
imgPts[3,:] = corners[(board_h-2)*(board_w-1) + board_w-2,:];

objPts[0,0] = 0; objPts[0,1] = 0;
objPts[1,0] = board_w -1; objPts[1,1] = 0;
objPts[2,0] = 0; objPts[2,1] = board_h -1;
objPts[3,0] = board_w -1; objPts[3,1] = board_h -1;

img = cv2.drawChessboardCorners(img, (9,6), imgPts,ret)
cv2.imshow('img',img)
cv2.waitKey(20)

H = cv2.getPerspectiveTransform(objPts,imgPts)
H[2,2] = 30

print("image size : ", img.shape)
img
dst = cv2.warpPerspective(img,H,(640,1200),flags= cv2.INTER_LINEAR+cv2.WARP_FILL_OUTLIERS+cv2.WARP_INVERSE_MAP)


aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
#board = cv2.aruco.CharucoBoard_create(3,4,.025,.0125,auro_dict)
#img = board.draw((200*3,200*3))

#loading camera parameters
data = np.load('camera_parameters.npz')
mtx=data["cam_matrix"]
dist=data["dist_coeff"]
arucoParams = aruco.DetectorParameters_create()
markerLength = 3.5 


while True:
    ret,frame=cap.read()
    img = cv2.warpPerspective(frame,H,(640,1200),flags= cv2.INTER_LINEAR+cv2.WARP_FILL_OUTLIERS+cv2.WARP_INVERSE_MAP)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)    # aruco.etectMarkers() requires gray image
    corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, aruco_dict, parameters=arucoParams) # Detect aruco
    if ids != None: # if aruco marker detected
        rvec, tvec = aruco.estimatePoseSingleMarkers(corners, markerLength, mtx, dist) # For a single marker
        print("rev and tec:",rvec.shape,tvec.shape)
        imgWithAruco = aruco.drawDetectedMarkers(img, corners, ids, (0,255,0))
        
        for i in range(len(ids)):
            imgWithAruco = aruco.drawAxis(imgWithAruco, mtx, dist, rvec[i], tvec[i], 15)  
            
            print("the marker {} has rotation x:{}, y:{},z:{}".format(ids[i],rvec[i,0,0],rvec[i,0,1],rvec[i,0,2]))
            print("the marker {} has coordinates x:{}, y:{},z:{}".format(ids[i],tvec[i,0,0],tvec[i,0,1],tvec[i,0,2]))
    else:   # if aruco marker is NOT detected
        imgWithAruco = img # assign imRemapped_color to imgWithAruco directly
    #print("retard",time()-tinit)
    sleep(0.05)
    cv2.imshow("aruco", imgWithAruco)   # display
    if cv2.waitKey(50) & 0xFF == ord('q'):   # if 'q' is pressed, quit.
        break
    if cv2.waitKey(10) & 0xFF==27:
        break

