import cli.util

# Check python version here. The rest of the imports will fail if we are not at
# least on python 3.10. Have this check in a separate file, to make other files
# usable as imports without side-effects.
cli.util.require_python_version(3, 10)
