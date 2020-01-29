cmake_minimum_required(VERSION 3.1 FATAL_ERROR)

project(TdlibRest VERSION 0.1.0 LANGUAGES CXX)

find_package(Td 1.5.5 REQUIRED)

add_executable(tdlib_rest_httpd main.cpp)
target_link_libraries(tdlib_rest_httpd PRIVATE Td::TdJson)
set_property(TARGET tdlib_rest_httpd PROPERTY CXX_STANDARD 11)

