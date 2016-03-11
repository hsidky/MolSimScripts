#!/afs/crc.nd.edu/x86_64_linux/python/3.4.0/gcc-4.8.0/bin/python3
''' reactive_flux.py - Calculates the normalized reactive flux, k(t),
	from a set of GROMACS simulations started at the maximum of the
	free energy barrier. Currently supports bimolecular reactions.
'''
import os
import numpy as np
import math
import sys

def getCoordinates(line):
	"""Parses coordinates from a particular line of a .gro file."""
	this_line = line.split()
	x = float(this_line[3])
	y = float(this_line[4])
	z = float(this_line[5])
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
	final_list = []
	normalization = list1[0]
	for i in range(0, len(list1)):
		final_list.append(list1[i]/normalization)
	return final_list

def usage():
	print("Something went wrong. Please check your inputs.")
	print("There three input files required:")
	print("1) ./settings")
	print("""num_simulations = int(settings_list[0])
			num_particles   = int(settings_list[1])
			num_frames      = int(settings_list[2])
			runtime         = float(settings_list[3])
			time_step       = float(settings_list[4])
			xbox            = float(settings_list[5])
			ybox            = float(settings_list[6])
			zbox            = float(settings_list[7])
			ts_loc_approx   = float(settings_list[8])""")
	print("2) ./molecule1")
	print("""atom_id1 atom_mass1
			atom_id2 atom_mass2...""")
	print("3) ./molecule2")

## USER INPUT ##
# Try to parse system info, otherwise give the user the usage()
try:
	molecules = []
	with open('settings', 'r') as settings_file:
		settings_list = settings_file.readlines()
		num_simulations = int(settings_list[0])
		num_particles   = int(settings_list[1])
		num_frames      = int(settings_list[2])
		runtime         = float(settings_list[3])
		time_step       = float(settings_list[4])
		xbox            = float(settings_list[5])
		ybox            = float(settings_list[6])
		zbox            = float(settings_list[7])
		ts_loc_approx   = float(settings_list[8])
		print("Read in ./settings successfully.")
	for molecule in range(0, 2):
		with open('molecule{0}'.format(molecule+1), 'r') as molecule1_file:
			this_molecule = []
			for line in molecule1_file.readlines():
				this_line = line.split()
				this_molecule.append([int(this_line[0]), float(this_line[1])])
		molecules.append(this_molecule)
		print("Read in ./molecule{0} sucessfully.".format(molecule))
	print("Cool - everything looks good.  We're ready to go.")
except:
	usage()
	exit()

# Based on the inputs above, some quantities that are needed...
half_xbox       = xbox/2.0
half_ybox       = ybox/2.0
half_zbox       = zbox/2.0
frame_length    = num_particles + 3 # GROMACS prints a few extra lines, we need the true frame length.

## Data structure initialization
time = list(np.linspace(0.00000, runtime + 0.0001, num_frames))
first_frames = list(np.arange(0, frame_length*num_frames, frame_length))
ktnum = [0 for i in range(0, num_frames)]
ktden = [0 for i in range(0, num_frames)]
inc_pts = 0
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

		# Loop over all frames
		for frame in first_frames:
			# Find molecule center of masses
			COMs = []
			for molecule in molecules:
					coordinate_list = []
					mass_list = []
					for atom in molecule:
						coordinate_list.append(getCoordinates(thisgro[1+frame+atom[0]]))
						mass_list.append(atom[1])
					COMs.append(COM(coordinate_list, mass_list))
			# Find displacement vector between them, along with magnitude
			disp = wrap(displacement(COMs[0], COMs[1]))
			mag_disp = magnitude(disp)
			# If analyzing the first frame, extract rdot(0)
			if first_frames.index(frame) == 0:
				COMs = []
				# Define Transition State Location
				ts_loc = magnitude(disp)
				if abs(ts_loc - ts_loc_approx) > 0.05:
					break
				# Find COMs at the second frame.
				for molecule in molecules:
					coordinate_list = []
					mass_list = []
					for atom in molecule:
						coordinate_list.append(getCoordinates(thisgro[frame+frame_length+atom[0]+1]))
						mass_list.append(atom[1])
					COMs.append(COM(coordinate_list, mass_list))
				# Find displacement vector between them, along with magnitude
				disp2 = wrap(displacement(COMs[0], COMs[1]))
				mag_disp2 = magnitude(disp2)
				# Calculate rdot(0)
				rdotzero = (mag_disp2 - mag_disp)/time_step
				# Calculate Heavyside(rdot(0))
				hs_rdotzero = heavyside(rdotzero, index=first_frames.index(frame), rdotzero=rdotzero)
				inc_pts += 1
			# Calculate Heavyside(r(t) - ts_loc)
			hs_rt_ts_loc = heavyside(mag_disp - ts_loc, index=first_frames.index(frame), rdotzero=rdotzero)

			# Calculate k(t) for that frame, append to lists
			ktnum[first_frames.index(frame)] += (rdotzero*hs_rt_ts_loc)
			ktden[first_frames.index(frame)] += (rdotzero*hs_rdotzero)
print("Analysis finished. Producing final reactive flux function, k(t).")
print("Included {0} data points.".format(inc_pts))

# Produce k(t) from numerator and denominator lists
kt = list_divide(ktnum, ktden)
print("Transmission Coefficient Estimate: {0}".format(kt[-1]))

print("Saving data.")
save_file = open("data", 'w')
for frame in range(0,num_frames-1):
	save_file.write("{0} {1}\n".format(time[frame], kt[frame]))
