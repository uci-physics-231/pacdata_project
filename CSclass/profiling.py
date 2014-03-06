"""
Test program for profiling and optimization. Program takes about 17s with n = 1e7.

Profile using:
python -m cProfile -o profile.out profiling.py

import pstats
p = pstats.Stats('profile.out')
p.sort_stats('time').print_stats(10)
"""

import random
import math

def generateGaussian():
	return random.gauss(0,1)

def generateRandomList(n):
	# generates and returns a list of random values
	values = [ ]
	for i in range(n):
		values.append(generateGaussian())
	return values

def getMoments(v):
	n = len(v)
	sum = 0.
	sumSq = 0.
	for x in v:
		sum += x
		sumSq += x*x
	mean = sum/n
	rms = math.sqrt(sumSq/n - mean*mean)
	return mean,rms

def run(n):
	v = generateRandomList(n)
	mean,rms = getMoments(v)
	print 'n = %d, mean = %f, rms = %f' % (n,mean,rms)

run(10000000)
