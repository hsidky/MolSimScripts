#!/usr/bin/python3
''' XYZ2VTK.py - Takes in an XYZ file containing coordinates 
    and vectors then converts them into VTK structured grids 
    (snapshots) for use in ParaView.
'''
import argparse
import os
from os import path

parser = argparse.ArgumentParser()
parser.add_argument(
	"-n",
	help="Number of frames to dump",
	type=int,
	default=0
)
parser.add_argument(
	"-f", 
	"--frames", 
	help="Dump every 'n'th frame", 
	type=int, 
	default=1
)
parser.add_argument(
	"-t",
	"--titles",
	help="Titles of each data column",
	type=str,
	default=""
)
parser.add_argument( 
	"--vector",
	help="Column positions of vector data",
	type=int,
	nargs=3
)
parser.add_argument(
	"-s",
	"--scalars",
	help="Column positions of scalar data",
	type=int,
	nargs="+"
)
parser.add_argument(
	"input",
	help="Input file name",
	type=str
)
parser.add_argument(
	"-o",
	"--output",
	help="Output folder name/file prefix",
	type=str,
	nargs=1
)

# Parse arguments
args = parser.parse_args()

# Definitions
frame = 0  # current frame 
n = args.frames  # Dump every "nth" frame
titles = args.titles.split()
nbegin = 0  # Are we at the beginning of a new frame?
fmax = args.n  # Maximum number of frames to dump
dirout = path.splitext(args.input)[0]  # Folder name
prefix = "frame"  # File prefix
vector = args.vector  # Vector to write
scalars = args.scalars  # Scalars to write

# Calculate required number of titles
ntit = 0
if vector is not None:
	ntit += len(vector) / 3
if scalars is not None:
	ntit += len(scalars)

if len(titles) is not int(ntit):
	print("Invalid number of titles. Must specify {0}".format(int(ntit)))
	exit()

# Check that the output directory exists.
# If not, make it.
if not path.exists(dirout):
    os.makedirs(dirout)

# Containers for frame data.
pdata = []  # Positional data
vdata = []  # Vector data
sdata = []  # Scalar data
species = []  # Species data

# Open input file 
with open(args.input, 'r') as f:
	for line in f:
		# If split is 1 we are at a new frame.
		if len(line.split()) is 1:
			nbegin = 1
			fname = path.join(dirout, "{0}{num:04d}.vtk".format(prefix, num=frame))

			# Write frame data if available 
			if len(pdata):
				with open(fname, "w") as fout:
					fout.write("# vtk DataFile Version 2.0\n")
					fout.write("VTK from XYZ2VTK\n")
					fout.write("ASCII\n")
					fout.write("DATASET STRUCTURED_GRID\n")
					fout.write("DIMENSIONS 1 {0} 1\n".format(len(pdata)))
					fout.write("POINTS {0} float\n".format(len(pdata)))
					for pline in pdata:
						fout.write("{0} {1} {2}\n".format(pline[0], pline[1], pline[2]))

					# If there's vector data.
					if len(vdata):
						fout.write("POINT_DATA {0}\n".format(len(vdata)))
						fout.write("VECTORS {0} float\n".format(titles[0]))
						for vline in vdata:
							fout.write("{0} {1} {2}\n".format(vline[0], vline[1], vline[2]))

					# Add species data 
					fout.write("SCALARS species float\n")
					fout.write("LOOKUP_TABLE default\n")
					for sline in sdata:
						fout.write("{0}\n".format(sline[0]))

					# Clear data lists.
					pdata = []
					vdata = []
					sdata = []

			# Increment frame counter.
			frame += 1
			continue

		# If we are at the beginning of a line, skip 
		# this frame since it's the box vecotrs.
		if nbegin is 1:
			nbegin = 0
			continue

		# If we are not at a frame we're interested in,
		# pass.
		if n and (frame - 1) % n is not 0:
			continue

		# If we maxed out the number of frames, quit
		if frame > fmax:
			break

		# Just in case we check that we're not at frame 0.
		if not nbegin and frame is not 0:
			data = line.split()

			# Append position data to array
			pdata.append(list(map(float, data[1:4])))

			# Append vector data to array
			if vector is not None:
				vlist = []
				vlist.append(float(data[vector[0]]))
				vlist.append(float(data[vector[1]]))
				vlist.append(float(data[vector[2]]))
				vdata.append(vlist)

			# Append species data to array
			if data[0] not in species:
				species.append(data[0])

			slist = []	
			slist.append(species.index(data[0]))
			sdata.append(slist)
