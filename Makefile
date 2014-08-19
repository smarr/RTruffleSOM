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
	if [ -e ./RTruffleSOM-no-jit ]; then ./RTruffleSOM-no-jit -cp Smalltalk:core-lib/SUnit:TestSuite/OMOP TestSuite/TestHarness.som; fi
	if [ -e ./RTruffleSOM-jit    ]; then ./RTruffleSOM-jit    -cp Smalltalk:core-lib/SUnit:TestSuite/OMOP TestSuite/TestHarness.som; fi

clean:
	@-rm RTruffleSOM-no-jit
	@-rm RTruffleSOM-jit
