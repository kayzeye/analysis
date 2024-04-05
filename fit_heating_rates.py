# -*- coding: utf-8 -*-
"""
@author: Chip Lab

Fits heating rates from unitary_expansion_analysis.m output .dat files.
Fit results are compiled and stored as a Dataframe in a pkl file for later 
analysis or plotting, and a xlsx for viewing.

Datasets must be placed in the heating data folder, and a metadata row
needs to be filled in the heating_metadata.xlsx sheet. 

Multiscans and double multiscans are handled by looking for ms_param and 
ms_param2 names in the metadata file. Those are stored in the output to be used
for data sorting after fitting.

New files can be analyzed and added to the pickled DataFrame and xlsx by
just analyzing the new files.

Relies on data_class.py, library.py

WARNING: The saved DataFrame will not be updated correctly with new analysis if 
there are any empty DataFrame entries in the new "update" DataFrame. I'm not 
sure how to get around this. Currently, this analysis file does not produce
any DataFrame rows that have empty cells, so this shouldn't be an issue.
"""
from data_class import Data
from library import *
from scipy.optimize import curve_fit
from itertools import chain
from matplotlib import cm

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt 
import os
import pickle

### files and paths
data_folder = 'data\\heating'
pkl_filename = 'heating_rate_fit_results.pkl'
pkl_file = os.path.join(data_folder, pkl_filename)
xlsx_results_filename = 'heating_data_results.xlsx'
xlsx_results_file = os.path.join(data_folder, xlsx_results_filename)
metadata_filename = 'heating_metadata.xlsx'
metadata_file = os.path.join(data_folder, metadata_filename)

### load metadata
metadata = pd.read_excel(metadata_file)

### script options
plotting = True
save = True

# only fit data up to max time in ms
max_time = 120

# class attributes to delete after analysis, before storage
del_attr = ['data', 'avg_data', 'fit_func', 'popt', 
			'pcov', 'err', 'poptT', 'pcovT', 'errT', 
			'poptEF', 'pcovEF', 'errEF', 'poptToTF', 
			'pcovToTF', 'errToTF','poptN', 'pcovN', 
			'errN', 'label', 'res_label', 'exclude']

# will only plot up to length of this list. Add more colors to plot more.
colors = ["blue", "red", "green", "orange", 
		  "purple", "black", "pink", "brown"]

##############################################
#### add list of files to analyze here #######
##############################################

# this selects all files that are not excluded e.g. have exclude = 0
files =  metadata.loc[metadata['exclude'] == 0]['filename'].values

# or select files manually, e.g. files = [filename1, filename2, ...]
files = ["2024-04-04_C_UHfit"]

# initialize list of runs to fill
runs = []

# convert metadata into dict of dicts
metadata = metadata.set_index('filename')
metadata = metadata.to_dict(orient='index')

#####
##### Field wiggle calibrations
#####

# freqs = [10, 10, 1, 2.5, 10, 5] # kHz
# Vpps = [0.4, 0.9, 0.9, 0.9, 1.0, 1.8] # 50 Ohm term
# fieldAmps = [0.021, 0.048, 0.01, 0.018, 0.054, 0.070] # fit amplitudes in Gauss
# e_fieldAmps = [0.002, 0.004, 0.001, 0.002, 0.001, 0.003] # fill
# e_fieldAmp = 2e-3 # estimated as 2 mG

# Bamp_per_Vpp = {1:None,2.5:None,5:None,10:None} # dict to loop and fill below
# for freq, val in Bamp_per_Vpp.items():
# 	# compute average scaled by Vpp if multiple calibrations at the same freq
# 	val_avg = np.mean([fieldAmps[i]/Vpps[i] for i in range(len(freqs)) if freqs[i] == freq])
# 	err_avg = np.mean([e_fieldAmps[i]/Vpps[i] for i in range(len(freqs)) if freqs[i] == freq])
# 	Bamp_per_Vpp[freq] = [val_avg, err_avg]

