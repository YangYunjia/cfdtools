import math
from functools import reduce
from scipy.optimize import fsolve

import subprocess
import tempfile
import os
import copy

ga = 1.4
R = 287

coef8 = math.sqrt(ga / R * (2.0 / (ga + 1))**((ga + 1) / (ga - 1)))

def std_atomsphere(h, tref=288.15, rref=1.225, pref=101325, muref=1.72e-5):
    '''
    docin.com/p-70811798.html
    杨炳尉 标准大气参数的公式表示 宇航学报 1983年1月

    '''
    if h <= 11:
        w = 1 - h / 44.3308
        t = tref * w
        r = rref * w**4.2559
        p = pref * w**5.2559
    elif h <= 20:
        w = math.exp((14.9647 - h) / 6.3416)
        t = 216.65
        p = pref * 0.11953 * w
        r = rref *  1.5898 * w
    elif h <= 32:
        w = 1 + (h - 24.9021) / 221.552
        t = 221.55
        p = pref * 0.025158 * w**-34.1629
        r = rref * 0.032722 * w**-35.1629
    else:
        raise ValueError("h < 0 or h > 32")
    
    mu = muref * (t / 273.11)**1.5 * 383.67 / (t + 110.56)
    a = 20.0468 * t**0.5

    return {'temperature': t, 'pressure': p, 'density': r, 'viscosity': mu, 'soundspeed': a}

def ideal_mfr(pt8, tt8, A8):
    return coef8 * pt8 / tt8**0.5 * A8

def ideal_thrust(pt7, tt7, p9, m8, fluid=None):
    npr = pt7 / p9
    if fluid is None:
        v9id = math.sqrt(2 * ga * R / (ga-1) * tt7 * (1 - npr**(-(ga-1)/ga)))
    else:
        v9id = u9(fluid, tt7, t9(fluid, npr, tt7))
    
    thrustid = m8 * v9id
    return thrustid, v9id


class Fluid():
    
    def __init__(self, name, fix_thermo=False):
        self.name = name
        self.is_fix_thermo = fix_thermo
        if name == 'Air':
            self._gamma = 1.4
            self._cp_R = 3.5
            self._cp_R_para =  [[3.69736457,-1.5817846e-03, 3.89632940e-06,-2.5147111e-09, 4.89905696e-13],
                                [3.01061392, 1.4262348e-03,-5.41285431e-07, 9.8318138e-11,-6.77753328e-15]]
        else:
            raise KeyError()

    def cp_R(self, T):

        if self.is_fix_thermo:
            return self._cp_R
        else:
            return self.cal_cp_R(T)

    def cal_cp_R(self, T, intergal=False):
        
        para = copy.deepcopy(self._cp_R_para)

        if intergal:
            for i in range(2, len(para[0])):
                para[0][i] /= i
                para[1][i] /= i
        # print(para[1][0]* math.log(T))
        
        if T < 100.0:
            return self.cal_cp_R(100.0, intergal=intergal)
        elif 100.0 <= T and T < 1000.0:
            return reduce(lambda x,i: (x + para[0][-i-1]) * T, range(len(para[0])-1),0) + para[0][0] * (1, math.log(T))[intergal]
        elif 1000.0 <= T and T < 5000.0:
            return reduce(lambda x,i: (x + para[1][-i-1]) * T, range(len(para[1])-1),0) + para[1][0] * (1, math.log(T))[intergal]
        elif 5000.0 <= T:
            return self.cal_cp_R(5000.0, intergal=intergal)

    def cal_cp_R_intergal(self, T, T0):

        if T < 1000.0 and 1000.0 <= T0:
            delta = - self.cal_cp_R(1000 - 1e-7,intergal=True) + self.cal_cp_R(1000,intergal=True)
        elif T0 < 1000.0 and 1000.0 <= T:
            delta = self.cal_cp_R(1000 - 1e-7,intergal=True) - self.cal_cp_R(1000,intergal=True)
        else:
            delta = 0.0
        
        return self.cal_cp_R(T,intergal=True) - self.cal_cp_R(T0,intergal=True) + delta


def t9(fluid, npr, tt7, fix_thermo=False):
    # approx with fix thermo
    if fluid.cp_R(500) == 0:
        print('!')
    _t9_fix = tt7 * npr**(-1 / 3.5)
    # print(npr, _t9_fix)
    if fix_thermo:return _t9_fix

    return fsolve(lambda x: math.log(npr) + fluid.cal_cp_R_intergal(x, tt7), _t9_fix)[0]

def u9(fluid, tt7, t9):
    if t9 >= tt7:
        return 0.0
    return math.sqrt(2 * R * (fluid.cp_R(tt7)*tt7 - fluid.cp_R(t9)*t9))


if __name__ == '__main__':
    air = Fluid('Air')
    # npr = 1.895
    # tt = 781.3
    npr = 2.827
    tt = 2063
    t9_v = t9(air, npr, tt)
    print(t9_v)
    print(u9(air, tt, t9_v))
    # print(ideal_mfr(191200, 781.3, 0.398))
    print(ideal_thrust(npr, tt, 1, 1))