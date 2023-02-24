
import numpy as np
import re

FEM_TYPE = [['FELINESEG'],
            ['FETRIANGLE', 'FEQUADRILATERAL', 'FEPOLYGON'],
            ['FETETRAHEDRON', 'FEBRICK', 'FEPOLYHEDRAL']]

FEM_FACE_TYPE = ['FEPOLYGON', 'FEPOLYHEDRAL']

STRDIGIT = [str(digit) for digit in range(10)] + ['-']

def _nparray2string(val):
    '''
    convert a numpy array to string
    '''
    m = val.shape
    if len(m) > 3:
        raise ValueError('Output limits to 3D matrix')
    if len(m) == 1:
        return ' '.join(['{:e}'.format(x) for x in val]) + '\n'
    if len(m) == 2:
        s = []
        for row in val:
            s.append(' '.join(['{:e}'.format(x) for x in row]))
        return '\n'.join(s) + '\n'
    if len(m) == 4:
        sp = []
        for p in val:
            s = []
            for row in val:
                s.append(' '.join(['{:e}'.format(x) for x in row]))
            sp.append('\n'.join(s))
        return '\n'.join(sp) + '\n'

def _formatnp(data):
    '''
    Generate appropriate format string for numpy array

    Argument:
        - data: a list of numpy array
    '''

    dataForm = []
    for i, idata in enumerate(data):
        if np.issubsctype(idata, np.integer):
            dataForm.append('{:d}')
        else:
            dataForm.append('{:e}')

    return ' '.join(dataForm)

def _writeZoneHeader(fid, header, size, izone=0):
    '''
    Write zone header
    Arguments:
        - fid: file stream)
        - header: zone header information
        - size: a list for size of the zone
    '''
    # zonename
    if 'zonename' in header:
        zonename = header['zonename']
    else:
        zonename = 'ZONE {:d}'.format(izone)
    fid.write('ZONE T="{:s}"'.format(zonename))

    # zonetype and size
    if 'zonetype' in header.keys():
        zonetype = header['zonetype']
    else:
        zonetype = 'ORDERED'
    fid.write(' ZONETYPE={:s}'.format(zonetype))
    if zonetype == 'ORDERED':
        if len(size) == 3:
            fid.write(' I={2:d} J={1:d} K={0:d}'.format(*size))
        elif len(size) == 2:
            fid.write(' I={1:d} J={0:d}'.format(*size))
        elif len(size) == 1:
            fid.write(' I={:d}'.format(*size))
    else:
        # FEM zone
        fid.write(' NODES={:d} ELEMENTS={:d}'.format(size[0], size[1]))
        if len(size) == 3:
            fid.write(' FACES={:d}'.format(size[3]))

    # passivevar
    if 'passivevarlist' in header:
        fid.write(' PASSIVEVARLIST = [{:s}]'.format(','.join([ii+1 for ii in header['passivevarlist']])))

    # reformat boolean type
    boolean_param = {
        'datapacking': {0: 'POINT', 1: 'BLOCK'},
    }
    for k in boolean_param.keys():
        if k in header.keys() and header[k] in boolean_param[k].keys():
            header[k] = boolean_param[k][header[k]]

    other_param = {
        'datapacking': ['BLOCK', '{:s}'],
        'solutiontime': [None, '{:e}'],
        'strandid': [None, '{:d}'],
        'varloc': [None, '{:s}']
    }

    for key, val in other_param.items():
        formatStr = ' {:s}'.format(key.upper()) + '=' + val[1]
        if key in header.keys():
            fid.write(formatStr.format(header[key]))
        elif val[0]:
            fid.write(formatStr.format(val[0]))

    fid.write('\n')
    return True

def split_data(dt, splitor, zonename=None):

    data = dt['data']
    var_num = len(data)
    data_num = len(data[0])
    zone_num = len(splitor)

    if zonename is None or len(zonename) != zone_num:
        zonename = ['Zone %d' % i for i in range(zone_num)]

    # if sum(splitor) != data_num:
    #     print("data number(%d) not equal to splitor" % data_num, splitor)
    #     return

    splited_data = [{'data': [], 'zonename': zm} for zm in zonename]

    for arr in data:
        arr_split = np.split(arr, splitor)
        for i in range(zone_num):
            splited_data[i]['data'].append(arr_split[i])

    return splited_data

