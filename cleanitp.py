#!/usr/bin/env python

import argparse
import operator

"""
	cleanitp is a script which cleans up an itp file generated by acpype containing a GAFF
	forcefield for gromacs. It converts atom-based specifications to type-based and eliminates
	redundancies.
"""

atomdict = {}

# Type based definitions
atomtypes = []
bondtypes = []
angletypes = []
dihedraltypes = []

# Atom based definitions
atoms = []
bonds = []
angles = []
dihedrals = []


def read_itp(filename):
	with open(filename, "r") as f:
		mode = "none"
		for line in map(str.strip, f):
			# Skip blank lines or comments.
			if not line:
				mode = "none"
				continue

			# Trim comments. Don't change mode in this case.
			line = line.split(";", 1)[0]
			if not line:
				continue

			# Assign mode
			if "atomtypes" in line:
				mode = "atomtypes"
				continue
			elif "bondtypes" in line:
				mode = "bondtypes"
				continue
			elif "angletypes" in line:
				mode = "angletypes"
				continue
			elif "dihedraltypes" in line:
				mode = "dihedraltypes"
				continue
			elif "atoms" in line:
				mode = "atoms"
				continue
			elif "bonds" in line:
				mode = "bonds"
				continue
			elif "angles" in line:
				mode = "angles"
				continue
			elif "dihedrals" in line:
				mode = "dihedrals"
				continue

			# Process mode
			if mode == "atomtypes":
				temp = line.split()
				# type, sigma, epsilon
				atomtypes.append((temp[0], float(temp[5]), float(temp[6])))
			elif mode == "bondtypes":
				temp = line.split()
				bondtype = (temp[0], temp[1], int(temp[2]), float(temp[3]), float(temp[4]))
				bondtypes.append(bondtype)
			elif mode == "angletypes":
				temp = line.split()
				# type1, type2, type3, funct, theta, k
				angletype = (temp[0], temp[1], temp[2], int(temp[3]),
                             float(temp[4]), float(temp[5]))
				angletypes.append(angletype)
			elif mode == "dihedraltypes":
				temp = line.split()
				# type1, type2, type3, type4, func, phase, kd, pn
				dihtype = (temp[0], temp[1], temp[2], temp[3], int(temp[4]),
                          float(temp[5]), float(temp[6]), int(temp[7]))
				dihedraltypes.append(dihtype)
			elif mode == "atoms":
				temp = line.split()
				atom = (int(temp[0]), temp[1], int(temp[2]),
                        temp[3], temp[4], int(temp[5]), float(temp[6]),
                        float(temp[7]))
				atoms.append(atom)

				# Create a map between atom IDs and types
				atomdict[atom[0]] = atom[1]
			elif mode == "bonds":
				temp = line.split()

				# ai, aj, function
				bond = (int(temp[0]), int(temp[1]), int(temp[2]))
				bonds.append(bond)

				if len(temp) > 3:
					# type1, type2, function, r, k
					bondtype = (atomdict[bond[0]], atomdict[bond[1]],
                                int(temp[2]), float(temp[3]), float(temp[4]))
					bondtypes.append(bondtype)
			elif mode == "angles":
				temp = line.split()

				# ai, aj, ak, function
				angle = (int(temp[0]), int(temp[1]), int(temp[2]), int(temp[3]))
				angles.append(angle)

				if len(temp) > 4:
					# type1, type2, type3, funct, theta, k
					angletype = (atomdict[angle[0]], atomdict[angle[1]], atomdict[angle[2]],
	                             int(temp[3]), float(temp[4]), float(temp[5]))
					angletypes.append(angletype)
			elif mode == "dihedrals":
				temp = line.split()

				# ai, aj, ak, al, function
				dih = (int(temp[0]), int(temp[1]), int(temp[2]), int(temp[3]), int(temp[4]))
				dihedrals.append(dih)

				if int(temp[4]) == 3:
					print("Error: RB dihedrals not supported. Please upgrade to the 21st century.")
					quit()

				if len(temp) > 5:
					# type1, type2, type3, type4, func, phase, kd, pn
					dihtype = (atomdict[dih[0]], atomdict[dih[1]], atomdict[dih[2]], atomdict[dih[3]],
	                           int(temp[4]), float(temp[5]), float(temp[6]), int(temp[7]))
					dihedraltypes.append(dihtype)


