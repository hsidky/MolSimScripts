#!/afs/crc.nd.edu/x86_64_linux/python/3.4.0/gcc-4.8.0/bin/python3
''' reactive_flux.py - Calculates the normalized reactive flux, k(t),
	from a set of GROMACS simulations started at the maximum of the
	free energy barrier. Currently supports bimolecular reactions.
'''
import os
import numpy as np
import math
import sys
import time

def heavyside(arg, i=1, rdz=1):
	if i == 0:
		if rdz >= 0:
			return 1.0
		else:
			return 0.0
	if arg >= 0:
		return 1.0
	if arg < 0:
		return 0.0

def list_divide(list1, list2):
	final_list = []
	for i in range(0, len(list1)):
		if list2[i] == 0:
			final_list.append(0)
		else:
			final_list.append(list1[i]/list2[i])
	return final_list

def list_subtract(list1, list2):
	final_list = []
	for i in range(0, len(list1)):
		final_list.append(list1[i] - list2[i])
	return final_list

def minimage(x, y, z):
	if x > boxx/2.0:
		x -= boxx
	elif x < -boxx/2.0:
		x += boxx
	if y > boxy/2.0:
		y -= boxy
	elif y < -boxy/2.0:
		y += boxy
	if z > boxz/2.0:
		z -= boxz
	elif z < -boxz/2.0:
		z += boxz
	return [x, y, z]

def covariance(A, B):
	'''Calculates the covariance between two data sets.'''
	# Calculate the mean of A and B, respectively
	muA = np.mean(A)
	muB = np.mean(B)

	# Calculate covariance.
	cov = 0
	N = len(A)
	for eA, eB in zip(A, B):
		cov += ((eA-muA)*(eB-muB))/N
	return cov

def chi(backwards, tsloc):
	'''Checks if the backwards trajectory recrosses the TS.'''
	chilist = []
	recrossed = False
	for value in backwards:
		if recrossed == True:
			chilist.append(0)
		else:
			this_dist = float(value.split()[1])
			if this_dist > tsloc:
				chilist.append(0)
				recrossed = True
			else:
				chilist.append(1)

	return chilist
# Check if we want a special RF function
runtype = ''
if len(sys.argv) == 2:
	runtype = sys.argv[1]
	print(runtype)
if len(sys.argv) == 3:
	runtype = sys.argv[1]
	print(runtype)

## Data structure initialization
num_frames = 600
num_simulations = 2000
ktnum  = [0 for i in range(0, num_frames+1)]
ktnum2 = [0 for i in range(0, num_frames+1)]
ktden  = [0 for i in range(0, num_frames+1)]
timelist = np.linspace(0.000, 3.000, num_frames).tolist()
lastnums = []
lastdens = []

# Get box size.
boxlines = open('1/nvt1.gro', 'r').readlines()
box = boxlines[-1].split()
boxx = float(box[0])
boxy = float(box[1])
boxz = float(box[2])
print("Detected box {0}, {1}, {2}".format(boxx, boxy, boxz))
tslocs = []