# def Bamp_from_Vpp(Vpp, freq):
# 	''' Returns Bamp and e_Bamp in an array '''
# 	key = int(freq)
# 	if key > 10: # if frequency is above 10 kHz, all cals the same
# 		key = 10
# 	return np.array(Bamp_per_Vpp[key]) * Vpp

# fit to 0.9Vpp field wiggle calibration data a 2024-04-01
WiggleCalpopt = [ 7.42905865e-02, -1.13381420e+01,  3.64847614e-03]
WiggleCalerr = [1.59511844e-03, 7.35920688e-01, 6.22923408e-04]
def exponential(x, a, b, c):
	return a*(1-np.exp(x/b))+c

def Bamp_from_Vpp(Vpp, freq):
	''' Returns Bamp and e_Bamp in an array '''
	Bamp = Vpp * exponential(freq,*WiggleCalpopt)/0.9
	# the below is wrong
	e_Bamp = 0
	return  Bamp, e_Bamp
	
#####
##### Trap frequency calibrations
#####

### 2024-03-06
## ODTs = 0.2/4
wx = 169.1 # Hz
wy = 453#429#*np.sqrt(2)
wz = 441#442#*np.sqrt(2)
mean_trapfreq = 2*pi*(wx*wy*wz)**(1/3)

### functions for use in this script
def linear(x, m, Ei):
	return m*x + Ei

def find_A(T, Bamp, e_T, e_Bamp):
	''' Returns A and e_A '''
	B0 = 202.14
	A = deBroglie(T)/a97(B0-Bamp)
	e_a97 = np.abs(a97(B0-Bamp) - a97(B0-Bamp+e_Bamp))
	e_dB = np.abs(deBroglie(T) - deBroglie(T+e_T))
	e_A = A*np.sqrt((e_a97/a97(B0-Bamp))**2 + (e_dB/deBroglie(T))**2)
	return A, e_A

# read description!!!
def fix_attribute(run, attr, attr_names):
	""" .... okay so like, if you're trying to generalize over multiscans, 
		you need to get the freq or amplitude from the .dat file, and use that 
		for analysis. That's what this does. It checks if those are not in the 
		metadata, and if they are't (i.e. they're nan) then it fills that attr
		with an entry from the .dat file, trying a list of names. """
	if getattr(run, attr) != getattr(run, attr): # nan check
		for name in attr_names:
			try:
				setattr(run, attr, run.data[name].values[0])
				break
			except KeyError:
				if name != attr_names[-1]:
					continue

