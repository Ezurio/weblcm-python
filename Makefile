PYTHON ?= /usr/bin/python
WEBLCM_PYTHON_EGG = dist/weblcm-python-1.0-py3.egg
WEBLCM_PYTHON_PY_SRCS = __main__.py weblcm_python_func.py weblcm_python_def.py
WEBLCM_PYTHON_PY_SETUP = setup.py

all: $(WEBLCM_PYTHON_EGG)

$(WEBLCM_PYTHON_EGG): $(WEBLCM_PYTHON_PY_SRCS) $(WEBLCM_PYTHON_PY_SETUP)
	$(PYTHON) $(WEBLCM_PYTHON_PY_SETUP) bdist_egg --exclude-source-files

.PHONY: clean

clean:
	-rm -rf dist
	-rm -rf build
	-rm -rf *.egg-info