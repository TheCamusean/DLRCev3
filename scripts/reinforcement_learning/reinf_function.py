import numpy as np


def robot_state_update(rob_pos, vel_robot,Ts): # vel_robot = (cm/s ; degrees/s)


	incr_r = vel_robot[0]*Ts
	incr_teta = vel_robot[1]*Ts

	new_pos_rob[0] = pos_rob[0] + incr_r*np.cos((pos_rob[2]+incr_teta/2)*pi/180)
	new_pos_rob[1] = pos_rob[1] + incr_r*np.sin((pos_rob[2]+incr_teta/2)*pi/180)
	new_pos_rob[2] = pos_rob[2] + incr_teta

	#print('new pos: ', new_pos_rob)

	if new_pos_rob[2] >360:
		new_pos_rob[2] = new_pos_rob[2] - 360
	elif new_pos_rob[2] < 0 :
		new_pos_rob[2] = 360 + new_pos_rob[2]

	

	return new_pos_rob 


def create_random_map(n_obs = 10): # Each cell is a 1x1 cm in the map

	cell_size = 1

	map = np.zeros([1000,1000])

	obstacle_size = 28

	obstacle_cells = obstacle_size


	# Obstacles position

	

	obs_pos = np.random.randint(1000-obstacle_cells-1,size=[n_obs,2]) 

	print("obs: ", obs_pos)

	

	for i in range(0,n_obs):

		

		map[obs_pos[i,0]:obs_pos[i,0]+obstacle_cells,obs_pos[i,1]:obs_pos[i,1]+obstacle_cells] = np.ones([obstacle_cells,obstacle_cells])


	target_on = 0
	while(target_on == 1):

		tar_pos = np.random.randint(1000,size=[2])

		if map[tar_pos[0],tar_pos[1]] == 0 :

			map[tar_pos[0],tar_pos[1]] = 2

			target_on = 1

			

	return map