### fitting and parameter calculation functions
### both take class as input, modify class, then return the same class
def fit_analysis(run):
	""" takes Data class run, fits computes some stuff, then returns class"""
	# fit energy to fit function
	run.fit_func = settings['fit']
	
	run.popt, run.pcov = curve_fit(run.fit_func, run.avg_data[run.param], 
						run.avg_data[settings['temp_param']], 
						sigma = run.avg_data['em_'+settings['temp_param']])
	run.err = np.sqrt(np.diag(run.pcov))
	run.dof = len(run.avg_data.index) - len(run.err) # num data - num params in the fit
	
	try:
		run.chi_sq = chi_sq(run.avg_data[settings['temp_param']], 
					run.fit_func(run.avg_data[run.param], *run.popt), 
					run.avg_data['em_'+settings['temp_param']], run.dof)
	except ZeroDivisionError:
		print("dof = 0, so no chi^2 to calculate.")
		run.chi_sq = 1

	# fit ToTF to get offset
	run.poptToTF, run.pcovToTF = curve_fit(run.fit_func, run.avg_data[run.param], 
						run.avg_data['ToTF'], 
						sigma = run.avg_data['em_'+'ToTF'])
	run.errToTF = np.sqrt(np.diag(run.pcovToTF))
	run.ToTF = run.poptToTF[1]
	run.e_ToTF = run.errToTF[1]
	
	# fit EF to get offset
	run.poptEF, run.pcovEF = curve_fit(run.fit_func, run.avg_data[run.param], 
						run.avg_data['EF'], 
						sigma = run.avg_data['em_'+'EF'])
	run.errEF = np.sqrt(np.diag(run.pcovEF))
	run.EF = run.poptEF[1]/h/1e3
	run.e_EF = run.errEF[1]/h/1e3
	
	# fit T to get offset
	run.poptT, run.pcovT = curve_fit(run.fit_func, run.avg_data[run.param], 
						run.avg_data['T'], 
						sigma = run.avg_data['em_'+'T'])
	run.errT = np.sqrt(np.diag(run.pcovT))
	run.T = run.poptT[1]
	run.e_T = run.errT[1]
	
	# fit N to get offset
	run.poptN, run.pcovN = curve_fit(run.fit_func, run.avg_data[run.param], 
						run.avg_data['N'], 
						sigma = run.avg_data['em_'+'N'])
	run.errN = np.sqrt(np.diag(run.pcovN))
	run.N = run.poptN[1]
	run.e_N = run.errN[1]
	run.loss_rate = run.poptN[0]/run.N
	run.e_loss_rate = run.loss_rate*np.sqrt((run.e_N/run.N)**2 + (run.poptN[0]/run.errN[0])**2)

	# calculate other run params and errors
	run.Bamp, run.e_Bamp = Bamp_from_Vpp(run.Vpp, run.freq)
	run.A, run.e_A = find_A(run.T, run.Bamp, run.e_T, run.e_Bamp)
	run.e_A2 = 2*run.A*run.e_A
	run.Ei = run.popt[1]
	run.e_Ei = run.err[1]
	run.heating = run.popt[0]/run.Ei
	# careful with correlated errors
	run.e_heating = run.heating*np.sqrt((run.err[0]/run.popt[0])**2 \
			   +(run.err[1]/run.popt[1])**2 - 2*run.pcov[0,1]/run.popt[0]/run.popt[1])
	run.rate = run.heating * 1000/run.A**2
	run.e_rate = run.rate*np.sqrt((run.e_heating/run.heating)**2+(run.e_A2/run.A**2)**2)

def analysis_for_dof_equals_two(run):
	"""For use when dof = 2, i.e. you can't fit."""
	# dumbest shit I've ever written
	df1 = run.avg_data.loc[run.avg_data[run.param] == run.avg_data[run.param].min()]
	df2 = run.avg_data.loc[run.avg_data[run.param] == run.avg_data[run.param].max()]
	
	run.ToTF = float(df1.ToTF)
	run.e_ToTF = float(df1.em_ToTF)
	run.EF = float(df1.EF)/h/1e3
	run.e_EF = float(df1.em_EF)/h/1e3
	run.T = float(df1['T']) # .T is the transpose operation... LOL
	run.e_T = float(df1.em_T)
	run.Ei = float(df1[settings['temp_param']])
	run.e_Ei = float(df1['em_'+settings['temp_param']])
	Ef = float(df2[settings['temp_param']])
	e_Ef = float(df2['em_'+settings['temp_param']])
	run.N = float(df1.N)
	run.e_N = float(df1.em_N)
	Nf = float(df2.N)
	e_Nf = float(df2.em_N)
	
	run.Bamp, run.e_Bamp = Bamp_from_Vpp(run.Vpp, run.freq)
	run.A, run.e_A = find_A(run.T, run.Bamp, run.e_T, run.e_Bamp)
	run.e_A2 = 2*run.A*run.e_A
	
	# rise over run...
	deltax = float(df2[run.param])-float(df1[run.param])
	deltay = Ef/run.Ei - 1
# 	deltay = Ef-run.Ei
	
	run.heating = deltay/deltax 
	run.e_heating = Ef/run.Ei/deltax * np.sqrt((e_Ef/Ef)**2 + (run.e_Ei/run.Ei)**2)
	
