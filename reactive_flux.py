#!/afs/crc.nd.edu/x86_64_linux/python/3.4.0/gcc-4.8.0/bin/python3
''' reactive_flux.py - Calculates the normalized reactive flux, k(t),
	from a set of GROMACS simulations started at the maximum of the 
	free energy barrier. Currently supports bimolecular reactions.
'''
import os
import numpy as np
import math
import re

def usage():
	print("Something went wrong.")
	print("num_simulations - number of independent simulations to analyze.")
	print("num_particles - number of particles to track in time.")
	print("box_x, box_y, box_z - box vectors (nanometers)")
	print("\nAfter basic system information is parsed, you will be asked to input molecular information:")
	print("first molecule: particle_id1 mass1 particle_id2 mass2")
	print("particle_id1 - the id of the first particle to track.")
	print("mass1 - the mass of the first particle to track.")


## USER INPUT ##
# Try to parse system info, otherwise give the user the usage()
try:
	molecule1 = []
	molecule2 = []
	num_simulations = int(input("Number of simulations to analyze: "))
	num_particles   = int(input("Total particles in a frame: ")) # This may not be necessary.
	num_frames      = int(input("Number of frames to analyze: ")) # Also may not be nece
	time_step       = float(input("Time step: "))
	box_x           = float(input("Box Vector X (nm) "))
	box_y           = float(input("Box Vector Y (nm) "))
	box_z           = float(input("Box Vector Z (nm) "))
	print("Basic system information read in successfully.")
	print("Now, I need information about the two molecules to track.")
	for molecule in range(0, 2):
		print("Molecule {0}, Atomic Constituents:".format(molecule+1))
		answer = "y"
		while answer == "y":
			atom_id = int(input("Atom ID: "))
			mass    = float(input("Atom Mass: "))
			if molecule == 0:
				molecule1.append([atom_id, mass])
			else:
				molecule2.append([atom_id, mass])
			answer = input("Add another atom to molecule {0}".format(molecule+1))
	print("Cool - everything look's good.  We're ready to go.")
except:
	usage()
	exit()

# Based on the inputs above, some quantities that are needed...
runtime         = time_step*num_frames
half_xbox       = xbox/2.0
half_ybox       = ybox/2.0
half_zbox       = zbox/2.0
frame_length    = num_particles + 3 # GROMACS prints a few extra lines, we need the true frame length.

u_num   = u - 1
o1_num  = o1 - 1
o2_num  = o2 - 1
ion_num = ion -1

def getCoordinates(line):
		"""Parses coordinates from .gro file."""
		parsed_line = re.match('^[\s]+[0-9A-Za-z]+[\s\t]+[0-9A-Za-z]+[\s\t]+[0-9][\s\t]+([0-9.-]+)[\s\t]+([0-9.-]+)[\s\t]+([0-9.-]{5}).*$', line)
		x = float(parsed_line.groups(1)[0])
		y = float(parsed_line.groups(2)[1])
		z = float(parsed_line.groups(3)[2])
		return([x, y, z])

def COM(coordinate_list, mass_list):
	"""Calculates the center of mass vector of a molecule."""
	totalmass = sum(mass_list)
	xcom = 0
	ycom = 0
	zcom = 0
	for coordinate in coordinate_list:
		xcom += coordinate[0]*mass_list[coordinate_list.index(coordinate)]
		ycom += coordinate[1]*mass_list[coordinate_list.index(coordinate)]
		zcom += coordinate[2]*mass_list[coordinate_list.index(coordinate)]
	xcom /= totalmass
	ycom /= totalmass
	zcom /= totalmass
	return([xcom, ycom, zcom])

def displacement(vec1, vec2):
	"""Find the displacement vector connecting two vectors."""
	dx = vec1[0] - vec2[0]
	dy = vec1[1] - vec2[1]
	dz = vec1[2] - vec2[2]
	return [dx, dy, dz]

def magnitude(vec):
	"""Find the magnitude of a vector"""
	return(math.sqrt(vec[0]**2 + vec[1]**2 + vec[2]**2))

def dot_product(vec1, vec2):
	"""Calculate the dot product of two vectors."""
	return (vec1[0]*vec2[0] + vec1[1]*vec2[1] + vec1[2]*vec2[2])

