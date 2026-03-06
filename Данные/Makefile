PYTHON ?= $(PROJECT_ROOT)/.venv/bin/python
CXX ?= g++

UNAME_S := $(shell uname -s)

# Абсолютный путь к папке, где лежит сам Makefile
MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PROJECT_ROOT := $(MAKEFILE_DIR)

BUILD_DIR := $(PROJECT_ROOT)/build
PY_APP := $(PROJECT_ROOT)/monitor.py

CPP_INC := $(PROJECT_ROOT)/src/analyse/include
CPP_SRC := $(PROJECT_ROOT)/src/analyse/src
CPP_MAIN := $(PROJECT_ROOT)/src/analyse

ANALYS_CPP := $(CPP_SRC)/analys_finance.cpp
MAIN_CPP := $(CPP_MAIN)/main.cpp
BINDINGS_CPP := $(firstword $(wildcard $(CPP_SRC)/bindings.cpp $(CPP_SRC)/building.cpp))

CXXFLAGS := -O2 -std=c++17 -fPIC -I$(CPP_INC)

CPP_SOURCES := $(ANALYS_CPP) $(MAIN_CPP) $(BINDINGS_CPP)

ifeq ($(UNAME_S),Darwin)
	LIB_NAME := libfinance.dylib
	SHARED_FLAG := -dynamiclib
else
	LIB_NAME := libfinance.so
	SHARED_FLAG := -shared
endif

LIB_PATH := $(BUILD_DIR)/$(LIB_NAME)

.PHONY: all build run clean rebuild check paths

all: build

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

build: check $(LIB_PATH)

$(LIB_PATH): $(CPP_SOURCES) | $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) $(CPP_SOURCES) $(SHARED_FLAG) -o $(LIB_PATH)

run: build
	$(PYTHON) -m streamlit run $(PY_APP)

rebuild: clean build

clean:
	rm -rf $(BUILD_DIR)

paths:
	@echo "PROJECT_ROOT = $(PROJECT_ROOT)"
	@echo "PY_APP       = $(PY_APP)"
	@echo "CPP_INC      = $(CPP_INC)"
	@echo "ANALYS_CPP   = $(ANALYS_CPP)"
	@echo "MAIN_CPP     = $(MAIN_CPP)"
	@echo "BINDINGS_CPP = $(BINDINGS_CPP)"
	@echo "LIB_PATH     = $(LIB_PATH)"

check:
	@test -f "$(PY_APP)" || (echo "ERROR: not found $(PY_APP)" && exit 1)
	@test -d "$(CPP_INC)" || (echo "ERROR: not found include dir $(CPP_INC)" && exit 1)
	@test -f "$(ANALYS_CPP)" || (echo "ERROR: not found $(ANALYS_CPP)" && exit 1)
	@test -f "$(MAIN_CPP)" || (echo "ERROR: not found $(MAIN_CPP)" && exit 1)
	@test -n "$(BINDINGS_CPP)" || (echo "ERROR: not found bindings.cpp or building.cpp in $(CPP_SRC)" && exit 1)
	@test -f "$(PROJECT_ROOT)/src/cpp_bridge.py" || (echo "ERROR: not found $(PROJECT_ROOT)/src/cpp_bridge.py" && exit 1)
	@test -f "$(PROJECT_ROOT)/src/cpp_signals.py" || (echo "ERROR: not found $(PROJECT_ROOT)/src/cpp_signals.py" && exit 1)
	@echo "OK"