# 	run.e_heating = np.sqrt((e_Ef)**2 + (run.e_Ei)**2)
	
	run.rate = run.heating * 1000/run.A**2
	run.e_rate = run.rate*np.sqrt((run.e_heating/run.heating)**2+(run.e_A2/run.A**2)**2)
	# I think this is done right... plz check.
		
	run.loss_rate = (Nf-run.N)/deltax/run.N
	run.e_loss_rate = Nf/run.N/deltax * np.sqrt((e_Nf/Nf)**2 + (run.e_N/run.N)**2)
		
	run.dof = 0
	run.chi_sq = 1

############## FITTING ##############

# analysis options
settings = {'param':'time',
			'temp_param':'meanEtot_kHz',
			'xlabel':'Time (ms)',
			'fit':linear,
			'files':files}

# loop over files, split into runs if they are multiscans
for file in files:
	dat = Data(file+".dat", path = data_folder, metadata=metadata[file])
	print("Fitting data from {}".format(dat.filename))
	
	# default to no multicans
	multiscan = False
	multiscan2 = False
	run_param_sets = [0,0] # dummy, only one loop per file
	
	# check for multiscan
	if dat.ms_param == dat.ms_param: # nan check
		multiscan = True
		print("Found multiscan param: {}".format(dat.ms_param))
		ms_vals = dat.data[dat.ms_param].unique()
		
		run_param_sets = [[ms_val] for ms_val in ms_vals] # number of loops
		
		# check for double multiscan
		if dat.ms_param2 == dat.ms_param2: # nan check
			multiscan2 = True
			print("Found 2nd multiscan param: {}".format(dat.ms_param2))
			run_param_sets = []
			for ms_val in ms_vals:
				# find multiscan 2 values for each multiscan 1 value
				ms2_vals = dat.data.loc[dat.data[dat.ms_param] == ms_val][dat.ms_param2].unique()
				# stuff pairs of multiscan values in list to loop over
				for ms2_val in ms2_vals:
					run_param_sets.append([ms_val, ms2_val]) # number of loops
	
	# loop over multiscan param pairs, if they exist
	for run_params in run_param_sets:
		# reload the .dat file, required when using drop, as we do below
		run = Data(file+".dat", path = data_folder, metadata=metadata[file])
			
		if multiscan: # then print multiscan value, and only keep relevant df portion
			print("{} = {}".format(dat.ms_param, run_params[0]))
			run.data = run.data.drop(run.data[run.data[run.ms_param]!=run_params[0]].index)
		else: # required to have saved DataFrame update correctly, can't leave blank.
			run.ms_param = 'nope'
		if multiscan2:
			print("{} = {}".format(dat.ms_param2, run_params[1]))
			run.data = run.data.drop(run.data[run.data[run.ms_param2]!=run_params[1]].index)
		else:
			run.ms_param2 = 'nada'
			
		# take out long time data if we want to
		run.data = run.data.drop(run.data[run.data[run.param]>max_time].index)
		
		# make sure there isn't a repeated point at the end of the file
		# FILL
		
		# calculate correct energy from Will's code output
		run.data[settings['temp_param']] = run.data['ENoEF'] * run.data['EF']/1000/h
		
		# average data
		run.group_by_mean(run.param)
		
		# find attributes needed for analysis that were not in metadata
		# because they change during scan, and weren't written in metadata file
		fix_attribute(run, 'freq', ['freq', 'wigglefreq', 'wiggle freq'])
		fix_attribute(run, 'Vpp', ['Vpp', 'amp', 'amplitude'])
		
		if run.date < pd.Timestamp(2024,3,1):
			run.Vpp = run.Vpp/2 # we had a funny setting on func. gen.
		
		# if it's just a run with two values... then dof = 0 so we have to 
		# do some calculations of rates without fitting
		if len(run.avg_data.index) == 2:
			analysis_for_dof_equals_two(run)
			
		else: # we just do linear fits
			fit_analysis(run)
			
		try:
			run.beta = run.avg_data['beta'].values[0]
		except KeyError: # if old .dat file, then there is no beta, so beta
