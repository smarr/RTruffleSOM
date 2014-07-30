#!/usr/bin/env make -f

PYPY_DIR ?= pypy
RPYTHON  ?= $(PYPY_DIR)/rpython/bin/rpython


all: compile

# RTruffleSOM-no-jit 
compile: RTruffleSOM-jit

RTruffleSOM-no-jit:
	PYTHONPATH=$(PYTHONPATH):$(PYPY_DIR) $(RPYTHON) --batch src/targetsomstandalone.py

RTruffleSOM-jit:	
	PYTHONPATH=$(PYTHONPATH):$(PYPY_DIR) $(RPYTHON) --batch -Ojit src/targetsomstandalone.py

test: compile
	PYTHONPATH=$(PYTHONPATH):$(PYPY_DIR) nosetests
	./som.sh             -cp Smalltalk:core-lib/SUnit:TestSuite/OMOP TestSuite/TestHarness.som
	./RTruffleSOM-no-jit -cp Smalltalk:core-lib/SUnit:TestSuite/OMOP TestSuite/TestHarness.som
	./RTruffleSOM-jit    -cp Smalltalk:core-lib/SUnit:TestSuite/OMOP TestSuite/TestHarness.som

clean:
	@-rm RTruffleSOM-no-jit
	@-rm RTruffleSOM-jit
