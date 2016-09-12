# wham.py: a thin wrapper for g_wham that does it all.
import os
import shutil
import sys

if len(sys.argv) != 2:
	print("sample usage: python3 wham.py 1-20")
	exit()

# Parse input
wham_range = sys.argv[1].split('-')
lower = int(wham_range[0])
upper = int(wham_range[1])

# Create WHAM/ Delete tpr-files and pullf-files
if not os.path.exists("WHAM/"): os.makedirs("WHAM/")
if os.path.exists("WHAM/tpr-files.dat"): os.remove("WHAM/tpr-files.dat")
if os.path.exists("WHAM/pull-files.dat"): os.remove("WHAM/pull-files.dat")

# Copy tprs, pullfs
for i in range(lower, upper+1):
	# pullfs
	shutil.copyfile("./pullf-umbrella{0}.xvg".format(i), "./WHAM/pullf-umbrella{0}.xvg".format(i))
	# tprs
	shutil.copyfile("./holds/{0}/hold{0}.tpr".format(i), "./WHAM/hold{0}.tpr".format(i))
	# create tpr-files.dat , pull-files.dat
	tpr_files = open("./WHAM/tpr-files.dat", "a")
	pull_files = open("./WHAM/pull-files.dat", "a")
	tpr_files.write("./WHAM/hold{0}.tpr\n".format(i))
	pull_files.write("./WHAM/pullf-umbrella{0}.xvg\n".format(i))
	tpr_files.close()
	pull_files.close()
# Call g_wham
os.system("gmx wham -it ./WHAM/tpr-files.dat -if ./WHAM/pull-files.dat -o -hist -unit kT")
