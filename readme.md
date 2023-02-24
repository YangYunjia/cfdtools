# CFDTOOLS

## Introduction

The CFDTOOLS is a collections of python interface to set, run and post-process commercial softwares. Currently two major parts is involved: the Metacomp CFD++ and Tecplot.

###  CFD++

[CFD++](https://www.metacomptech.com/index.php/features/icfd) is a wide-used compuational fluid dynamic software suite. All functions provided in the software suite can be directly run through the command line of Windows/Linux system. Here, Python interfaces are implmented to operate CFD++ through cmd/powershell.

The implmentation are based on CFD++ 14.1.

### Tecplot

A collections of tools to let python export/import data in [tecplot format](http://home.ustc.edu.cn/~cbq/360_data_format_guide.pdf). The tools only require you to install numpy and python3. There is no need to install [pytecplot](https://www.tecplot.com/docs/pytecplot/), which requires TecPLUS(TM) maintenance service.

The interfaces are modified from [Luo Han](https://github.com/luohancfd/py2tec). The structure of the code is reorganized, and the usable range is broadened. The main two functions are:

- py2tec: export data in tecplot format
- tec2py: import data in tecplot format

### Disclaimer


CFD++ is a software suite that is available for use on all computer systems developed by Metacomp Technologies, which is a leading provider of software tools for major aerospace, defense, and automobile manufacturers. Tecplot is the name of a family of visualization & analysis software tools developed by Tecplot, Inc., which is headquartered in Bellevue, Washington. Any illegal use of the brand name and related products is beyond the expectation of the author of cfdtools. The author of cfdtools doesn't take any responsibility for the conditions.

The cfdtools is licensed with [GPL 3.0 or later](https://www.gnu.org/licenses/gpl-3.0.html). You are welcome to distribute the codes and you are not required to cite anything. But if you make any modifications, you are required to open source.

## Manual (CFD++)

### start

To use the interface to CFD++, one should first create a object of class `cfdpp` with the code below:

```python

op = cfdpp(op_dir='D:\\cfdppfolder')
```

The **absolute path** is recommanded. The `op_dir` can also be set later by

```python
op.set_path(op_dir='D:\\cfdppfolder')
```

Several additional options need to be assigned when creating the object:

- `core_number`:   core number to conduct cfd (should be assigned when you want to run cfd++ with `cfdtools`)
- `ave_window`:    the number of calculation step of average window. 
    - When reading cfd++ outputs, sometimes (often in unsteady flowfield simulations) we need to average on last several calculation steps to obtain a averaged flowfield or coefficients. The average window (how long you want the average invovle) can be set here. 
    - `ave_window = 0` means no average.
- `verbose`:     how to display infomation during the run
    - `verbose = All`:     display all infomation
    - `verbose = Warning`: only display warnings
    - `verbose = None`:   display nothing

### set running parameters

The parameters of cfd++ can be quarry and set with two groups of commands:

- For ordinary settings:

    Most of settings in CFD++'s `.inp` file is in the format of  `key     value`. For example, `ntstep 500` in line 56 means the calculation takes 500 steps. 
    
    <blockquote>
    If you don't know the setting that you want to change corresponds to which key, you may change it in gui and compare the later and former `.inp` file to find out.
    </blockquote>

    `cfdtools` offer you the interface to acquire and set those parameters. For acquisition, use:

    ```python
    op.read_para(key='somekey')
    ```

    For assignment, use:

    ```python
    op.set_para(key='somekey', value='somevalue')
    ```

- For output variables settings:

    The `npfopts.inp` file determine which variables to be output (by neutral plotter and tecplot). If you want to output a variable, use:

    ```python
    op.set_para(key='P', value='yes', file='node')
    ```

- For infomation set:

    - edit info set

        The operations with `infoset` is a bit complicated. 

        When you want to change the value in a infoset, i.e., to set the outlet pressure in info set No.8 to 101325, use:

        ```python
        op.set_infset(inf_num=8, values=[101325]):
        ```

        note that the infoset for outlet bc only contain 1 parameters, so the length of the list given to `values` is 1.

        if you want to set a inlet conditions (pressure, temperature, k, eps) in info set No.8, use:

        ```python
        op.set_infset(inf_num=8, values=[ptub, ttub, 1.2e5, 8.0e-4])
        ```

        the order is the same with in gui.

        For more complex usage, if you want to just set the pressure and temperature without modify the turbulance infomation k and eps, you can use the keyword for filter `filte` like:

        ```python
        op.set_infset(inf_num=8, values=[ptub, ttub, 0, 0], filte=[2, 3])
        ```

        It means the value in `values` at index no. 2 and 3 will be neglected, and the original value in `.inp` on that place will be keep.
        
        <blockquote>
        Be carefull that the infoset number is not the boundary condition number!
        </blockquote>

    - add infoset

        If you want to add a new info set, use:

        ```python
        new_idx = op.new_infset(typ='backpressure', values=[101325])
        ```

        the new index of the infoset will be returned (as a int).

        Currently, the bc types below are listed:

        | type | number of values needed |  code number in CFD++ |
        | ---- | ---- | ---- |
        | sym  | 0 | 6|
        | wall | 0 | 7|
        | charactistic | 7 |16|
        | backpressure | 1 |35|
        | totalpt | 4| 82|
        | mfr | 4 | 98 |

    - change the infoset for a boundary

        Then you may want to assign this new infoset to a boundary condition, use:

        ```python
        op.change_infset(bc_num=12, typ='backpressure', infset_num=new_idx)
        ```

### run CFD

It is very easy to run CFD++! If the the computation domain has not be divided into parts for mpi (there should be `mcfd_metis.graph` and `mcpusin.bin.##` in the folder is the division is done), use the following command to divide:

```python
op.metis()
```

the core number is decided when creating the object `op`.

Then:

```python
op.run_cfd(restart=False, step=1500)
```

a new console window will automaticly open and the calculation is done in that thread, the main thread will wait until calculation down.

If you want to assign some running parameters before running cfd, you can give the parameters by a keyword dict, like:

```python
op.run_cfd(restart=False, step=1500, cfllbg=0.1)
```

means the cfl number at beginning is set to 0.1. Remind that the `.inp` is changed pertually.

### read output data

- read area

    the geometry area(s) or length(for 2D) of given boundary condition(s) can be read by:

    ```python
    area = op.read_area(typ, bc_series)
    ```

    - The `typ` can be `x`, `y`, or `z`, indicating the projection area along that direction respectively.
    - The `bc_series` is a list containing the boundary number(s). The returned result is the algebra summation of the area of all the boundary(s) in the list.

- read flux

    read flux is alike read area. The energy flux, mass flux, momentum flux (on three directions) and moment (along the axis of three directions) can be read by:

    ```python
    flux = op.read_flux(typ, bc_series)
    ```

    - The `typ` can be:  `energy`, `mass`, `fx`, `fy`, `fz`, `mx`, `my`, `mz`
    - The `bc_series` is defined same as `read_area`
    - The **result will be averaged** by the setting when create the `op`. If you want to override that setting, you can assign it by `ave_window=100` in the parameter.
    - The 3D reference point for moment calculation is defined in gui (default (0,0,0)), if you want to output moment according to other pivot (x1, y1, z1), add `move_axis=(x1, y1, z1)` in parameter

- extract values on bc

    read the values on a given boundary. 

    ```python
    bcdata = op.extract_bc(bc_series, forcenew, remove=True, is_sort=None)
    ```

    - A tecplot file of each boundary in the list `bc_series` will appear contain the data on that boundary (the variables are the same as in flowfield)
    - if boundary is 1D, the data is read via `cfdtools.tecplot` and returned.
    - if `is_sort` is assigned to a variable, i.e, `is_sort='Y'`, the retured data will be sorted by `Y`. 

- extract straight line

    ```python
    linedata = extract_line(st, ed, forcenew, remove=True, var='P T U V W R M')
    ```
    - A line from `st` (a Tuple with three components) to `ed` (a Tuple with three components) will be create. And everywhere the created line intersect with grid line, a datapoint is interpolated and returned. 
    - The returned data is in `cfdtools.tecplot` format




