# Revolution EDA Schematic/Symbol/Layout Editors

## Introduction

Revolution EDA is a new generation of schematic and symbol editor targeting custom integrated circuit design.

1. Revolution EDA uses PySide6, a modern GUI toolkit assuring that the same code base can be used on Linux, MacOS and Windows platforms.
2. Revolution EDA includes integrated circuit design oriented schematic, layout and symbol 
   editors.
3. Revolution EDA can create schematic symbols with both symbol attributes that are common to 
   all instances as well instance parameters. Instance parameters can be also python 
   functions that allow the dynamic calculation of parameters for each instance.
4. Layout editor allows use of parametric layout cells written in Python. Parametric cells are denoted by *pcell* cellviews making clear distinction between cell layouts and parametric cells.
5. Layout via and via arrays, pins, paths (manhattan, diagonal and free-angle), rectangles 
   and polygons can be drawn.
6. Layouts can be exported using gdstk library to hierarchical GDS files. Unlike commercial 
   EDA systems, layout and netlist export processes *do not block* Revolution EDA. The user 
   can continue working as usual.
7. Symbols can be created automatically from schematics, Verilog-A modules and Spice subcircuits. Symbols can 
   include circles, lines, rectangles and arches. Notes can be entered on symbols using *Normal* labels.
8. Verilog-A symbols have a clear separation between model and instance parameters.
9. File formats are JSON-based allowing easy inspection and editing with a text editor if 
   needed.
10. Netlisting process can be guided by a config view like commercial tools allowing designer 
   to choose between different views for simulation.
11. Hierarchical netlisting capability is available. Netlisting is currently geared towards 
   Xyce, but ngSpice netlisting is also on the roadmap.
12. Labels can include Python functions such that the full power of Python is available to 
   instance callbacks functions. Thus, the professional front-end process design kits can be created.
13. There is a familiar library browser allowing creation, renaming, copying, and deleting of 
   libraries, cells and cell views.
14. Configuration parameters can be saved in a configuration file to be reused.
15. A log file logs error, warning and info messages.

When downloading the package from pypi repository, you may want to download to source package as well to download *exampleLibraries*.

You could also use pypi repository to install Revolution EDA:
`pip install revolution-eda`

## Attribution

- Some icons by [Yusuke Kamiyamane](http://p.yusukekamiyamane.com/). Licensed under a [Creative Commons Attribution 3.0 License](http://creativecommons.org/licenses/by/3.0/).
