#!/usr/bin/env python

import numpy as np

# Input file name 

xyzfile = 'nvt-140.xyz'


def compute_properties(x, y, z, ux, uy, uz):
	stacks = []
	

def process_frame(f, n, x, y, z, ux, uy, uz):
	i = 0
	for line in f:
		lsplit = line.split()
		x[i] = lsplit[1]
		y[i] = lsplit[2]
		z[i] = lsplit[3]
		ux[i] = lsplit[4]
		uy[i] = lsplit[5]
		uz[i] = lsplit[6]
		i += 1
		if i == n:
			return

def read_xyz(filename):
	frame = 0
	pcount = 0
	with open(filename, 'r') as f:
		for line in f:
			# Get particle count.
			pcount = int(line.split()[0])

			# Skip comment line.
			line = f.next()
			
			# Initialize coordinates and directors
			# and get frame data.
			x = np.zeros((pcount, 1))
			y = np.zeros((pcount, 1))
			z = np.zeros((pcount, 1))
			ux = np.zeros((pcount, 1))
			uy = np.zeros((pcount, 1))
			uz = np.zeros((pcount, 1))
			process_frame(f, pcount, x, y, z, ux, uy, uz)

			compute_properties(x, y, z, ux, uy, uz)
			# print('Processed frame {0}...'.format(frame))
			frame += 1
			if frame is 150:
				return

read_xyz(xyzfile)