if runtype == '':
	print("Calculating the Bennett-Chandler transmission coefficient.")
	for sim in range (1, num_simulations+1):
		sys.stdout.write("\rAnalyzing simulation {0}/{1}...".format(sim, num_simulations))
		sys.stdout.flush()
		for i in range(0,2):
			if i == 0: # forwards
				with open("{0}/distanceu.xvg".format(sim), "r") as f:
					udistfile = f.readlines()
				with open("{0}/distancel.xvg".format(sim), "r") as f:
					ldistfile = f.readlines()
				with open("{0}/velocityu.xvg".format(sim), "r") as f:
					uvelofile = f.readlines()
				with open("{0}/velocityl.xvg".format(sim), "r") as f:
					lvelofile = f.readlines()
				with open("{0}/dist.xvg".format(sim), "r") as f:
					distfile = f.readlines()
			elif i == 1: # reverse
				with open("{0}/distanceur.xvg".format(sim), "r") as f:
					udistfile = f.readlines()
				with open("{0}/distancelr.xvg".format(sim), "r") as f:
					ldistfile = f.readlines()
				with open("{0}/velocityur.xvg".format(sim), "r") as f:
					uvelofile = f.readlines()
				with open("{0}/velocitylr.xvg".format(sim), "r") as f:
					lvelofile = f.readlines()
				with open("{0}/distr.xvg".format(sim), "r") as f:
					distfile = f.readlines()

			# Get r
			tsloc = float(distfile[15].split()[1])
			tslocs.append(tsloc)

			# Get COM of U, L
			UCOM = float(udistfile[24].split()[1]), float(udistfile[24].split()[2]), float(udistfile[24].split()[3])
			LCOM = float(ldistfile[24].split()[1]), float(ldistfile[24].split()[2]), float(ldistfile[24].split()[3])

			# Get COV of U, L
			UCOV = float(uvelofile[24].split()[1]), float(uvelofile[24].split()[2]), float(uvelofile[24].split()[3])
			LCOV = float(lvelofile[24].split()[1]), float(lvelofile[24].split()[2]), float(lvelofile[24].split()[3])

			# Calculate dx, dy, dz
			dx, dy, dz = minimage(UCOM[0]-LCOM[0], UCOM[1]-LCOM[1], UCOM[2]-LCOM[2])

			# Calculate dvx, dvy, dvz
			dvx = UCOV[0]-LCOV[0]
			dvy = UCOV[1]-LCOV[1]
			dvz = UCOV[2]-LCOV[2]

			rdotzero = (dx*dvx + dy*dvy + dz*dvz)/(dx**2+dy**2+dz**2)**0.5
			#print('New Rdotzero: {0}'.format(rdotzero))
			#rdotzero = (distance2-tsloc)/0.005
			#print('Old Rdotzero (finite difference): {0}'.format(rdotzero))
			hs_rdotzero = heavyside(rdotzero)
			# And loop over all distances:
			i = 0
			for line in distfile[15:]:
				this_line = line.split()
				distance = float(this_line[1])
				hs_rt_ts_loc = heavyside(distance - tsloc, i, rdotzero)

				# Calculate k(t) for that frame, append to lists
				ktnum[i] += (rdotzero*hs_rt_ts_loc)
				ktden[i] += (rdotzero*hs_rdotzero)
				i += 1
	print("Analysis finished. Producing final reactive flux function, kbc(t).")
	# Produce k(t) from numerator and denominator lists
	kt = list_divide(ktnum, ktden)

	print("Transmission Coefficient Estimate: {0}".format(np.mean(kt[-200:])))
	print("Saving data.")
	save_file = open("data", 'w')
	for frame in range(0,num_frames-1):
		save_file.write("{0} {1}\n".format(timelist[frame], kt[frame]))
	save_file.close()

	#with open('tcoeff', 'a') as tcfile:
	#	tcfile.write(str(np.mean(kt[-200:])))
#		tcfile.write('\n')