def py2tec(tdata, fname):
    '''
    Argument list:

    - tdata: A dictionary of data, it can have the following keys:
        + title (optional): title of the file
        + varnames: a list of variable names
        + lines (optional): a list of [line data] for line plot
          each [line data] should be a dict having following keys
            + `data`: the data for the line, it should be a list of numpy arraies, which should have the same length.
                    numpy array's dtype can be int or float
            + `zonename`(opt., default = 'ZONE' + No.): name of the zone
            + `passivevarlist` (opt., default = None): exclude some variables from the data
            + `datapacking` (opt., default = 'POINT')
            + `zonetype` (opt., default = 'ORDERED')
            # TODO
            + lines.datapacking
        + surfaces (optional): TODO
    '''
    if not isinstance(tdata, dict):
        raise TypeError('tdata should be a dict')
    with open(fname, 'w', encoding='utf-8') as fid:
        # title
        if 'title' in tdata:
            fid.write('TITLE = "{:s}"\n'.format(tdata['title']))

        # variables
        fid.write('VARIABLES = {:s}\n'.format(','.join(['"{:s}"'.format(i) for i in tdata['varnames']])))

        nzone = {'lines': 0, 'surfaces': 0}
        for key in nzone.keys():
            if key in tdata:
                nzone[key] = len(tdata[key])

        izone = 0
        # ========================== write lines ======================================
        if nzone['lines'] > 0:
            for i, line in enumerate(tdata['lines']):
                izone += 1

                # get number of rows
                nx = len(line['data'][0])

                # modify header
                if 'datapacking' not in line.keys():
                    line['datapacking'] = 'POINT'
                if 'zonetype' not in line.keys():
                    line['zonetype'] = 'ORDERED'
                
                _writeZoneHeader(fid, line, [nx], izone)

                # write data
                dataFormat = _formatnp(line['data']) + '\n'
                # nvar = len(tdata['varnames']) - len(passivevarlist)
                for ix in range(nx):
                    d = [j[ix] for j in line['data']]
                    fid.write(dataFormat.format(*d))

                fid.write('\n')
        # =========================== Write 2D surface ================================
        if nzone['surfaces'] > 0:
            for isurf, surf in enumerate(tdata['surfaces']):
                izone += 1
                if 'datapacking' not in surf.keys():
                    surf['datapacking'] = 'BLOCK'

                # 0 for nodal, 1 for center
                if 'varloc' in surf.keys():
                    ivarloc = surf['varloc']
                    if isinstance(ivarloc, list):
                        surf['datapacking'] = 'BLOCK'
                        icen = []
                        inodal = []
                        for i, ii in enumerate(ivarloc):
                            if ii == 1:
                                icen.append(i+1)
                            else:
                                inodal.append(i+1)
                else:
                    ivarloc = 0

                x = surf['x']
                # x should be store in the following way
                # x -----> i
                # |
                # |
                # ^ j
                y = surf['y']
                if 'z' in surf.keys():
                    z = surf['z']
                if 'v' in surf.keys():
                    v = surf['v']

                m, n = x.shape
                if isinstance(ivarloc, list):
                    surf['varloc'] = 'VARLOCATION=({:s}=CELLCENTERED, {:s}=NODAL)\n'.format(str(icen), str(inodal))
                elif ivarloc == 1:
                    surf['varloc'] = 'VARLOCATION=([{:d}-{:d}]=CELLCENTERED)\n'.format(1, len(tdata['varnames']))

                _writeZoneHeader(fid, surf, [m, n], izone)

                if surf['datapacking'] == 'BLOCK':
                    fid.write(_nparray2string(x))
                    fid.write(_nparray2string(y))
                    if 'z' in surf.keys():
                        fid.write(_nparray2string(z))
                    if 'v' in surf.keys():
                        for vv in v:
                            fid.write(_nparray2string(vv))
                else:
                    data = x
                    data = np.vstack((data, y))
                    if 'z' in surf.keys():
                        data = np.vstack((data, z))
                    if 'v' in line.keys():
                        for vv in v:
                            data = np.vstack((data, vv))
                    fid.write(_nparray2string(data.T))
                fid.write('\n\n')

