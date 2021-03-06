# -*- coding: utf-8 -*-
"""CSTR.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1lyIDawlw9DpC_gEyIZSlSm3hWnwLpkGY

#Importing Libraries
"""

import numpy as np
import pandas as pd
import keras
import tensorflow as tf
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout, InputLayer
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
from scipy.interpolate import CubicSpline
from scipy import signal
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split 
from sklearn.preprocessing import PolynomialFeatures, MinMaxScaler
import pdb

q = 100            # L/min
Ti = 350           # K
cA_i = 1           # mol/L
V = 100            # L
rho = 1000         # g/L
C = 0.239          # J/(g K)
Hr = -5e4          # J/(g K)
E_over_r = 8750    # K
k0 = 7.2e10        # min^(-1)
UA = 5e4           # J/(min K)
Tc = Tc0 = 300     # K

# simulation run time: 60 min (1 hr)

tspan = (0, 60)
t = np.linspace(*tspan, 1000)

# Add steady state values

Ca0 = 0.5    #mol/L
T0 = 350.0   #K

# pdb.set_trace()

# Generating a noise array
length = len(t)
noise = 0.001*np.random.randn(length)

# defining the reactor model
def simulation_model(t,x):
    Ca = x[0]
    T = x[1]
    k = k0*np.exp(-E_over_r/T)
    w = q*rho
    dcAdt = q*(cA_i - Ca)/V - k*Ca
    dTdt = 1/(V*rho*C)*(w*C*(Ti - T) - Hr*V*k*Ca + UA*(Tc - T))
    return dcAdt, dTdt

# Initial Conditions
y0 = [Ca0, T0]

simulation_model(0,y0)

def simulate():
    res = solve_ivp(simulation_model, tspan, y0, t_eval=t)
    return res.y


#cA = res
#T = res
#print(cA,T)

Ca,T = simulate()

plt.plot(t, T, 'g.')
plt.ylabel('Temp (K)')
plt.xlabel("time (min)")  
plt.grid()
plt.show()

plt.plot(t, Ca, 'r.')
plt.ylabel('Conc (mol/L)')
plt.xlabel("time (min)")  
plt.grid()
plt.show()

plt.plot(T, Ca, 'b.')
plt.ylabel('Conc (mol/L)')
plt.xlabel("temp (K)")  
plt.grid()
plt.show()

# Concentartion after adding noise
conc = Ca + noise
temp = T + noise
print(Ca)
print(conc.ndim)
print(t.ndim)
#Extracting Independent and dependent Variable  
x1= t
y1= conc
#import pdb
#pdb.set_trace()
x2 = x1.reshape(-1,1)



#Fitting the Polynomial regression to the dataset
x_ = PolynomialFeatures(degree=3, include_bias=False).fit_transform(x2)
model = LinearRegression().fit(x_, y1)
intercept, coefficients = model.intercept_, model.coef_
y_pred = model.predict(x_)

r_sq = model.score(x_, y1)
print(r_sq)
#model = LinearRegression().fit(x2, y1)
#y_pred = model.intercept_ + model.coef_ * x2
#y_new = model.predict(x1)
# Construct results and save data file
#data = np.vstack((t,Caf,Ca,T)) # vertical stack
#data = data.T             # transpose data
#np.savetxt('data.txt',data,delimiter=',')

# Computing MAE between the simulated data and the noise-added data
print('MAE of the simulation is (using regression) ' + str(np.round(mean_absolute_error(conc, y_pred), 5)))

cs = CubicSpline(t, conc)
cs1 = CubicSpline(t, temp)
conc_new = cs(x2)
temp_new = cs1(x2)

"""Do moving avg first then use cubic spline"""

def moving_average(temp_avg, w):
    return np.convolve(temp_avg[:,0], np.ones(w), 'valid') / w

def moving_average(conc_avg, w):
    return np.convolve(conc_avg[:,0], np.ones(w), 'valid') / w

def moving_average(t_avg, w):
    return np.convolve(t_avg[:,0], np.ones(w), 'valid') / w


# print(moving_average(temp_new, 5))
pd.DataFrame(moving_average(temp_new, 5)).plot()
pd.DataFrame(moving_average(conc_new, 5)).plot()

conc_avg = moving_average(conc_new, 5)
temp_avg = moving_average(temp_new, 5)
print(t.shape)
print(temp_avg.shape)
print(conc_avg.shape)
t_avg = moving_average(t.reshape(-1,1), 5)

# Plot the inputs and results
#plt.plot(t,Ca,'r-',label='Ca')
#plt.plot(t_sys,Ca_sys,'g--',label='Ca (State Space)')

#plt.legend(loc='best')
#plt.grid()

#print(t)
#print(conc)
# t2 = t_avg.reshape(-1,1)

# t_avg = np.ma.masked_equal(t2,0)
#conc_avg = np.ma.masked_equal(conc_avg,0)
#temp_avg = np.ma.masked_equal(temp_avg,0)

#Visulaizing the result for Polynomial Regression  
#plt.plot(t_sys,conc,'b--', markersize=2, label='Ca (with noise- simul)')
#plt.plot(x2, y_pred, color="orange")
#plt.plot(t2, conc_avg, color="violet")
# plt.plot(t,conc,'bo', markersize=2, label='Ca (with noise- simul)')

