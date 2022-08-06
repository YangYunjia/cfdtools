

import subprocess
import tempfile

import os


def cmd(command, path=None, wait=None, buffering=10*100):

    '''
    open a new cmd window(minium), and conduct `command`

    paras:
    ---
    `command`   : command to be conducted

    `path`      : change the cmd window to path, default is None

    `wait`      : kill the process after wait time (in second)
    
    `buffering` : buffering to avoid block of `subprocess.Popen`

    return:
    ---
    `lines`     : the output info from cmd, a list(readlines), in byte

        use lines.deconde('gbk') to decode it (on some computer is 'utf-8')

    raise:
    ---
    `TimeoutError`  : when `wait` time is reached, the process is killed, and
                      a `TimeoutError` is raised with infomation about which 
                      command is timeout and which PID is killed

    remark:
    ---
    the function is based on `subprocess.Popen`, which may have block problem

    based on `taskkill` to kill all sub-process\n
    - /F  : forced to kill
    - /T  : kill all sub-process

    usage:
    ---

    >>> try:
    >>>     cmd('start /wait /min /d   '+folder+'  %s.bat'%(bash_name), wait=timeout)
    >>> except TimeoutError:
    >>>     if info:
    >>>         print("    warning: [external_run] timeout at %.2f sec: %s" %(timeout, name))
    >>>     return self.read_output(out_name)

    '''


    if path is not None:
        command = 'cd %s && ' % path + command
    
    try:
        out_tmp = tempfile.SpooledTemporaryFile(buffering=buffering)
        fileno = out_tmp.fileno()
        obj = subprocess.Popen(command, shell=True, stdout=fileno, stderr=fileno)
        if wait is not None:
            obj.wait(wait)
        else:
            obj.wait()

        out_tmp.seek(0)
        lines = out_tmp.readlines()
    
    except subprocess.TimeoutExpired as e:
        p = subprocess.Popen("taskkill /F /T /PID %s" %obj.pid, shell=True, stdout=subprocess.PIPE)
        info = p.stdout.readlines()
        info_line = '>>>   Info:\n'
        for line in info:
            info_line += ('         ' + line.decode('gbk'))
        raise TimeoutError(str(e)+'\n' + info_line)

    finally:
        if out_tmp:
            out_tmp.close()

    return lines


def cfdpp_cmd(command, path=None, wait=None, buffering=10*100):
    mlogflag = False

    if path is not None:
        mlogPath = os.path.join(path, 'mlog')
    else:
        mlogPath = 'mlog'

    if os.path.exists(mlogPath):
        mlogflag = True

    try:
        lines = cmd(command=command, path=path, wait=wait, buffering=buffering)
    
    finally:
        if not mlogflag and os.path.exists(mlogPath):
            os.system('rmdir /s /q  %s' % mlogPath)

    return lines