#!/usr/bin/env python

import numpy as np
from numpy import column_stack as colstack
from numpy import linalg as la
import sys
import os

# Input output files
xyzfile = '{0}.xyz'.format(os.path.splitext(sys.argv[1])[0])
outfile = '{0}.p2'.format(os.path.splitext(xyzfile)[0])

with open(outfile, 'w') as f:
	f.write('{0: <15} {1: <15} {2: <15} {3: <15}\n'.format('P2', 'ux', 'uy', 'uz'))


def compute_p2(ux, uy, uz):
	u = colstack((ux.ravel(), uy.ravel(), uz.ravel()))
	Q = 1.5*(np.dot(u.transpose(), u)/len(ux) - np.eye(3)/3.)
	w, v = la.eig(Q)

	# Sort eigenvalues, take largest val/vec pair.
	idx = w.argsort()[::-1]
	w = w[idx]
	v = v[:, idx]
	with open(outfile, 'a') as f:
		f.write('{0:<15.8f} {1:<15.8f} {2:<15.8f} {3:<15.8f}\n'.format(w[0], v[0,0], v[1,0], v[2,0]))


def process_frame(f, n, x, y, z, ux, uy, uz):
	i = 0
	for line in f:
		lsplit = line.split()
		x[i] = float(lsplit[1])
		y[i] = float(lsplit[2])
		z[i] = float(lsplit[3])
		ux[i] = float(lsplit[4])
		uy[i] = float(lsplit[5])
		uz[i] = float(lsplit[6])
		i += 1
		if i == n:
			return


def read_xyz(filename):
	pcount = 0
	with open(filename, 'r') as f:
		for line in f:
			# Get number of particles.
			pcount = int(line.split()[0])
			# Next line is a comment.
			line = f.next()

			# Extract data from frames
			x = np.zeros((pcount, 1))
			y = np.zeros((pcount, 1))
			z = np.zeros((pcount, 1))
			ux = np.zeros((pcount, 1))
			uy = np.zeros((pcount, 1))
			uz = np.zeros((pcount, 1))

			process_frame(f, pcount, x, y, z, ux, uy, uz)
			compute_p2(ux, uy, uz)

read_xyz(sys.argv[1])
