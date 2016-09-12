#!/afs/crc.nd.edu/x86_64_linux/python/3.4.0/gcc-4.8.0/bin/python3
# umbrella.py - set up umbrella sampling runs from a single steered MD run in GROMACS.
__author__ = "Ken Newcomb"
import os
import sys
import numpy
import shutil

###  Inputs  ###
num_frames = int(input("Number of frames to analyze: "))
distances = numpy.arange(0, 1.201, 0.025).tolist()

# Make folder structure.
if not os.path.exists('confs'):
    os.makedirs('confs')
if not os.path.exists('dists'):
    os.makedirs('dists')
if not os.path.exists('holds'):
    os.makedirs('holds')
print("Folder structure generated.")

# Extract steered MD trajectory frame by frame.
ans = input("Do you need to extract steered MD frames? ")
if ans == "Y":
	filename = input("Name of pull files: ")
	print("Separating frames...")
	os.system("echo 0 | gmx trjconv -f {0}.trr -s {0}.tpr -o confs/conf.gro -sep &> /dev/null".format(filename))
	print("Done.")

# Call GROMACS and get distances between groups
ans = input("Do you need distances from GROMACS? (Y/n) ")
if ans == 'Y':
	filename = input("Name of pull files: ")
	for i in range (0, num_frames+1):
		sys.stdout.write("\rProcessing configuration {0}...".format(i))
		sys.stdout.flush()
		os.system("echo com of group r_1 plus com of group r_2 | gmx distance -s {0}.tpr -f confs/conf{1}.gro -n index.ndx -oall dists/dist{1}.xvg &>/dev/null".format(filename, i))


# Generate a summary file containing the configuration index
# and the distance between the two groups.
print("Generating summary file.")
summary_file = open("summary_distances.dat", 'w')
for i in range(0, num_frames+1):
	dist_file = open("dists/dist{0}.xvg".format(i), 'r')
	dist_list = dist_file.readlines()
	distance = dist_list[15].split()[1]
	print(distance)
	summary_file.write("{0} {1}\n".format(i, distance))
	dist_file.close()
summary_file.close()

# Find configurations closest to given distances
print("Finding best configurations for umbrella sampling...")
summary_file = open("summary_distances.dat", 'r')
summary_list = summary_file.readlines()
desired_points = []
for dist in distances:
	distance_number = distances.index(dist)
	for line in summary_list:
		split_line = line.split()
		# If first time through loop, take this as the best candidate
		if summary_list.index(line) == 0:
			desired_points.append([(float(split_line[1])), split_line[0]])
		# If not, check to see if this value is a better candidate
		else:
			if abs(dist - float(split_line[1])) < abs(dist- desired_points[distance_number][0]):
				desired_points[distance_number] = [float(split_line[1]), split_line[0]]

# Copy configurations to holds/
print("Finished. Last step: Copying over selected configurations.")
i = 0
for point in desired_points:
	if not os.path.exists("holds/{0}/".format(i+1)): os.makedirs("holds/{0}/".format(i+1))
	shutil.copyfile("confs/conf{0}.gro".format(point[1]), "holds/{0}/conf{1}.gro".format(i+1, point[1]))
	print("Configuration {0}: Target: {1:.3f}, Actual: {2:.3f}, Config: {3}".format(i, distances[i], point[0], point[1]))
	i += 1
