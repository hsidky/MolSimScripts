import argparse 
import numpy as np
from numpy import linalg as la

parser = argparse.ArgumentParser()

parser.add_argument(
	"input",
	help="Input file name",
	type=str
)

parser.add_argument(
	"output",
	help="Output file name",
	type=str
)

args = parser.parse_args()

def roundf(x):
    if x >= 0:
        return np.floor( x + 0.5 )
    else:
        return np.ceil( x - 0.5 )


def apply_min_image(H,x):
    s = np.dot(la.inv(H),x)
    for i in range(0,3):
        s[i] -= roundf(s[i])
    return np.dot(H,s)


with open(args.input, 'r') as fin:
	with open(args.output, 'w') as fout:
		for line in fin:
			# Fist line already skips timestep label.
			fin.next() # Skip timestep
			fin.next() #  Skip atom count label

			# Get particle count
			n = int(fin.next().rstrip()) 

			s = np.zeros((n,), dtype=np.int)
			m = np.zeros((n,), dtype=np.int)
			x = np.zeros((n,3))
			H = np.zeros((3,3))

			fin.next() # Skip box labels.

			# Extract box info.
			xmin, xmax = [float(i) for i in fin.next().split(' ')]
			ymin, ymax = [float(i) for i in fin.next().split(' ')]
			zmin, zmax = [float(i) for i in fin.next().split(' ')]

			# Construct box matrix. 
			H[0,0] = xmax - xmin
			H[1,1] = ymax - ymin
			H[2,2] = zmax - zmin 

			fin.next() # Skip item labels.

			# Loop through atoms 
			for i in range(0,n):        
				si, mi, xi, yi, zi = [float(j) for j in fin.next().rstrip().split(' ')]
				x[i,:] = [xi-xmin, yi-ymin, zi-zmin]
				s[i] = int(si)
				m[i] = int(mi)

			# Sort first by molecule ID then by atom ID
			ind = np.lexsort((m,s)).flatten()
			s = s[ind]
			m = m[ind]
			x = x[ind,:]

			# Long and short axis directors.
			u = np.zeros((n,3))
			v = np.zeros((n,3))

			for mid in np.unique(m):
				ind = np.where(m == mid)[0]

				# Get first, last and middle particles.
				first = ind[0]
				last = ind[-1]
				mid = int(len(ind)/2)+first

				# Get director for long axis.
				ui = apply_min_image(H, x[first,:] - x[last,:])
				ui = ui/la.norm(ui)

				# Get director for short axis
				vi = apply_min_image(H, x[first,:] - x[mid,:])
				vi = vi - ui*np.dot(ui,vi)
				vi = vi/la.norm(vi)

				u[first,:] = ui
				v[first,:] = vi

				# Unwrap positions.
				for i in range(1,len(ind)):
				    j = ind[i-1]
				    k = ind[i]
				    u[k,:] = ui
				    v[k,:] = vi
				    x[k,:] = apply_min_image(H,x[k,:]-x[first,:])+x[first,:]

			fout.write("{0}\n".format(n))
			fout.write('{0} {1} {2}\n'.format(H[0,0], H[1,1], H[2,2]))
			for i in range(n):
				fout.write('P{0} {1} {2} {3} {4} {5} {6} {7} {8} {9}\n'.format(s[i],x[i,0],x[i,1],x[i,2],u[i,0],u[i,1],u[i,2],v[i,0],v[i,1],v[i,2]))