plt.plot(t,Ca,'bo', markersize=2)
plt.plot(t_avg,conc_avg,'k-', markersize=2)
plt.ylabel('Conc (mol/L)')
plt.xlabel("time (min)")  
plt.grid()

plt.show()

plt.plot(t,temp,'ro', markersize=2, label='Ca (with noise- simul)')
plt.plot(t_avg,temp_avg,'k-', markersize=2)
plt.ylabel('Temperature (K)')
#plt.title("(Polynomial Regression)")  
plt.xlabel("time (min)")  
#plt.ylabel("conc")
plt.grid()

plt.show()

pd.DataFrame(temp_avg).plot()

temp_avg

xscaler = MinMaxScaler()
yscaler = MinMaxScaler()

X = xscaler.fit_transform(temp_avg.reshape(temp_avg.shape[0], 1))
Y = yscaler.fit_transform(conc_avg.reshape(conc_avg.shape[0], 1))

print(xscaler.data_min_)

pd.DataFrame(X).describe()

d = pd.DataFrame(temp_avg, columns=["T"])
d[d["T"] == 0].count()

# # inputs and outputs
# x_in = pd.DataFrame(np.array(temp_avg), columns=["T"])        # input: the simulation time series
# x_out = pd.DataFrame(np.array(conc_avg), columns=["C"])   # output: difference between measurement and simulation

# split into train-test set
x_train, x_test, y_train, y_test= train_test_split(X, Y, test_size= 0.33, random_state=1)  

# x_train = x_train.reshape(x_train.shape + (1,))
# y_train = y_train.reshape(y_train.shape + (1,))

# x_test = x_test.reshape(x_test.shape + (1,))
# y_test = y_test.reshape(y_test.shape + (1,))

# check shapes
print('shape of X_train is: ' + str(x_train.shape) + '; shape of y_train is: ' + str(y_train.shape))
print('shape of Y_test is: ' + str(y_test.shape) + '; shape of y_test is: ' + str(y_test.shape))

df1 = pd.DataFrame(x_train).describe()
print(df1)
ax1 = df1.plot()

df2 = pd.DataFrame(y_train).describe()
print(df2)
ax2 = df2.plot()

# making a simple neural network model
model = Sequential()
model.add(Dense(64, activation='relu'))
model.add(Dense(64, activation='relu'))
model.add(Dense(1))

epochs = 100
loss = "mse"
model.compile(optimizer='adam',
              loss=loss,
              metrics=['mae'], #Mean Absolute Error
             )
history = model.fit(x_train, y_train, 
                    shuffle=True, 
                    epochs=epochs,
                    batch_size=20,
                    validation_split =.2, 
                    verbose=2)

model.summary()

plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])

history.history

result = model.predict(x_test)
# X:      0 2 1 8 9
# Y:       2 3 4 5 6
# Y_pred:  1 2 3 4 5

result_unscaled = yscaler.inverse_transform(result)
y_test_unscaled = yscaler.inverse_transform(y_test)
x_test_unscaled = yscaler.inverse_transform(x_test)
#pd.DataFrame(result_unscaled - y_test_unscaled).abs().describe()

pd.DataFrame(result_unscaled - y_test_unscaled).abs().hist(color='#607c8e', grid=True)
plt.title('Concentration Prediction error')
plt.xlabel('delta (y_predicted - y_test)')
plt.ylabel('count')
plt.grid(axis='y', alpha=0.75)
#plt.plot([i for i in range(len(result_unscaled))], result_unscaled, y_test_unscaled)

res = pd.DataFrame(result_unscaled - y_test_unscaled)
import seaborn as sns
sns.set_style("whitegrid")
sns.boxplot(data = res)

model.evaluate(x_test,  y_test, verbose=2)

mean_absolute_error(y_test_unscaled, result_unscaled)

# RMSE
mean_squared_error(y_test_unscaled, result_unscaled)
np.sqrt(mean_squared_error(y_test_unscaled, result_unscaled))

# R-squared
r2_score(y_test_unscaled, result_unscaled)

print(history.history.keys())

plt.plot(history.history['mae'])
plt.ylabel('mae')
plt.xlabel('epoch')
plt.legend(['train'], loc='best')
plt.show()

plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('model loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'validation'], loc='best')
plt.show()

plt.plot(temp_avg, conc_avg)
plt.title('CSTR concentration vs. temperature plot')
plt.ylabel('conc (mol/L)')
plt.xlabel('temp (K)')
plt.show()

#plt.plot(temp_avg, conc_avg, 'r.')
plt.plot(x_train, y_train, 'b.')
plt.plot(x_test, result, 'r*')
print(x_test_unscaled.ndim)
print(temp_avg.ndim)
print(result_unscaled.ndim)
print(conc_avg.ndim)
#plt.plot(temp_avg, conc_avg, 'r.')
plt.title('CSTR concentration vs. temperature plot')
plt.ylabel('conc (mol/L)')
plt.xlabel('temp (K)')
plt.legend(['train', 'validation'], loc='best')
plt.show()

plt.plot(x_test_unscaled, result_unscaled)
plt.title('CSTR concentration vs. temperature plot')
plt.ylabel('conc (mol/L)')
plt.xlabel('temp (K)')
plt.show()

# X (temp):      0 2 1 8 9
# Y (conc):       2 3 4 5 6
# Y_pred (conc):  1 2 3 4 5

"""boxplot (abs_delta), histogram(sns - delta)"""