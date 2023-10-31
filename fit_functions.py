# -*- coding: utf-8 -*-
"""
2023-10-19
@author: Chip Lab

Fitting functions for general analysis scripts 
"""
import numpy as np
import math

def Linear(data):
	"""
	Returns:  m*x + b 
	"""
	guess = None
	param_names = ["m", "b"]
	
	def linear(x, m, b):
		return m*x + b 
	return linear, guess, param_names

def Parabola(data):
	"""
	Returns:  A*(x - x0)**2 + C
	"""
	x_ofmax = data[np.abs(data[:,1]).argmax(),0]
	mean_y = data[:,1].mean()
	max_y = data[:,1].max()
	
	param_names = ["A", "x0", "C"]
	guess = [max_y-mean_y, x_ofmax, mean_y]
	
	def parabola(x, A, x0, C):
		return A*(x - x0)**2 + C
	return parabola, guess, param_names

def Sqrt(data):
	"""
	Returns:  A*np.sqrt(x - x0)
	"""
	min_y = data[:,1].min()
	max_y = data[:,1].max()
	
	param_names = ["A", "x0"]
	guess = [max_y-min_y, 0]
	
	def sqrt(x, A, x0):
		return A*np.sqrt(x-x0)
	return sqrt, guess, param_names

def Gaussian(data):
	"""
	Returns:  A * np.exp(-(x-x0)**2/(2*sigma**2)) + C
	"""
	x_ofmax = data[np.abs(data[:,1]).argmax(),0]
	max_x = data[:,0].max()
	min_x = data[:,0].min()
	mean_y = data[:,1].mean()
	max_y = data[:,1].max()
	
	param_names = ["A", "x0", "sigma", "C"]
	guess = [max_y-mean_y, x_ofmax, (max_x-min_x)/2, mean_y]
	
	def gaussian(x, A, x0, sigma, C):
		return A * np.exp(-(x-x0)**2/(2*sigma**2)) + C
	return gaussian, guess, param_names

def Lorentzian(data):
	"""
	Returns:  A/((x-x0)**2 + (sigma)**2) + C
	"""
	x_ofmax = data[np.abs(data[:,1]).argmax(),0]
	max_x = data[:,0].max()
	min_x = data[:,0].min()
	mean_y = data[:,1].mean()
	max_y = data[:,1].max()
	
	param_names = ["A", "x0", "sigma", "C"]
	guess = [max_y-mean_y, x_ofmax, (max_x-min_x)/2, mean_y]
	
	def lorentzian(x, A, x0, sigma, C):
		return A/((x-x0)**2 + (sigma)**2) + C
	return lorentzian, guess, param_names

def Sin(data):
	"""
	Returns: A*np.sin(omega*x - phi) + C
	"""
	mean_y = data[:,1].mean()
	max_y = data[:,1].max()
	
	param_names = ["A", "omega", "phi", "C"]
	guess = [max_y-mean_y, 1, 0, mean_y]
	
	def sin(x, A, omega, phi, C):
		return A*np.sin(omega*x - phi) + C
	return sin, guess, param_names

def Sinc(data):
	"""
	Returns:   A*np.sinc((x-x0) / sigma) + C
	"""
	x_ofmax = data[np.abs(data[:,1]).argmax(),0]
	max_x = data[:,0].max()
	min_x = data[:,0].min()
	mean_y = data[:,1].mean()
	max_y = data[:,1].max()
	
	param_names = ["A", "x0", "sigma", "C"]
	guess = [max_y-mean_y, x_ofmax, (max_x-min_x)/2, mean_y]
	
	def sinc(x, A, x0, sigma, C):
		return A*(np.sinc((x-x0) / sigma)) + C
	return sinc, guess, param_names

def Sinc2(data):
	"""
	Returns:   A*np.sinc((x-x0) / sigma) + C
	"""
	x_ofmax = data[np.abs(data[:,1]).argmax(),0]
	max_x = data[:,0].max()
	min_x = data[:,0].min()
	mean_y = data[:,1].mean()
	max_y = data[:,1].max()
	
	param_names = ["A", "x0", "sigma", "C"]
	guess = [max_y-mean_y, x_ofmax, (max_x-min_x)/2, mean_y]
	
	def sinc2(x, A, x0, sigma, C):
		return A*(np.sinc((x-x0) / sigma)**2) + C
	return sinc2, guess, param_names