def tec2py(datfile, info=True, is_sort=None):
    '''
    Argument list:

    return:
    ===
    - tdata: A dictionary of data, it can have the following keys:
        + varnames: a list of variable names
        + lines (optional): a list of [line data] for line plot
          each [line data] should be a dict having following keys
            + `data`: the data for the line, it should be a list of numpy arraies, which should have the same length.
                    numpy array's dtype can be int or float
            + `zonename`(opt., default = 'ZONE' + No.): name of the zone
            + `passivevarlist` (opt., default = None): exclude some variables from the data
            + `datapacking` (opt., default = 'POINT')
            + `zonetype` (opt., default = 'ORDERED')
            # TODO
            + lines.datapacking
        + surfaces (optional): TODO
    '''
    # datfile = "D:\\CEN\\Opt1\\415\\Calculation\\0\\BC3.DAT"

    var_list = []
    lines = []
    nzone = 0

    with open(datfile, 'r') as fid:
        try:
            line_num = 1
            line = next(fid).strip()
            split_line = line.split()
            while True:
                if len(split_line) <= 0 or split_line[0] in ['TITLE', '#']:
                    line = next(fid).strip()
                    line_num += 1
                    split_line = line.split()
                
                elif split_line[0] == 'VARIABLES':

                    while True:
                        if line[0] not in ['"', 'V']:
                            split_line = line.split()
                            break
                        var_list += re.findall(r'[''"](.*?)[''"]', line)
                        line = next(fid).strip()
                        line_num += 1
                        
                    n_var = len(var_list)
                    if info:
                        print("%d variables recognized, name:" % n_var, var_list)
                
                elif split_line[0] == 'ZONE':
                    nzone = nzone + 1
                    # ===========load zone information===================
                    inum = False
                    jnum = False
                
                    while True:
                        if line[0] in STRDIGIT:
                            split_line = line.split()
                            break
                            
                        if not inum:
                            inum = re.findall(r'I\s*=\s*(\d+)', line)
                        if not jnum:
                            jnum = re.findall(r'J\s*=\s*(\d+)', line)
                        zonename = re.findall(r'T\s*=\s*["''](.*)[''"]', line)
                        line = next(fid).strip()
                        line_num += 1

                    if inum:
                        inum = int(inum[0])
                    else:
                        inum = 0

                    if jnum:
                        jnum = int(jnum[0])
                    else:
                        jnum = 1
                    
                    ndata = inum*jnum

                    if not zonename:
                        zonename = re.findall(r'T\s*=\s*(.*)', line)
                    if zonename:
                        zonename = zonename[0]
                    else:
                        zonename = 'data %d' % (nzone,)

                    #  ============== load data ===========================
                    zone_data = []
                    try:
                        while True:
                            # print(split_line)
                            l2append = [float(i) for i in split_line]
                            zone_data += l2append
                            line = next(fid).strip()
                            split_line = line.split()
                            
                    except ValueError or StopIteration:
                        pass

                    finally:
                        # print(zone_data)
                        if jnum == 1:
                            zone_data = np.array(zone_data).reshape(-1, n_var)
                            ndata0 = zone_data.shape[0]
                            if ndata == 0:
                                print('%d points read, I,J not found' % ndata0)
                            elif ndata0 == ndata:
                                print('ndata: I=%d read' % (inum))
                            else:
                                print('ndata = %d, but %d points read' % (ndata, ndata0))

                            zone_data = zone_data.T
                            
                        else:
                            zone_data = np.array(zone_data).reshape((inum, jnum, n_var))
                            print('ndata: I=%d * J=%d' % (inum, jnum))
                            zone_data = zone_data.transpose((2, 0, 1))
                            
                        lines.append({'zonename': zonename, 'data': [i for i in zone_data]})

                else:
                    raise IOError("Can't Identify line # %d: %s" % (line_num, line))


        except StopIteration:
            pass

        if is_sort is not None:

            if is_sort not in var_list:
                print('No variable "%s" in varlist:' % is_sort + var_list)
            else:
                sort_idx = var_list.index(is_sort)

                for line in lines:
                    sort_idx = np.argsort(line['data'][sort_idx])
                    line['data'] = [np.array([d[i] for i in sort_idx]) for d in line['data']]



    return {'varnames': var_list, 'lines': lines}