if runtype == 'bc2':
	print("Calculating the Bennett-Chandler 2 transmission coefficient.")
	for sim in range (1, num_simulations+1):
		sys.stdout.write("\rAnalyzing simulation {0}/{1}...".format(sim, num_simulations))
		sys.stdout.flush()
		with open("{0}/distanceu.xvg".format(sim), "r") as f:
			udistfile = f.readlines()
		with open("{0}/distancel.xvg".format(sim), "r") as f:
			ldistfile = f.readlines()
		with open("{0}/velocityu.xvg".format(sim), "r") as f:
			uvelofile = f.readlines()
		with open("{0}/velocityl.xvg".format(sim), "r") as f:
			lvelofile = f.readlines()
		with open("{0}/dist.xvg".format(sim), "r") as f:
			distfile = f.readlines()
		with open("{0}/distr.xvg".format(sim), "r") as f:
			distrfile = f.readlines()

		# Check to see if the trajectory started at the right location.
		# If so, extract rdot(0):
		tsloc = float(distfile[15].split()[1])

		# Get COM of U, L
		UCOM = float(udistfile[24].split()[1]), float(udistfile[24].split()[2]), float(udistfile[24].split()[3])
		LCOM = float(ldistfile[24].split()[1]), float(ldistfile[24].split()[2]), float(ldistfile[24].split()[3])

		# Get COV of U, L
		UCOV = float(uvelofile[24].split()[1]), float(uvelofile[24].split()[2]), float(uvelofile[24].split()[3])
		LCOV = float(lvelofile[24].split()[1]), float(lvelofile[24].split()[2]), float(lvelofile[24].split()[3])

		# Calculate dx, dy, dz
		dx, dy, dz = minimage(UCOM[0]-LCOM[0], UCOM[1]-LCOM[1], UCOM[2]-LCOM[2])

		# Calculate dvx, dvy, dvz
		dvx = UCOV[0]-LCOV[0]
		dvy = UCOV[1]-LCOV[1]
		dvz = UCOV[2]-LCOV[2]

		rdotzero = (dx*dvx + dy*dvy + dz*dvz)/(dx**2+dy**2+dz**2)**0.5
		hs_rdotzero = heavyside(rdotzero)
		# And loop over all distances:
		i = 0
		for fline, bline in zip(distfile[15:], distrfile[15:]):
			this_fline = fline.split()
			fdistance = float(this_fline[1])
			this_bline = bline.split()
			bdistance = float(this_bline[1])
			hs_rt_ts_loc = heavyside(fdistance - tsloc, i, rdz=rdotzero)
			hs_lt_ts_loc = heavyside(tsloc - bdistance, i, rdz=rdotzero)

			# Calculate k(t) for that frame, append to lists
			ktnum[i] += rdotzero*hs_rt_ts_loc*hs_lt_ts_loc
			ktden[i] += rdotzero*hs_rdotzero
			i += 1

		# Save last frame of numerator and denominator to a list
		lastnums.append(rdotzero*hs_rt_ts_loc*hs_lt_ts_loc)
		lastdens.append(rdotzero*hs_rdotzero)

	print("Analysis finished. Producing final reactive flux function, kbc2(t).")
	# Produce k(t) from numerator and denominator lists
	kt = list_divide(ktnum, ktden)

	# Calculate transmission coefficient (last frame)
	tc = np.mean(kt[-1:])

	# Calculate error bars
	sigmaK = (((np.std(lastnums)/ktnum[-1])**2) + ((np.std(lastdens)/ktden[-1])**2)-2*covariance(lastnums, lastdens)/(ktnum[-1]*ktden[-1]))**(1/2)
	sigmafile = open('sigma', 'w')
	sigmafile.write(str(sigmaK))
	sigmafile.close()

	print("Transmission Coefficient Estimate: {0}".format(tc))
	print("Saving data.")
	save_file = open("databc2", 'w')
	for frame in range(0,num_frames-1):
		save_file.write("{0} {1}\n".format(timelist[frame], kt[frame]))
	save_file.close()
	num_file = open('databc2num', 'w')
	for frame in range(0, num_frames-1):
		num_file.write("{0} {1}\n".format(timelist[frame], ktnum[frame]))
	num_file.close()
	den_file = open('databc2den', 'w')
	for frame in range(0, num_frames-1):
		den_file.write("{0} {1}\n".format(timelist[frame], ktden[frame]))
	den_file.close()

