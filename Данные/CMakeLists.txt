cmake_minimum_required(VERSION 3.20)

project(FinanceMonitor LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Пути проекта
set(ANALYSE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/src/analyse)
set(CPP_INC     ${ANALYSE_DIR}/include)
set(CPP_SRC     ${ANALYSE_DIR}/src)

set(ANALYS_CPP   ${CPP_SRC}/analys_finance.cpp)
set(BUILDING_CPP ${CPP_SRC}/building.cpp)
set(MAIN_CPP     ${ANALYSE_DIR}/main.cpp)
set(PY_APP       ${CMAKE_CURRENT_SOURCE_DIR}/monitor.py)

# Проверки только нужных для сборки C++ файлов
# foreach(path IN LISTS CPP_INC ANALYS_CPP BUILDING_CPP MAIN_CPP)
#     if(NOT EXISTS "${${path}}")
#         message(FATAL_ERROR "Required path not found: ${${path}}")
#     endif()
# endforeach()

# Библиотека. CMake сам выберет правильный формат:
# Linux  -> .so
# macOS  -> .dylib
# Windows-> .dll
add_library(finance SHARED
    ${ANALYS_CPP}
    ${BUILDING_CPP}
    ${MAIN_CPP}
)

# Псевдоним для нормального target-style
add_library(finance::finance ALIAS finance)

target_include_directories(finance
    PUBLIC
        ${CPP_INC}
)

# Для shared library это безопасно и переносимо
set_target_properties(finance PROPERTIES
    OUTPUT_NAME finance
    POSITION_INDEPENDENT_CODE ON
)

# Кладём артефакты в build/lib на всех ОС
set_target_properties(finance PROPERTIES
    ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
)

foreach(cfg Debug Release RelWithDebInfo MinSizeRel)
    string(TOUPPER "${cfg}" cfg_upper)
    set_target_properties(finance PROPERTIES
        ARCHIVE_OUTPUT_DIRECTORY_${cfg_upper} ${CMAKE_BINARY_DIR}/lib
        LIBRARY_OUTPUT_DIRECTORY_${cfg_upper} ${CMAKE_BINARY_DIR}/lib
        RUNTIME_OUTPUT_DIRECTORY_${cfg_upper} ${CMAKE_BINARY_DIR}/lib
    )
endforeach()

# Удобная служебная цель
add_custom_target(paths
    COMMAND ${CMAKE_COMMAND} -E echo "CPP_INC      = ${CPP_INC}"
    COMMAND ${CMAKE_COMMAND} -E echo "ANALYS_CPP   = ${ANALYS_CPP}"
    COMMAND ${CMAKE_COMMAND} -E echo "BUILDING_CPP = ${BUILDING_CPP}"
    COMMAND ${CMAKE_COMMAND} -E echo "MAIN_CPP     = ${MAIN_CPP}"
    COMMAND ${CMAKE_COMMAND} -E echo "PY_APP       = ${PY_APP}"
    COMMAND ${CMAKE_COMMAND} -E echo "LIB_DIR      = ${CMAKE_BINARY_DIR}/lib"
)

# Не ломаем сборку, если Python или monitor.py отсутствуют.
find_package(Python3 COMPONENTS Interpreter QUIET)
if(Python3_Interpreter_FOUND AND EXISTS "${PY_APP}")
    add_custom_target(run
        COMMAND ${Python3_EXECUTABLE} -m streamlit run ${PY_APP}
        DEPENDS finance
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        USES_TERMINAL
    )
endif()