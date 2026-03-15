.PHONY: all build run clean rebuild paths debug release

BUILD_DIR := build

all: build

build:
	cmake -S . -B $(BUILD_DIR)
	cmake --build $(BUILD_DIR)

run:
	cmake -S . -B $(BUILD_DIR)
	cmake --build $(BUILD_DIR) --target run

paths:
	cmake -S . -B $(BUILD_DIR)
	cmake --build $(BUILD_DIR) --target paths

clean:
	cmake -E rm -rf $(BUILD_DIR)

rebuild: clean build

debug:
	cmake -S . -B $(BUILD_DIR) -DCMAKE_BUILD_TYPE=Debug
	cmake --build $(BUILD_DIR)

release:
	cmake -S . -B $(BUILD_DIR) -DCMAKE_BUILD_TYPE=Release
	cmake --build $(BUILD_DIR)