if runtype == 'pf':
	print("Calculating the postive flux (PF) transmission coefficient.")
	for sim in range (1, num_simulations+1):
		sys.stdout.write("\rAnalyzing simulation {0}/{1}...".format(sim, num_simulations))
		sys.stdout.flush()
		with open("{0}/distanceu.xvg".format(sim), "r") as f:
			udistfile = f.readlines()
		with open("{0}/distancel.xvg".format(sim), "r") as f:
			ldistfile = f.readlines()
		with open("{0}/velocityu.xvg".format(sim), "r") as f:
			uvelofile = f.readlines()
		with open("{0}/velocityl.xvg".format(sim), "r") as f:
			lvelofile = f.readlines()
		with open("{0}/dist.xvg".format(sim), "r") as f:
			distfile = f.readlines()
		with open("{0}/distr.xvg".format(sim), "r") as f:
			distrfile = f.readlines()

		# Check to see if the trajectory started at the right location.
		# If so, extract rdot(0):
		# Check to see if the trajectory started at the right location.
		# If so, extract rdot(0):
		tsloc = float(distfile[15].split()[1])

		# Get COM of U, L
		UCOM = float(udistfile[24].split()[1]), float(udistfile[24].split()[2]), float(udistfile[24].split()[3])
		LCOM = float(ldistfile[24].split()[1]), float(ldistfile[24].split()[2]), float(ldistfile[24].split()[3])

		# Get COV of U, L
		UCOV = float(uvelofile[24].split()[1]), float(uvelofile[24].split()[2]), float(uvelofile[24].split()[3])
		LCOV = float(lvelofile[24].split()[1]), float(lvelofile[24].split()[2]), float(lvelofile[24].split()[3])

		# Calculate dx, dy, dz
		dx, dy, dz = minimage(UCOM[0]-LCOM[0], UCOM[1]-LCOM[1], UCOM[2]-LCOM[2])

		# Calculate dvx, dvy, dvz
		dvx = UCOV[0]-LCOV[0]
		dvy = UCOV[1]-LCOV[1]
		dvz = UCOV[2]-LCOV[2]

		rdotzero = (dx*dvx + dy*dvy + dz*dvz)/(dx**2+dy**2+dz**2)**0.5
		hs_rdotzero = heavyside(rdotzero)
		chilist = chi(backwards, tsloc)
		# And loop over all distances:
		i = 0
		for fline, bline in zip(distfile[15:], distrfile[15:]):
			this_fline = fline.split()
			fdistance = float(this_fline[1])
			this_bline = bline.split()
			bdistance = float(this_bline[1])
			hs_rt_ts_loc = heavyside(fdistance - tsloc, i, rdz=rdotzero)
			hs_lt_ts_loc = heavyside(bdistance - tsloc, i, rdz=rdotzero)

			# Calculate k(t) for that frame, append to lists
			ktnum[i]  += (rdotzero*hs_rdotzero*hs_rt_ts_loc)
			ktnum2[i] += (rdotzero*hs_rdotzero*hs_lt_ts_loc)
			ktden[i]  += (rdotzero*hs_rdotzero)
			i += 1

	print("Analysis finished. Producing final reactive flux function, kpf(t).")
	# Produce k(t) from numerator and denominator lists
	kt1 = list_divide(ktnum, ktden)
	kt2 = list_divide(ktnum2, ktden)
	kt = list_subtract(kt1, kt2)

	print("Transmission Coefficient Estimate: {0}".format(np.mean(kt[-200:])))
	print("Saving data.")
	save_file = open("datapf", 'w')
	for frame in range(0,num_frames-1):
		save_file.write("{0} {1}\n".format(timelist[frame], kt[frame]))

