import numpy as np


class Seebeck(): 
    """
    This class creates an object which contains raw and analysed data 
    for Seebeck experiment
    
    Takes as argument a .csv/.dat a file full of data with columns as follows:
    VS : Seebeck channel T+ : Higher temperature channel T- : Lower temperature channel
    each with components _X, _Y, _R, _theta, _dc
    Out_Freq : Output frequency Out_Amp : Output amplitude
    """
    def __init__(self, data):
        self.data = data
        self.data['V+_X'] = self.data['T+_R']*np.cos(self.data['T+_theta']*2*np.pi/360)
        self.data['V+_Y'] = self.data['T+_R']*np.sin(self.data['T+_theta']*2*np.pi/360)
        self.data['V-_X'] = self.data['T-_R']*np.cos(self.data['T-_theta']*2*np.pi/360)
        self.data['V-_Y'] = self.data['T-_R']*np.sin(self.data['T-_theta']*2*np.pi/360)
        self.data['VS_X'] = self.data['VS_R']*np.cos(self.data['VS_theta']*2*np.pi/360)
        self.data['VS_Y'] = self.data['VS_R']*np.sin(self.data['VS_theta']*2*np.pi/360)
        self.data['T0'] = self.data['Temperature_Temperature']

        # Load coefficients of thermocouples for E = f(T_Celsius) where E is in Volts
        self.coeff_E_below_273K = np.array([0, 5.8665508708E1, 4.5410977124E-2, -7.7998048686E-4,
                                    -2.5800160843E-5, -5.9452583057E-7, -9.3214058667E-9,
                                    -1.0287605534E-10, -8.0370123621E-13, -4.3979497391E-15,
                                    -1.6414776355E-17, -3.9673619516E-20, -5.5827328721E-23,
                                    -3.4657842013E-26])[::-1]*1e-6
        self.coeff_E_above_273K = np.array([0, 5.8665508710E1, 4.5032275582E-2, 2.8908407212E-5,
                                    -3.3056896652E-7, 6.5024403270E-10, -1.9197495504E-13,
                                    -1.2536600497E-15, 2.1489217569E-18, -1.4388041782E-21,
                                    3.5960899481E-25])[::-1]*1e-6

    def Sther(self, T_Kelvin):
        """
        This function returns the Seebeck coefficient of the thermocouple
        concerned (by default type "E") at a certain temperature. The input of the
        function is a temperature in Kelvin, but the coefficients below are for a
        polynomial function with T in Celsius. The output is S in [V / K]
        """
        # Convert T_Kelvin to Celsius
        x = T_Kelvin - 273.15
        # T < 273 K
        E_below = np.poly1d(self.coeff_E_below_273K)  # is a poly1d object in Volt
        S_below = np.polyder(E_below)  # is a poly1d object in Volt / Celsius
        # T > 273 K
        E_above = np.poly1d(self.coeff_E_above_273K)  # is a poly1d object in Volt
        S_above = np.polyder(E_above)  # is a poly1d object in Volt / Celsius
        S_values = np.piecewise(x, [x <= 0, x > 0], [S_below(x), S_above(x)]) # is in Volt / K
        return S_values

    
    # def Sther(self,T_Kelvin, Type = "E"):
    #     print(T_Kelvin)
    #     """
    #     This function returns the Seebeck coefficient of the thermocouple
    #     concerned (by default type "E") at a certain temperature. The input of the
    #     function is a temperature in Kelvin, but the coefficient below are for a
    #     polynomial function with T in Celsius. The output is S in [V / K]
    #     """
    #     ## Load coeff of thermocouples for E = f(T_Celsius) where E is in microVolts    
    #     if Type == "E":
    #         coeff_E_below_270K = np.array([0,
    #                                       5.8665508708E1,
    #                                       4.5410977124E-2,
    #                                       -7.7998048686E-4,
    #                                       -2.5800160843E-5,
    #                                       -5.9452583057E-7,
    #                                       -9.3214058667E-9,
    #                                       -1.0287605534E-10,
    #                                       -8.0370123621E-13,
    #                                       -4.3979497391E-15,
    #                                       -1.6414776355E-17,
    #                                       -3.9673619516E-20,
    #                                       -5.5827328721E-23,
    #                                       -3.4657842013E-26])
    
    #         coeff_E_below_270K = coeff_E_below_270K[::-1] # ->reverse,
    #                                     # it is necessary to have cn, cn-1,...
    #                                     # for using poly1d and polyder
    
    #         coeff_E_above_270K = np.array([0,
    #                                       5.8665508710E1,
    #                                       4.5032275582E-2,
    #                                       2.8908407212E-5,
    #                                       -3.3056896652E-7,
    #                                       6.5024403270E-10,
    #                                       -1.9197495504E-13,
    #                                       -1.2536600497E-15,
    #                                       2.1489217569E-18,
    #                                       -1.4388041782E-21,
    #                                       3.5960899481E-25])
    
    #         coeff_E_above_270K = coeff_E_above_270K[::-1] # ->reverse,
    #                                     # it is necessary to have cn, cn-1,...
    #                                     # for using poly1d and polyder
    
    #     ## Convert T_Kelvin to Celsius
    #     T_Celsius = T_Kelvin - 273.15
    
    #     ## Selection of coefficient for temperature regime
    #     index_below = np.where(T_Celsius <= 0)[0] # np.where returns the index of the condition
    #     index_above = np.where(T_Celsius > 0)[0] # np.where returns the index of the condition
    
    #     S_values = np.zeros(np.size(T_Kelvin))
    
    #     E_below = np.poly1d(coeff_E_below_270K) # is a poly1d object in microVolt
    #     S_below = np.polyder(E_below) # is a poly1d object in microVolt / Celsius
    #     S_values[index_below] = S_below(T_Celsius[index_below])*1e-6 # is in Volt / K
    
    
    #     E_above = np.poly1d(coeff_E_above_270K) # is a poly1d object in microVolt
    #     S_above = np.polyder(E_above) # is a poly1d object in microVolt / Celsius
    #     S_values[index_above] = S_above(T_Celsius[index_above])*1e-6 # is in Volt / K
    #     return S_values
    
    def analysis_ac(self):
        Tp_X = self.data["V+_X"] / self.Sther(self.data['T0'])
        Tp_Y = self.data["V+_Y"] / self.Sther(self.data['T0'])
        Tm_X = self.data["V-_X"] / self.Sther(self.data['T0'])
        Tm_Y = self.data["V-_Y"] / self.Sther(self.data['T0'])
        self.data['dT_AC'] = np.sqrt((Tp_X-Tm_X)**2+(Tp_Y-Tm_Y)**2) # delta T R
        self.data['Phi_dT'] = 180/np.pi* np.arctan2(Tp_Y - Tm_Y, Tp_X - Tm_X)
        self.data['Phi_VS'] = self.data['VS_theta']
        self.data['dPhi'] = self.data["VS_theta"] - self.data['Phi_dT']
        self.data['S_AC'] = - np.abs(self.data["VS_R"]/ self.data['dT_AC']) * np.cos(np.pi/180 * self.data['dPhi'])               
        
    # def analysis_dc(self,noise_obj=0):
    #     if not noise_obj == 0:
    #         self.data['T+_DC'] -= np.mean(noise_obj.data['T+_DC'])
    #         self.data['T-_DC'] -= np.mean(noise_obj.data['T-_DC'])
    #         self.data['VS_DC'] -= np.mean(noise_obj.data['VS_DC'])
        
    #     #self.data['T+_dc'] = self.data['T+_DC']/self.Sther(self.data['T0']) + self.data['T0']
    #     #self.data['T-_dc'] = self.data['T-_DC']/self.Sther(self.data['T0']) + self.data['T0']
    #     self.data['dT_DC'] = self.data['T+_DC']/self.Sther(self.data['T0']) - self.data['T-_DC']/self.Sther(self.data['T0'])
    #     self.data['S_DC'] = - self.data['VS_DC']/self.data['dT_DC']
   







    # def Sther(self, T_Kelvin):
    #     """
    #     This function returns the Seebeck coefficient of the thermocouple
    #     concerned (by default type "E") at a certain temperature. The input of the
    #     function is a temperature in Kelvin, but the coefficients below are for a
    #     polynomial function with T in Celsius. The output is S in [V / K]
    #     """
    #     # Convert T_Kelvin to Celsius
    #     x = T_Kelvin - 273.15
    #     # T < 273 K
    #     E_below = np.poly1d(self.coeff_E_below_273K)  # is a poly1d object in Volt
    #     S_below = np.polyder(E_below)  # is a poly1d object in Volt / Celsius
    #     # T > 273 K
    #     E_above = np.poly1d(self.coeff_E_above_273K)  # is a poly1d object in Volt
    #     S_above = np.polyder(E_above)  # is a poly1d object in Volt / Celsius
    #     S_values = np.piecewise(x, [x <= 0, x > 0], [S_below(x), S_above(x)]) # is in Volt / K
    #     return S_values

    # def Ether(self, T_Kelvin):
    #     """
    #     This function returns the integrated Seebeck coefficient in temperature
    #     of the thermocouple concerned (by default type "E") at a certain
    #     temperature. The input of the function is a temperature in Kelvin,
    #     but the coefficients below are for a polynomial function with T
    #     in Celsius. The output is E in Volts
    #     """
    #     # Convert T_Kelvin to Celsius
    #     x = T_Kelvin - 273.15
    #     # Create a piecewise function of E(T_Celsius) in Volts
    #     E_values = np.piecewise(x, [x <= 0, x > 0],
    #                  [lambda x: np.polyval(self.coeff_E_below_273K,x),
    #                   lambda x: np.polyval(self.coeff_E_above_273K,x)])
    #     return E_values