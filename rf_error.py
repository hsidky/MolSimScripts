# rf_error.py: Calculate the error in the transmission coefficient.
import numpy
## FORMULA:
# sigmakappa**2 = kappa*((sigmaA/A)**2+(sigmaB/B)**2)-2Cov(A,B)/(A*B)

# Load in A and B
afile = open('databc2num', 'r')
bfile = open('databc2den', 'r')

	
