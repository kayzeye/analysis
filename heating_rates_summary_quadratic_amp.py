# -*- coding: utf-8 -*-
"""
@author: Chip Lab

Plots data fitted in heating_rates_fitting.py and theory lines from modified
Tilman code bulkvisctrap_class.py.

Relies on data_class.py, library.py, and bulkvisctrap_class.py
"""
from data_class import Data
from library import *
from bulkvisctrap_class import BulkViscTrap, BulkViscTrapToTF
from itertools import chain
from matplotlib import cm
from scipy.optimize import curve_fit

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt 
import os
import pickle

data_folder = 'data\\heating'
pkl_filename = 'heating_rate_fit_results.pkl'
pkl_file = os.path.join(data_folder, pkl_filename)

plotting = True
debugging_plots = False
plot_legend = True

def quadratic(x, a, b):
	return a*x**2 + b

def linear(x, a, b):
	return a*x + b

colors = ["blue", "red", "green", "orange", 
		  "purple", "black", "pink", "brown"]

markers = ["o", "s", "^", "D", "h"]

############ LOAD DATA ############
try: # open pkl file if it's there
	with open(pkl_file, 'rb') as f:
		lr = pickle.load(f) # load all results in file
except FileNotFoundError: # if file not there then complain
	print("Can't find data results pickle file, you silly billy.")
	
### select the data
amp_data = lr.loc[(lr.ms_param == 'amplitude') | (lr.ms_param2 == 'amplitude')]

############## PLOTTING ##############		
# change matplotlib options
plt.rcParams.update({"figure.figsize": [8,8]})
fig, axs = plt.subplots(2,1)
num = 500
font = {'size'   : 12}
plt.rc('font', **font)
legend_font_size = 10 # makes legend smaller, so plot is visible

### plot	
ax = axs[0]
ylabel = "Scaled Heating Rate $\partial_t E/E/A^2$ (Hz)"
ylabel = "Scaled Heating Rate $\partial_t E/E$ (Hz)"
xlabel = "Amplitude of Drive"
ax.set(ylabel=ylabel, xlabel=xlabel)

ax_res = axs[1]
ylabel = "Residual Heating Rate (Hz)"
ax_res.set(ylabel=ylabel, xlabel=xlabel)

# amp_data = amp_data.drop(amp_data.loc[amp_data.freq!=5].index)

for freq, color in zip(amp_data.freq.unique(), colors):
	df = amp_data.loc[amp_data.freq==freq]
	
# 	df = df.drop(df.loc[df.A>0.4].index)
	
	xx = np.array(df["A"])
	yy = np.array(df["heating"])
	yerr = np.array(df["e_heating"]) 
	
	label = r"$f=${:.0f} kHz".format(freq)
	
	popt, pcov = curve_fit(quadratic, xx, yy, sigma=yerr)
	perr = np.sqrt(np.diag(pcov))
	
	popt2, pcov2 = curve_fit(linear, xx, yy, sigma=yerr)
	perr2 = np.sqrt(np.diag(pcov2))
	
	ax.errorbar(xx, yy, yerr=yerr, fmt='o', capsize=2, color=color, label=label)
	xlist = np.linspace(0, max(xx), num)
	ax.plot(xlist, quadratic(xlist, *popt), '-', color=color)
	ax.plot(xlist, linear(xlist, *popt2), '--', color=color)
	
	ax_res.errorbar(xx, yy- quadratic(xx, *popt), yerr, fmt='o', capsize=2, 
				  color=color)
	ax_res.plot(xx,np.zeros(len(xx)), 'k--')

ax.legend()
plt.show()

