#!/usr/bin/env python

import numpy as np
import numpy.linalg as linalg
import os
import sys

# Input file name 
xyzfile = '{0}.xyz'.format(os.path.splitext(sys.argv[1])[0])
outfile = '{0}.stacks'.format(os.path.splitext(xyzfile)[0])

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
	ids = range(x.shape[0])
	while ids:
		# Get the first element from the list of candidates 
		# and add to new stack.
		i = ids[0]
		stack = [i]
		ids.remove(i)

		prevl = 0
		currl = len(stack)
		while prevl != currl:
			prevl = currl
			for j in ids[:]:
				xj = x[j, :]
				for k in stack:
					xk = x[k, :]
					rjk = xj - xk
					minimum_image(rjk)

					if linalg.norm(rjk) <= 5.5:
						stack.append(j)
						ids.remove(j)
						break

			currl = len(stack)

		# print('Appended stack of length {0}'.format(currl))
		stacks.append(stack)

	with open(outfile, 'a') as f:
		f.write('{0}\n'.format(' '.join([str(len(s)) for s in stacks])))


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

			# Get dimensions from next line.
			line = f.next()
			lsplit = line.split()
			bdim[0] = float(lsplit[1])
			bdim[1] = float(lsplit[5])
			bdim[2] = float(lsplit[9])
			
			# Initialize coordinates and directors
			# and get frame data.
			x = np.zeros((pcount, 3)) # Positions
			u = np.zeros((pcount, 3)) # Directors
			process_frame(f, pcount, x, u)

			compute_properties(x, u)
			print('Processed frame {0}...'.format(frame))
			frame += 1


read_xyz(xyzfile)