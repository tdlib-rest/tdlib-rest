cmake_minimum_required(VERSION 3.1 FATAL_ERROR)

project(TdlibRest VERSION 0.1.0 LANGUAGES CXX)

set(Boost_USE_STATIC_LIBS        ON)
set(Boost_USE_MULTITHREADED      ON)
set(Boost_USE_STATIC_RUNTIME    OFF)

find_package ( Boost COMPONENTS system filesystem program_options date_time REQUIRED )
if(NOT DEFINED Boost_INCLUDE_DIRS)
  message(SEND_ERROR "Boost is not found, or your boost version was below 1.46. Please download Boost!")
endif()

find_package(Td 1.5.5 REQUIRED)

find_package(Threads REQUIRED)

file(GLOB SOURCES
    ./*.h
    ./*.cpp
)
add_executable(tdlib_rest_httpd ${SOURCES})
target_link_libraries(tdlib_rest_httpd PRIVATE Td::TdJson Boost::system Threads::Threads)
set_property(TARGET tdlib_rest_httpd PROPERTY CXX_STANDARD 11)