rdotzeros = []
if runtype == 'epf':
	print("Calculating the transmission coefficient via the effective positive flux (EPF) algorithm [RECOMMENDED].")
	for sim in range (1, num_simulations+1):
		sys.stdout.write("\rAnalyzing simulation {0}/{1}...".format(sim, num_simulations))
		sys.stdout.flush()
		with open("{0}/distanceu.xvg".format(sim), "r") as f:
			udistfile = f.readlines()
		with open("{0}/distancel.xvg".format(sim), "r") as f:
			ldistfile = f.readlines()
		with open("{0}/velocityu.xvg".format(sim), "r") as f:
			uvelofile = f.readlines()
		with open("{0}/velocityl.xvg".format(sim), "r") as f:
			lvelofile = f.readlines()
		with open("{0}/dist.xvg".format(sim), "r") as f:
			distfile = f.readlines()
		with open("{0}/distr.xvg".format(sim), "r") as f:
			distrfile = f.readlines()

		# Check to see if the trajectory started at the right location.
		# If so, extract rdot(0):
		tsloc = float(distfile[15].split()[1])

		# Get COM of U, L
		UCOM = float(udistfile[24].split()[1]), float(udistfile[24].split()[2]), float(udistfile[24].split()[3])
		LCOM = float(ldistfile[24].split()[1]), float(ldistfile[24].split()[2]), float(ldistfile[24].split()[3])

		# Get COV of U, L
		UCOV = float(uvelofile[24].split()[1]), float(uvelofile[24].split()[2]), float(uvelofile[24].split()[3])
		LCOV = float(lvelofile[24].split()[1]), float(lvelofile[24].split()[2]), float(lvelofile[24].split()[3])

		# Calculate dx, dy, dz
		dx, dy, dz = minimage(UCOM[0]-LCOM[0], UCOM[1]-LCOM[1], UCOM[2]-LCOM[2])

		# Calculate dvx, dvy, dvz
		dvx = UCOV[0]-LCOV[0]
		dvy = UCOV[1]-LCOV[1]
		dvz = UCOV[2]-LCOV[2]

		# Calculate rdotzero and its heaviside
		rdotzero = (dx*dvx + dy*dvy + dz*dvz)/(dx**2+dy**2+dz**2)**0.5
		hs_rdotzero = heavyside(rdotzero)
		rdotzeros.append(rdotzero*hs_rdotzero)

		# Calculate the CHI function. (see van erp paper/powerpoint)
		chilist = chi(distrfile[15:], tsloc)

		# And loop over all distances:
		i = 0
		for fline in distfile[15:]:
			this_fline = fline.split()
			fdistance = float(this_fline[1])
			hs_rt_ts_loc = heavyside(fdistance - tsloc, i, rdz=rdotzero)
			# Calculate k(t) for that frame, append to lists
			ktnum[i] += rdotzero*hs_rdotzero*chilist[i]*hs_rt_ts_loc
			ktden[i] += rdotzero*hs_rdotzero
			i += 1

		# Save last frame of numerator and denominator to a list
		lastnums.append(rdotzero*hs_rdotzero*chilist[i-1]*hs_rt_ts_loc)
		lastdens.append(rdotzero*hs_rdotzero)

	print("Analysis finished.")
	# Produce k(t) from numerator and denominator lists
	kt = list_divide(ktnum,ktden)

	# Calculate error bars
	sigmaA = np.std(lastnums)
	sigmaB = np.std(lastdens)
	A = ktnum[-1]/num_simulations
	B = ktden[-1]/num_simulations
	print("A: {0}".format(A))
	print("B: {0}".format(B))
	print("sigA: {0}".format(sigmaA))
	print("sigB: {0}".format(sigmaB))
	sigmaK = kt[-1]*((sigmaA/A)**2 + (sigmaB/B)**2 - (2*covariance(lastnums,lastdens)/(A*B)))**(0.5)
	sigmaK = sigmaK/(num_simulations**0.5)
	sigmafile = open('sigma', 'w')
	sigmafile.write(str(sigmaK))
	sigmafile.close()
	print("ERROR: {0}".format(sigmaK))

	print("Transmission Coefficient: {0}".format(kt[-1]))
	print("Saving data.")
	save_file = open("transmissioncoefficient", 'w')
	for frame in range(0, num_frames-1):
		save_file.write("{0} {1}\n".format(timelist[frame], kt[frame]))
	save_file.close()
	print("wrote.")
	print("AVERAGE rdotzerohsrdotzero: {0}".format(np.mean(rdotzeros)))
	#num_file = open('databc2num', 'w')
	#for frame in range(0, num_frames-1):
	#	num_file.write("{0} {1}\n".format(timelist[frame], ktnum[frame]))
	#num_file.close()
	#den_file = open('databc2den', 'w')
	#for frame in range(0, num_frames-1):
	#	den_file.write("{0} {1}\n".format(timelist[frame], ktden[frame]))
	#den_file.close()
