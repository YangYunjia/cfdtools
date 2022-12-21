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

## Disclaimer


CFD++ is a software suite that is available for use on all computer systems developed by Metacomp Technologies, which is a leading provider of software tools for major aerospace, defense, and automobile manufacturers. Tecplot is the name of a family of visualization & analysis software tools developed by Tecplot, Inc., which is headquartered in Bellevue, Washington. Any illegal use of the brand name and related products is beyond the expectation of the author of cfdtools. The author of cfdtools doesn't take any responsibility for the conditions.

The cfdtools is licensed with [GPL 3.0 or later](https://www.gnu.org/licenses/gpl-3.0.html). You are welcome to distribute the codes and you are not required to cite anything. But if you make any modifications, you are required to open source.