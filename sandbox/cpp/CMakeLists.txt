# To build the whole of sandbox, do the following steps:
# * Make sure that you have conan installed in your Python virtual environment (pip3 install conan)
# * Execute the commands:
# cd {root of the repository}
# mkdir sandbox-cpp-build
# cmake ../sandbox/cpp && make all

cmake_minimum_required(VERSION 3.5.1)

project(Sandbox)

set(default_build_type "Debug")

include(conan.cmake)

conan_cmake_run(REQUIRES jsoncpp/1.8.4@theirix/stable
        BASIC_SETUP CMAKE_TARGETS
        BUILD missing)

add_executable(play_with_default_value_date play_with_default_value_date.cpp)
add_executable(play_with_duration_regex play_with_duration_regex.cpp)
add_executable(play_with_jsoncpp play_with_jsoncpp.cpp)
target_link_libraries(play_with_jsoncpp CONAN_PKG::jsoncpp)

add_executable(play_with_placement_new play_with_placement_new.cpp)