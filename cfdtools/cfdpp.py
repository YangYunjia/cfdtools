'''
cfdtools.cfdpp

a selection of tools to set, run and post-process the commercial software cfd++

'''

import os
import numpy as np
from .system import cfdpp_cmd
from .tecplot import tec2py

# the index of output flux type
typ_dict = {
    'energy':   0,
    'mass':     1,
    'fx':       2,
    'fy':       3,
    'fz':       4,
    'mx':       5,
    'my':       6,
    'mz':       7
}

class cfdpp():
    ''' 
    operation interface to CFD++

    paras
    ===
    - `op_dir`    operation dirctionary
    - `core_number`   core number to conduct cfd
    - `verbose`     how to display infomation during the run
        - `All`     display all infomation
        - `Warning` only display warnings
        - `None`:   display nothing

    '''

    def __init__(self, op_dir=None, core=1, verbose='All'):
        
        self.verbose = {'All': 0, 'Warning': 1, 'None': 2}[verbose]
        
        if op_dir is None:
            op_dir = os.getcwd()
        self.set_path(op_dir)

        # for runing
        self.core_number = core

    def set_path(self, new_path):
        '''
        set work dir. to `new_path`, in which should have file mcfd.inp. The dir. is saved in `self.op_dir`, all operations with cfdpp object is conducted in this folder.

        paras
        ===
        `new_path`      the new direction


        '''
        self.op_dir  = new_path
        self.inp_dir = os.path.join(new_path, "mcfd.inp")
        self.bak_dir = os.path.join(new_path, "mcfd_bak_sp.inp")
        self.FFM_data = None
        self.areas = None

        if not os.path.exists(self.inp_dir):
            if self.verbose < 2: print("mcfd.inp not exist in " + self.op_dir + "nbc not set")
        else:
            self.bc_number = int(self.read_para('mbcons'))
        
        if self.verbose < 1: print("\ndirection changed to " + self.op_dir)

        os.chdir(self.op_dir)

    def metis(self):
        '''
        split metis and split field to `self.core_number` metis
        '''

        os.system("cd %s && @tometis pmetis %d > metis.log" % (self.op_dir, self.core_number))

    def set_para(self, key, value, file=None):
        '''
        set the `key` in mcfd.inp to given value

        paras
        ===
        - `key`   key to be find in `file` and set
        - `value `    value to be set
        - `file`    the file where the value need to be set
            - if is None, set the value in `self.inp_dir` (mcfd.inp)

        '''

        data = ''

        try:
            val_str = str(value)
        except:
            print("value can't be convert to a string")

        if file is None:
            f_name = self.inp_dir
        elif file == 'node':
            f_name = os.path.join(self.op_dir, 'npfopts.inp')
        else:
            if not os.path.exists(file):
                raise FileNotFoundError(file + ' not exist, when setting ' + key + ' to ' + value)
            f_name = os.path.join(self.op_dir, file)
        
        b_name = f_name + '.bak'

        with open(f_name, 'r') as f, open(b_name, 'w') as fbak:
            for line in f.readlines():
                fbak.write(line)
                
                if line.find(key) > -1:
                    line = key + " " +val_str + "\n"

                data += line

        with open(f_name, 'w') as f:
            f.writelines(data)

    def read_para(self, key):
        '''
        read the value in `mcfd.inp` of key

        paras
        ===
        `key`   key to find in mcfd.inp

        return
        ===
        `value` the value of key

        '''
        with open(self.inp_dir, 'r') as f:
            for line in f.readlines(): 
                if line.find(key) > -1:
                    return line.split()[1]
            
        if self.verbose < 2: print("the key %s not found in file" % key)
        return None

                
    def set_infset(self, inf_num, values, filte=[]):
        '''
        write the infset in mcfd.inp

        paras
        ===
        - `inf_num`   the infoset number to be set
        - `values`    should be a list with length same as required variables of the infoset. 
            each value in list corespond the value to be set of the infoset
        - `filte`     should be a list. 
            each number represent the index to maintain current value in mcfd.inp, and not
            to be set by which in `values`

        '''
        
        data = ''

        with open(self.inp_dir, 'r') as f, open(self.bak_dir, 'w') as fbak:
            flag = False
            var_idx = 0
            for line in f.readlines():
                fbak.write(line)

                # Slit boundary type
                
                if line.find('seq.# %s' % str(inf_num)) > -1:
                    splitline = line.split()
                    value_num = int(splitline[3])
                    rest_value_num = value_num
                    inf_name = splitline[5]

                    if len(values) != value_num:
                        print("number not match")
                    else:
                        flag = True
            
                elif flag:
                    pre_data = line.split()
                    line = 'values '
                    for i in range(min(5, rest_value_num)):
                        if var_idx in filte:
                            line += pre_data[i + 1] + " "
                        else:
                            line += "%.4e " % values[var_idx]
                        var_idx += 1
                    line += "\n"
                    rest_value_num -= 5
                    if rest_value_num <= 0:
                        flag = False
                
                data += line
        
        with open(self.inp_dir, 'w') as f:
            f.writelines(data)

    def run_cfd(self, restart=False, step=1500, **kwargs):
        '''
        run cfd

        paras
        ===
        `restart`   bool, whether to restart
        `step`      int, number of steps

        '''

        self.set_para("istart", int(restart))
        self.set_para("ntstep", step)

        for key in kwargs:
            self.set_para(key, kwargs[key])

        print("runing cfd with core number %d" % self.core_number)

        if self.core_number > 1:
            os.chdir(self.op_dir)
            os.system('start /wait /min "" "C:\Program Files\MPICH2\\bin\mpiexec.exe" -localonly -np %d mpimcfd' % self.core_number)
            
            # cfdpp_cmd('"C:\Program Files\MPICH2\\bin\mpiexec.exe" -localonly -np %d mpimcfd' % self.core_number)


    def read_FFM_history(self, n_var=8, n_step=1e10):
        '''
        read the FFM history from mcfd.info1, ignore solver settiong lines

        paras
        ===
        `n_var`     the varibles in mcfd.info1, 8 is default and no need to change
        `n_step`    to read first `n_step`

        data
        ===
        the data read from file is saved in:
        >   `self.areas`        the areas of each boundary in x, y, z and n direction
        >   `self.FFM_data`     FFM data of each boundary, the representation of index is:
        >       dim0: step
        >       dim1: bc_num
        >       dim2: type
        >          typ_dict = {
        >              'energy':   0,
        >              'mass':     1,
        >              'fx':       2,
        >              'fy':       3,
        >              'fz':       4,
        >              'mx':       5,
        >              'my':       6,
        >              'mz':       7
        >          }
        '''

        with open(self.op_dir + "//mcfd.info1", 'r') as f:
            lines = f.readlines()

        for idx, line in enumerate(lines):
            if line.split()[0] == 'At':
                # print(lines[idx: idx + 11])
                del lines[idx: idx + 11]

        
        idx = 14
        step = 0
        file_len = len(lines)

        n_bc = self.bc_number
        n_step = min(int((file_len) / (23 * n_bc + 1)), n_step)
        if self.verbose < 1: print("Acquiring %d bcs intergal data for first %d steps" % (n_bc, n_step))

        data = np.zeros((n_step, n_bc, n_var))
        areass = np.zeros((n_bc, 4))

        for _ in range(n_step):
            for i_bc in range(n_bc):
                for i_var in range(n_var):
                    data[step, i_bc, i_var] = lines[idx].split()[2]
                    idx += 1
                idx += 15
            idx += 1
            step += 1
        
        for i_area in range(n_bc):
            areas_str = lines[22 + i_area * 23].split()
            for i_typ in range(4):
                areass[i_area, i_typ] = float(areas_str[1 + i_typ])


        self.FFM_data = data
        self.areas = areass
        # return data, areass    

    def read_flux(self, typ, bc_series, ave_window=800, move_axis=None):
        '''
        read flux of given type and sum for given bc_series

        paras
        ===
        - `typ`       type to read
        >              'energy':   0,
        >              'mass':     1,
        >              'fx':       2,
        >              'fy':       3,
        >              'fz':       4,
        >              'mx':       5,
        >              'my':       6,
        >              'mz':       7
        - `bc_series`     bc indexs to read and sum
            indx is same with cfd++
        - `ave_window`    averge the last several steps to overcome fluctration
        - `move_axis`     the length to move axis of momentum, in (x, y, z) direction

        return
        ===
        flux        float

        '''
        if self.FFM_data is None:
            self.read_FFM_history()
        
        int_typ = typ_dict[typ]
        
        eps = 1e-3
        flux = 0.0

        if ave_window > 0:
            if self.verbose < 1:print("result averaged by %d steps" % (ave_window))

        for i_bc in bc_series:
            # print("reading bc No. %d, type %s" % (i_bc,typ))

            flux_i = self.FFM_data[-1, i_bc-1, int_typ] 
            if abs(flux_i - self.FFM_data[-5, i_bc-1, int_typ]) / flux_i > eps:
                if self.verbose < 2:print("bc No. %d, type %s not converge" % (i_bc,typ))
            if ave_window > 0:
                flux_i = sum([stepData[i_bc-1, int_typ] for stepData in self.FFM_data[-ave_window:]]) / ave_window

            if move_axis is not None:
                if typ == 'mz':
                    if self.verbose < 1:print("move axis")
                    flux_i -= sum([stepData[i_bc-1, 3] for stepData in self.FFM_data[-ave_window:]]) / ave_window * move_axis[0]
                    flux_i -= sum([stepData[i_bc-1, 2] for stepData in self.FFM_data[-ave_window:]]) / ave_window * move_axis[1]

            flux += flux_i

        
        return flux

    def read_area(self, typ, bc_series):
        '''
        read areas or its projection on axis, for given bc indexs
        paras
        ===
        `typ`       type to read
        >              'x':       0,
        >              'y':       1,
        >              'z':       2
        `bc_series`     bc indexs to read and sum
            indx is same with cfd++

        '''
        if self.areas is None:
            self.read_FFM_history()

        if typ == 'x':
            int_typ = 0
        elif typ == 'y':
            int_typ = 1
        elif typ == 'z':
            int_typ = 2
        
        area = 0.0
        for i_bc in bc_series:
            area += self.areas[i_bc-1, int_typ]

        return area       

    def extract_bc(self, bc_series, forcenew, remove=True):
        data = {'varnames': None, 'lines': []}
        for i in bc_series:
            if forcenew or not os.path.exists(os.path.join(self.op_dir, "BC%d.dat" % i)):
                cfdpp_cmd("exbc2do1 exbcsin.bin pltosout.bin %d" % i)
                if remove:
                    os.system('del ' + os.path.join(self.op_dir, "BC%d.mpf1d" % i))
                    os.system('del ' + os.path.join(self.op_dir, "BC%d.txt" % i))
            if not os.path.exists("BC%d.dat" % i):
                raise IOError("    [Warning] BC%d not extract" %i)
            
            data_tmp = tec2py(os.path.join(self.op_dir, "BC%d.dat" % i))
            if data['varnames'] is None:
                data['varnames'] = data_tmp['varnames']
            data['lines'] += data_tmp['lines']
        

        return data

    
    def extract_line(self, st, ed, forcenew, remove=True, var='P T U V W R M'):

        if forcenew or not os.path.exists(os.path.join(self.op_dir, "lineoutput_1.tec")):
            with open(os.path.join(self.op_dir, "linelist.inp"), 'w') as f:
                
                f.write('1\n')
                f.write('6\n')
                f.write('%.5f %.5f %.5f  ' % st)
                f.write('%.5f %.5f %.5f\n' % ed)

            cfdpp_cmd("npf2lin1 0 linelist.inp lineoutput pltosout.bin " + var)
            if remove:
                os.system('del ' + os.path.join(self.op_dir, "lineoutput_1.mpf1d"))
                os.system('del ' + os.path.join(self.op_dir, "lineoutput_1.txt"))

        if not os.path.exists(os.path.join(self.op_dir, "lineoutput_1.tec")):
            raise IOError("    [Warning] line not extract")

        data = tec2py(os.path.join(self.op_dir, "lineoutput_1.tec"), info=False)



        return data