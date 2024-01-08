# Revolution EDA Schematic/Symbol Editors

## Introduction

Revolution EDA is a new generation of schematic and symbol editor targeting custom integrated circuit design.

1. Revolution EDA include integrated circuit design oriented schematic, layout and symbol 
   editors.
2. Revolution EDA can create schematic symbols with both symbol attributes that are common to 
   all instances as well instance parameters. Instance parameters can be also python 
   functions that allow the dynamic calculation of parameters for each instance.
3. Layout editor allows use of parametric layout cells written in Python. 
4. Layout via and via arrays, pins, paths (manhattan, diagonal and free-angle), rectangles 
   and polygons can be drawn.
5. Layouts can be exported using gdstk library to hierarchical GDS files. Unlike commercial 
   EDA systems, layout and netlist export processes *do not block* Revolution EDA. The user 
   can continue working.
5. Symbols can be created automatically from schematics and Verilog-A modules. Symbols can 
   include circles, lines, rectangles and arches. Notes can be entered on symbols using *Normal* labels.
6. Verilog-A symbols have a clear separation between model and instance parameters.
7. File formats are JSON-based allowing easy inspection and editing with a text editor if 
   needed.
8. Netlisting process can be guided by a config view like commercial tools allowing designer 
   to choose between different views for simulation.
9. Hierarchical netlisting capability is available. Netlisting is currently geared towards 
   Xyce although not everything has not been implemented yet, for example subcircuit parameters.
10. Labels can include Python functions such that the full power of Python is available to 
   instance callbacks functions. Thus, the professional front-end process design kits can be created.
11. There is a familiar library browser allowing creation, renaming, copying, and deleting of 
   libraries, cells and cell views.
12. Configuration parameters can be saved in a configuration file.
1Log file logs error, warning and info messages.

When downloading the package from pypi repository, you may want to download to source package as well to download *exampleLibraries*.

## Attribution

- Some icons by [Yusuke Kamiyamane](http://p.yusukekamiyamane.com/). Licensed under a [Creative Commons Attribution 3.0 License](http://creativecommons.org/licenses/by/3.0/).
