import pathlib
print(pathlib.Path.cwd())
if pathlib.Path.cwd().joinpath("revinit.py").exists():
    import revinit
else:
    print('no revinit file.')