def write_itp(filename):
	global atoms, bonds, angles, dihedrals, atomtypes, bondtypes, angletypes, dihedraltypes

	# First we clean up the types so there are no duplicates.
	atoms = list(set(atoms))
	bonds = list(set(bonds))
	angles = list(set(angles))
	dihedrals = list(set(dihedrals))
	atomtypes = list(set(atomtypes))
	bondtypes = list(set(bondtypes))
	angletypes = list(set(angletypes))
	dihedraltypes = list(set(dihedraltypes))
	atoms.sort()
	bonds.sort()
	angles.sort()
	dihedrals.sort(key=operator.itemgetter(4, 0, 1, 2, 3))
	atomtypes.sort()
	bondtypes.sort()
	angletypes.sort()
	dihedraltypes.sort(key=operator.itemgetter(4, 0, 1, 2, 3, 7))

	with open(filename, "w") as f:
		f.write("[ atomtypes ]\n")
		f.write(";name    at_no        mass     charge   ptype   sigma         epsilon\n")
		for at in atomtypes:
			f.write(" {:<8s} {:<11s} {:3.5f}  {:3.5f}   A   {:13.5e} {:13.5e}\n".format(
                    at[0], at[0], 0.0, 0.0, at[1], at[2]))
		f.write("\n")

		f.write("[ bondtypes ]\n")
		f.write(";   ai     aj funct   r             k\n")
		for bt in bondtypes:
			f.write("{:>6s} {:>6s} {:3d} {:13.4e} {:13.4e}\n".format(
                    bt[0], bt[1], bt[2], bt[3], bt[4]))
		f.write("\n")

		f.write(" [ angletypes ]\n")
		f.write(";   ai     aj     ak    funct   theta         cth\n")
		for at in angletypes:
			f.write("{:>6s} {:>6s} {:>6s} {:6d} {:13.4e} {:13.4e}\n".format(
                    at[0], at[1], at[2], at[3], at[4], at[5]))
		f.write("\n")

		f.write(" [ dihedraltypes ]\n")
		f.write(";    i      j      k      l   func   phase     kd      pn\n")
		for dt in dihedraltypes:
			f.write("{:>6s} {:>6s} {:>6s} {:>6s} {:5d} {:8.2f} {:8.5f} {:5d}\n".format(
                    dt[0], dt[1], dt[2], dt[3], dt[4], dt[5], dt[6], dt[7]))
		f.write("\n")

		f.write(" [ atoms ]\n")
		f.write(";   id  type  resi  res   atom  cgnr     charge      mass\n")
		for a in atoms:
			f.write("{:>6d} {:>4s} {:>4d}  {:>5s}  {:>5s}  {:>4d}  {:10.6f} {:10.6f}\n".format(
                    a[0], a[1], a[2], a[3], a[4], a[5], a[6], a[7]))
		f.write("\n")

		f.write(" [ bonds ]\n")
		f.write(";   ai     aj funct\n")
		for b in bonds:
			f.write("{:>6d} {:>6d} {:>3d}\n".format(b[0], b[1], b[2]))
		f.write("\n")

		f.write(" [ angles ]\n")
		f.write(";   ai     aj     ak    funct\n")
		for a in angles:
			f.write("{:>6d} {:>6d} {:>6d} {:>6d}\n".format(a[0], a[1], a[2], a[3]))
		f.write("\n")

		f.write(" [ dihedrals ]\n")
		f.write(";    i      j      k      l   func\n")
		for d in dihedrals:
			f.write("{:>6d} {:>6d} {:>6d} {:>6d} {:>4d}\n".format(d[0], d[1], d[2], d[3], d[4]))
		f.write("\n")


parser = argparse.ArgumentParser(description="Gromacs ITP file cleaner v0.1")
parser.add_argument("-i", "--input", help="itp file to clean", required=True,
                    default=None, metavar="<input.itp>", action="store", dest="input")
parser.add_argument("-o", "--output", help="output itp file", required=True,
                    default=None, metavar="<output.itp>", action="store", dest="output")

args = parser.parse_args()

read_itp(args.input)
write_itp(args.output)