def TrapFreq(data):
	"""
	Returns:  A*np.exp(-x/b)*(np.sin(l * x - x0)) +  C + D*x
	"""
	x_ofmax = data[np.abs(data[:,1]).argmax(),0]
	max_x = data[:,0].max()
	min_x = data[:,0].min()
	mean_y = data[:,1].mean()
	max_y = data[:,1].max()
	
	param_names = ['Amplitude','b','l','Center','Offset','Linear Slope']
	guess = [10000, 0.05, 20  ,-2 , 100, -0.1]
	
	def TrapFreq(x, A, b, l, x0, C, D):
		return A*np.exp(-x/b)*(np.sin(l * x - x0)) +  C + D*x
	return TrapFreq, guess, param_names

def TrapFreq2(data):
	"""
	Returns: A*np.exp(-x/b)*(np.sin(l * x - x0)) +  C 
	"""
	x_ofmax = data[np.abs(data[:,1]).argmax(),0]
	max_x = data[:,0].max()
	min_x = data[:,0].min()
	mean_y = data[:,1].mean()
	max_y = data[:,1].max()
	
	param_names = ['Amplitude','b','l','Center','Offset']
	guess = [10000, 0.05, 20  ,-2 , 100, -0.1]
	
	def TrapFreq2(x, A, b, l, x0, C, D):
		return A*np.exp(-x/b)*(np.sin(l * x - x0)) +  C 
	return TrapFreq2, guess, param_names

def RabiFreq(data):
	"""
	Returns:  A*(np.sin(b/2 * x - x0))**2 + C
	"""
	param_names = ['Amplitdue','b','Center','Offset']
	guess = [1,1,1,0]
	
	def RabiFreq(x, A, b, x0, C):
		return A*(np.sin(b/2 * x - x0))**2 + C
	return RabiFreq, guess, param_names

def Expontial(data):
	"""
	Returns: A*np.exp(-x/sigma)
	"""
	x_ofmax = data[np.abs(data[:,1]).argmax(),0]
	max_x = data[:,0].max()
	min_x = data[:,0].min()
	mean_y = data[:,1].mean()
	max_y = data[:,1].max()
	
	param_names = ['Amplitude','sigma']
	guess = [max_x - min_x, 1]
	
	def Exponential(x, A, sigma):
		return A*np.exp(-x/sigma)
	return Exponential, guess, param_names

def RabiLine(data):
	"""
	Returns:  (b**2 / (l**2 + (x - m)**2 ) ) * (A * np.sin(np.sqrt(s**2 + (x - j)**2 ) * k)**2 + p )
	"""
	param_names = ['b', 'l', 'm', 'A', 's', 'j','k','p']
	guess = [1, 1, 1, 1, 1, 1, 1, 0]
	
	def RabiLine(x, b, l, m, A, s, j, k, p): 
		return (b**2 / (l**2 + (x - m)**2 ) ) * (A * np.sin(np.sqrt(s**2 + (x - j)**2 ) * k)**2 + p )

	return RabiLine, guess, param_names



def ErfcFit(data):
	"""
	Returns:  A * math.erfc((x - x0) / b ) + C
	"""
	param_names =  ['Amp', 'Center', 'b', 'Offset']
	guess = [1, 1, 1, 0]
	
	def ErfcFit(x, A, x0, b, C):
		return A * math.erfc((x - x0) / b ) + C
	
	return ErfcFit, guess, param_names


def SinplusCos(data):
	"""
	Returns:  A*np.sin(omega*t) + B*np.cos(omega*t) + C
	"""
	param_names = ['Sin Amp', 'Cos Amp', 'Offset']
	guess = [1, 1, 1, 0]
	
	def SinplusCos(t, omega, A, B, C):
		return A*np.sin(omega*t) + B*np.cos(omega*t) + C

	return SinplusCos, guess, param_names

def FixedSin(data):
	"""
	hard coded 10 kHz
	Returns: A*np.sin(0.0628*x - p) + C
	"""
	param_names =  ['Amplitude','phase','offset']
	guess = [1, 1, 0]
	
	def FixedSin(t, A, p, C):
		omega = 0.010 * 2 * np.pi # 10 kHz
		return A*np.sin(omega*t - p) + C
	
	return FixedSin, guess, param_names

def FixedSin5kHz(data):
	"""
	hard coded 5 kHz
	Returns: A*np.sin(0.0314*x - p) + C
	"""
	param_names =  ['Amplitude','phase','offset']
	guess = [1, 1, 0]
	
	def FixedSin5kHz(t, A, p, C):
		omega = 0.005 * 2 * np.pi # 5 kHz
		return A*np.sin(omega*t - p) + C
	
	return FixedSin5kHz, guess, param_names