def wrap(vec):
	"""Wrap the box."""
	if vec[0] > half_xbox:
		vec[0] -= xbox
	elif vec[0] < -half_xbox:
		vec[0] += xbox
	if vec[1] > half_ybox:
		vec[1] -= ybox
	elif vec[1] < -half_ybox:
		vec[1] += ybox
	if vec[2] > half_zbox:
		vec[2] -= zbox
	elif vec[2] < -half_zbox:
		vec[2] += zbox
	return vec

def heavyside(arg, index = 1 , rdotzero = 1):
	if index == 0:
		if rdotzero > 0:
			return 1.0
		else:
			return 0.0
	if arg > 0:
		return 1.0
	if arg < 0:
		return 0.0
	if arg == 0:
		return 0.5

def divide(list1, divisor):
	"""Returns a single list from two lists, dividing the values of the first list by the values of the second."""
	final_list = []
	for i in range(0, len(list1)):
		final_list.append(list1[i]/divisor)
	return final_list

def list_divide(list1, list2):
	final_list = []
	for i in range(0, len(list1)):
		final_list.append(list1[i]/list2[i])
	return final_list

def normalize(list1):
	fi
	nal_list = []
	normalization = list1[0]
	for i in range(0, len(list1)):
		final_list.append(list1[i]/normalization)
	return final_list

if __name__ == "__main__":
	## Data structure initialization
	time = list(np.arange(0.00000, runtime + 0.0001, time_step))
	line_numbers = list(np.arange(0, frame_length*num_frames, frame_length))
	ktnum = [0 for i in range(0, num_frames)]
	ktden = [0 for i in range(0, num_frames)]

	# Loop over all 1000 simulations (500 forward, 500 reverse)
	for sim in range (1, num_simulations+1):
		sys.stdout.write("\rAnalyzing simulation {0}/{1}...".format(sim, num_simulations))
		sys.stdout.flush()
		for i in range(0,2):
			thisgro = []
			if i == 0: # forwards
				with open("{0}/nvt{0}.gro".format(sim), "r") as f:
					thisgro = f.readlines()
			elif i == 1: # reverse
				with open("{0}/nvt{0}r.gro".format(sim), "r") as f:
					thisgro = f.readlines()

			# Loop over all 1401 frames
			for line_num in line_numbers:
				# Find water center of mass coordinates
				uranium = getCoordinates(thisgro[line_num+u_num])
				# Find sodium center of mass coordinates
				ion = getCoordinates(thisgro[line_num+ion_num])
				# Find displacement vector between them, along with magnitude
				disp = wrap(displacement(uranium, ion))
				mag_disp = magnitude(disp)
				# If analyzing the first frame, extract rdot(0)
				if line_numbers.index(line_num) == 0:
					# Define Transition State Location
					ts_loc = magnitude(disp)
					# Find water, sodium center of mass coordinates at the second frame.
					uranium2 = getCoordinates(thisgro[line_num+u_num+frame_length])

					# Find sodium center of mass coordinates
					ion2 = getCoordinates(thisgro[line_num+ion_num+frame_length])

					# Find displacement vector between them, along with magnitude
					disp2 = wrap(displacement(uranium2, ion2))
					mag_disp2 = magnitude(disp2)
					# Calculate rdot(0)
					rdotzero = (mag_disp2 - mag_disp)/time_step
					# Calculate Heavyside(rdot(0))
					hs_rdotzero = heavyside(rdotzero, index=line_numbers.index(line_num), rdotzero=rdotzero)
				# Calculate Heavyside(r(t) - ts_loc)
				hs_rt_ts_loc = heavyside(mag_disp - ts_loc, index=line_numbers.index(line_num), rdotzero=rdotzero)

				# Calculate k(t) for that frame, append to lists
				ktnum[line_numbers.index(line_num)] += (rdotzero*hs_rt_ts_loc)
				ktden[line_numbers.index(line_num)] += (rdotzero*hs_rdotzero)
	print("Analysis finished. Producing final reactive flux function, k(t).")

	# Produce k(t) from numerator and denominator lists
	kt = list_divide(ktnum, ktden)
	print("Transmission Coefficient Estimate: {0}".format(kt[-1]))
	
	print("Saving data.")
	save_file = open("data", 'w')
	for frame in range(0,num_frames-1):
		save_file.write("{0} {1}\n".format(time[frame], kt[frame]))
