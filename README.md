# Revolution EDA Schematic/Symbol Editors

## Introduction

Revolution EDA is a new generation of schematic and symbol editor targeting custom integrated
circuit design.

1. Revolution EDA can create symbols with both symbol attributes that are common to all
   instances as well instance parameters. Instance parameters can be also python functions that
   allow the dynamic calculation of parameters for each instance.
2. Symbols can be created automatically from schematics and Verilog-A modules. Symbols can
   include circles, lines, rectangles and arches. Notes can be entered on symbols using *Normal*
   labels.
3. Verilog-A symbols have a clear separation between model and instance parameters.
4. File formats are JSON-based allowing easy inspection and editing with a text editor if
   needed.
5. Netlisting process can be guided by a config view like commercial tools allowing designer to
   choose between different views for simulation.
6. Hierarchical netlisting capability is available. Netlisting is currently geared towards Xyce
   although not everything has not been implemented yet, for example subcircuit parameters.
7. Labels can include Python functions such that the full power of Python is available to
   instance callbacks functions. Thus, the professional front-end process design kits can be
   created.
8. There is a familiar library browser allowing creation, renaming, copying, and deleting of
   libraries, cells and cell views.
9. Configuration parameters can be saved in a configuration file.
10. Log file logs error, warning and info messages.

When downloading the package from pypi repository, you may want to download to source package as
well to download *exampleLibraries*.

## Attribution

- Some icons by [Yusuke Kamiyamane](http://p.yusukekamiyamane.com/). Licensed under
  a [Creative Commons Attribution 3.0 License](http://creativecommons.org/licenses/by/3.0/).
