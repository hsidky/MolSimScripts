#!/afs/crc.nd.edu/x86_64_linux/python/3.4.0/gcc-4.8.0/bin/python3
''' reactive_flux.py - Calculates the normalized reactive flux, k(t),
	from a set of GROMACS simulations started at the maximum of the
	free energy barrier. Currently supports bimolecular reactions.
'''
import os
import numpy as np
import math
import sys

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

def list_divide(list1, list2):
	final_list = []
	for i in range(0, len(list1)):
		final_list.append(list1[i]/list2[i])
	return final_list

# Check if we want a special RF function
runtype == ''
if len(sys.argv) == 3:
	runtype = sys.argv[2]

## Data structure initialization
num_frames = 600
num_simulations = 500
ktnum  = [0 for i in range(0, num_frames)]
ktnum2 = [0 for i in range(0, num_frames)]
ktden  = [0 for i in range(0, num_frames)]
timelist = np.linspace(0.000, 3.000, num_frames).tolist()

if runtype == '':
	print("Calculating the Bennett-Chandler transmission coefficient.")
	for sim in range (1, num_simulations+1):
		sys.stdout.write("\rAnalyzing simulation {0}/{1}...".format(sim, num_simulations))
		sys.stdout.flush()
		for i in range(0,2):
			if i == 0: # forwards
				with open("{0}/dist.xvg".format(sim), "r") as f:
					distfile = f.readlines()
			elif i == 1: # reverse
				with open("{0}/distr.xvg".format(sim), "r") as f:
					distfile = f.readlines()

			# Check to see if the trajectory started at the right location.
			# If so, extract rdot(0):
			tsloc = float(distfile[15].split()[1])
			print("TS: {0}".format(tsloc))
			distance2 = float(distfile[16].split()[1])
			rdotzero = distance2-tsloc
			hs_rdotzero = heavyside(rdotzero, index=0, rdotzero=rdotzero)
			# And loop over all distances:
			for line in distfile[15:]:
				this_line = line.split()
				distance = float(this_line[1])
				hs_rt_ts_loc = heavyside(distance - tsloc, index=1, rdotzero=rdotzero)

				# Calculate k(t) for that frame, append to lists
				ktnum[distfile[15:].index(line)-1] += (rdotzero*hs_rt_ts_loc)
				ktden[distfile[15:].index(line)-1] += (rdotzero*hs_rdotzero)
	print("Analysis finished. Producing final reactive flux function, kbc(t).")

if runtype == 'bc2':
	print("Calculating the Bennett-Chandler 2 transmission coefficient.")
	for sim in range (1, num_simulations+1):
		sys.stdout.write("\rAnalyzing simulation {0}/{1}...".format(sim, num_simulations))
		sys.stdout.flush()
		with open("{0}/dist.xvg".format(sim), "r") as f:
			forwardfile = f.readlines()
		with open("{0}/distr.xvg".format(sim), "r") as f:
			backwardsfile = f.readlines()

		# Check to see if the trajectory started at the right location.
		# If so, extract rdot(0):
		tsloc = float(distfile[15].split()[1])
		print("TS: {0}".format(tsloc))
		distance2 = float(distfile[16].split()[1])
		rdotzero = distance2-tsloc
		hs_rdotzero = heavyside(rdotzero, index=0, rdotzero=rdotzero)
		# And loop over all distances:
		for line in forwardfile[15:]:
			this_line = line.split()
			distance = float(this_line[1])
			hs_rt_ts_loc = heavyside(distance - tsloc, index=1, rdotzero=rdotzero)

			# Calculate k(t) for that frame, append to lists
			ktnum[forwardfile[15:].index(line)-1] += (rdotzero*hs_rt_ts_loc)
			ktden[forwardfile[15:].index(line)-1] += (rdotzero*hs_rdotzero)

		for line in backwardfile[15:]:
			this_line = line.split()
			distance = float(this_line[1])
			hs_lt_ts_loc = heavyside(tsloc - distance, index=1, rdotzero=rdotzero)

			# Calculate k(t) for that frame, append to lists
			ktnum[backwardfile[15:].index(line)-1] *= (rdotzero*hs_lt_ts_loc)
	print("Analysis finished. Producing final reactive flux function, kbc2(t).")
# Produce k(t) from numerator and denominator lists
kt = list_divide(ktnum, ktden)
print("Transmission Coefficient Estimate: {0}".format(np.mean(kt[-200:])))
print("Saving data.")
save_file = open("data", 'w')
for frame in range(0,num_frames-1):
	save_file.write("{0} {1}\n".format(timelist[frame], kt[frame]))
