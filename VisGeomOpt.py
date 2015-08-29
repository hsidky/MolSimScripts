#!/usr/bin/python3
## VisGeomOpt.py: Visualize the iterations of a geometry optimization performed in PSI4.
import time
import subprocess
import select
import sys
from matplotlib import pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import copy

# Check for valid input
if len(sys.argv) != 2:
	print("Usage: python3 VisGeomOpt.py <filename>")
	exit()

# Grab log filename
filename = sys.argv[1]
prevatoms = []
while True:
	atoms = []
	log_file = open(filename, 'r').readlines()
	rev_file = list(reversed(log_file))
	for line in rev_file:
		if 'Geometry (in Angstrom),' in line and "Center" not in rev_file[rev_file.index(line)-2]:
			index = rev_file.index(line)-2
			i = 0
			this_line = rev_file[index-i].split()
			while this_line != []:
				atom_type = this_line[0]
				x         = float(this_line[1])
				y         = float(this_line[2])
				z         = float(this_line[3])
				atoms.append([atom_type, x, y, z])
				i += 1
				this_line = rev_file[index-i].split()
			break
	
	# Plot the data
	if atoms != [] and atoms != prevatoms:
		plt.close()
		numpyatoms = []
		for atom in atoms:
			this_atom = np.asarray([atom[1], atom[2], atom[3]])
			numpyatoms.append(this_atom)
		
		stacked_atoms = np.vstack(numpyatoms)
		ax = plt.subplot(111, projection='3d')
	
		ax.scatter3D(stacked_atoms[:, 0], stacked_atoms[:, 1], stacked_atoms[:, 2], s=60)
		ax.set_xlim3d(-2.5, 2.5)
		ax.set_ylim3d(-2.5, 2.5)
		ax.set_zlim3d(-2.5, 2.5)	
		plt.show(block=False)
		ax.view_init(elev=89, azim=0)
		plt.draw()
		# Wait a second before trying to read the file again.
	prevatoms = copy.deepcopy(atoms)
	time.sleep(0.1)