# 			print("This must be an old .dat file, adding old beta value")
			run.beta = 1.8339e-05
	
		# make a legend label for this run, assumes typical sig figs
		run.label = "$B_{{amp}}=${:.0f}({:.0f}) mG, $f=${:.0f} kHz, $T/T_F=${:.2f}({:.0f}), $E_F=${:.1f}({:.0f}) kHz".format(
					   run.Bamp*1e3, run.e_Bamp*1e3, run.freq, run.ToTF, 
					      run.e_ToTF*1e2, run.EF, run.e_EF*1e1)
		run.res_label = r"$\chi^2=${:.2f}".format(run.chi_sq)
		
		run.date = run.date.strftime('%Y-%m-%d')
		
		# label for run in results file, will be unique
		# format e.g. "B_2024-03-31_f=10_Vpp=0.5"
		run.name = "{}_{}_f={:.0f}_Vpp={:.2f}".format(run.date, run.run,
												run.freq, run.Vpp)
		
		# put run class into list, for later plotting and saving
		runs.append(run)

############## PLOTTING ##############		
if plotting == True:
	### matplotlib options
	plt.rcParams.update({"figure.figsize": [14,7]})
	fig, axs = plt.subplots(2,3)
	num = 500
	font = {'size'   : 12}
	plt.rc('font', **font)
	legend_font_size = 9 # makes legend smaller, so plot is visible
			
	###
	### Heating rate data, fit
	###
	ax = axs[0,0]
	xlabel = settings['xlabel']
	ylabel = "Energy (kHz)"
	ax.set(xlabel=xlabel, ylabel=ylabel)
	
	### loop over runs, plotting fits
	max_plots = len(colors)
	if len(runs) > max_plots: # check if we are ignoring some fits when plotting
		print("Only showing {} datasets. Add more colors, ".format(max_plots))
		print("or reduce the number of runs to fit.")
	for run, color in zip(runs, colors): 
		xx = np.array(run.avg_data[settings['param']])
		yy = np.array(run.avg_data[settings['temp_param']])
		yerr = np.array(run.avg_data['em_'+settings['temp_param']])
		
		ax.errorbar(xx, yy, yerr=yerr,
			  label=run.label, color=color, capsize=2,
			   fmt='o')
		
		xx = np.array(run.avg_data[settings['param']])
		yy = np.array(run.avg_data[settings['temp_param']])
		if len(xx) == 2: # if no fit, then just connect the two points
			ax.plot(xx, yy, color=color, linestyle='--')
		else:
			xlist = np.linspace(xx.min(), xx.max(), num)
			ax.plot(xlist, run.fit_func(xlist, *run.popt), color=color, linestyle='--')

	###
	### Residuals
	###
	ax = axs[1,0]
	xlabel = settings['xlabel']
	ylabel = "Residual Energy (kHz)"
	ax.set(xlabel=xlabel, ylabel=ylabel)
	
	# zero line
	ax.plot(xlist, np.zeros(num), color='k', linestyle='--')
	
	# residuals
	for run, color in zip(runs, colors):
		xx = np.array(run.avg_data[settings['param']])
		yy = np.array(run.avg_data[settings['temp_param']])
		yerr = np.array(run.avg_data['em_'+settings['temp_param']])
		if len(xx) == 2: # no fit, no residual
			continue 
		residuals =  yy - run.fit_func(xx, *run.popt)
		ax.errorbar(xx, residuals, yerr=yerr, label=run.res_label, color=color, 
			  capsize=2, fmt='o')
		
	###
	### ToTF
	###
	ax = axs[0,1]
	xlabel = settings['xlabel']
	ylabel = r"$T/T_F$"
	ax.set(xlabel=xlabel, ylabel=ylabel)
	
	# loop over runs, plotting fits
	for run, color in zip(runs, colors):
		xx = np.array(run.avg_data[settings['param']])
		yy = np.array(run.avg_data['ToTF'])
		yerr = np.array(run.avg_data['em_'+'ToTF'])
		
		ax.errorbar(xx, yy, yerr=yerr,label=run.label, color=color, capsize=2, fmt='o')
		
		if len(xx) == 2:
			ax.plot(xx, yy, color=color, linestyle='--')
		else:
			xlist = np.linspace(xx.min(), xx.max(), num)
			ax.plot(xlist, run.fit_func(xlist, *run.poptToTF), color=color, linestyle='--')
		
	###
	### EF
	###
	ax = axs[1,1]
	xlabel = settings['xlabel']
	ylabel = r"$E_F$ (kHz)"
	ax.set(xlabel=xlabel, ylabel=ylabel)
	
	# loop over runs, plotting fits
	for run, color in zip(runs, colors):
		xx = np.array(run.avg_data[settings['param']])
		yy = np.array(run.avg_data['EF']/1e3/h)
		yerr = np.array(run.avg_data['em_'+'EF']/h/1e3)
		
		ax.errorbar(xx, yy, yerr=yerr,label=run.label, color=color, capsize=2, fmt='o')
		
		if len(xx) == 2:
			ax.plot(xx, yy, color=color, linestyle='--')
		else:
			xlist = np.linspace(xx.min(), xx.max(), num)
			ax.plot(xlist, run.fit_func(xlist, *run.poptEF)/h/1e3, color=color, linestyle='--')
	
	###
	### N
	###
	ax = axs[0,2]
	xlabel = settings['xlabel']
	ylabel = r"$N$ (atom no.)"
	ax.set(xlabel=xlabel, ylabel=ylabel)
	
	# loop over runs, plotting fits
	for run, color in zip(runs, colors):
		xx = np.array(run.avg_data[settings['param']])
		yy = np.array(run.avg_data['N'])
		yerr = np.array(run.avg_data['em_'+'N'])
		
		ax.errorbar(xx, yy, yerr=yerr,label=run.label, color=color, capsize=2, fmt='o')
		
		if len(xx) == 2:
			ax.plot(xx, yy, color=color, linestyle='--')
		else:
			xlist = np.linspace(xx.min(), xx.max(), num)
			ax.plot(xlist, run.fit_func(xlist, *run.poptN), color=color, linestyle='--')
		
	###
	### Legend in own subplot
	###
	lax = axs[1,2]
	h, l = axs[0,0].get_legend_handles_labels() # get legend from first plot
	lax.legend(h, l, borderaxespad=0, prop={'size':legend_font_size})
	lax.axis("off")
	
	fig.tight_layout()
	plt.show()
# 	fig.savefig('heating_rate_data.pdf')

############ SAVE RESULTS ############	
if save == True:
	save_results = pd.DataFrame() # df for storing results, to be pickled
	for run in runs:
		results = vars(run) # makes dict out of class attribues, this gives me goosebumps
		
		# delete attributes from dict results that you don't want to save
		for attr in del_attr:
			results.pop(attr, None) # None in case of key error
		
		# stuff result (dict) in dataframe OH YEAH BABY
		save_results = save_results.append(results, ignore_index=True)
	
	# set index as name
	save_results = save_results.set_index('name')
	try: # open pkl file if it's there
		with open(pkl_file, 'rb') as f:
			loaded_results = pickle.load(f) # load all results in file
			# update index, then rows of loaded df
			loaded_results = loaded_results.reindex(loaded_results.index.union(save_results.index))
			loaded_results.update(save_results)
		with open(pkl_file, 'wb') as f:
			pickle.dump(loaded_results, f)  # write new pkl file
			loaded_results.to_excel(xlsx_results_file)
	except FileNotFoundError: # if file not there then make it
		with open(pkl_file, 'wb') as f:
			pickle.dump(save_results, f)
			save_results.to_excel(xlsx_results_file)