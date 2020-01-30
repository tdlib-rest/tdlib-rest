# based on https://github.com/tdlib/td/tree/master/example/cpp instructions.

. ./build_env_local.sh

echo "building the tdlib-rest httpd..."

cores=$((`grep processor /proc/cpuinfo | wc -l`-1))
echo using $cores cpu cores.

pushd $tdhome
tdhome_abs=`pwd`
popd

pushd main_src

mkdir -pv build
cd build
#build_type="Release"
build_type="Debug"
echo "cmake -DCMAKE_BUILD_TYPE=$build_type -DTd_DIR=$tdhome_abs/example/cpp/td/lib/cmake/Td .."
cmake -DCMAKE_BUILD_TYPE=$build_type -DTd_DIR=$tdhome_abs/example/cpp/td/lib/cmake/Td ..
echo "cmake --build ."
cmake --build . -j $cores

echo "Documentation for all available classes and methods can be found at https://core.telegram.org/tdlib/docs ."
echo "To run this, you may need to manually copy a tdjson shared library from $tdhome_abs/bin to a directory containing built binaries."

#cp -v $tdhome/bin/tdjson.so

popd

echo "now run:"
echo "  $ ./main_src/build/tdlib_rest_httpd"

