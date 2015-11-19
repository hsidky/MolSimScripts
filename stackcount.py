#!/usr/bin/env python

import numpy as np
import numpy.linalg as linalg

# Input file name 

xyzfile = 'testsnap.xyz'

bdim = np.array([135.0, 135.0, 135.0])

def anint(x):
	if x >= 0:
		return np.floor(x + 0.5)
	else:
		return np.ceil(x - 0.5)


def minimum_image(rij):
	rij[0] -= bdim[0]*anint(rij[0]/bdim[0])
	rij[1] -= bdim[1]*anint(rij[1]/bdim[1])
	rij[2] -= bdim[2]*anint(rij[2]/bdim[2])


def compute_properties(x, u):
	stacks = []
	for i in range(x.shape[0]):
		#print('Processing particle {0}. Stack count: {1}'.format(i, len(stacks)))
		xi = x[i,:]
		ui = u[i,:]
		found = False # Have we found a stack?
		for stack in stacks:
			for j in stack:
				xj = x[j,:]
				uj = u[j,:] 

				# minimum image convention.
				rij = xi - xj
				minimum_image(rij)

				if linalg.norm(rij) <= 8.0:
					stack.append(i)
					found = True
					break

			if found is True:
				break

		# If we still haven't found an appropriate stack, 
		# create a new one.
		if found is False:
			stacks.append([i])

	# Mean stack length. 
	msl = np.mean([len(s) for s in stacks])
	print('Average stack length: {0}'.format(msl))
	i = 0
	for stack in stacks:
		i += 1
		for j in stack:
			print('GB{0} {1} {2} {3}'.format(i, x[j,0], x[j,1], x[j,2]))

def process_frame(f, n, x, u):
	i = 0
	for line in f:
		lsplit = line.split()
		x[i,:] = lsplit[1:4]
		u[i,:] = lsplit[4:7]
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
			x = np.zeros((pcount, 3)) # Positions
			u = np.zeros((pcount, 3)) # Directors
			process_frame(f, pcount, x, u)

			compute_properties(x, u)
			print('Processed frame {0}...'.format(frame))
			frame += 1
			if frame is 1:
				return

read_xyz(xyzfile)