# based on https://github.com/tdlib/td/tree/master/example/cpp instructions.

. ./build_env_local.sh

echo "building the tdlib_rest httpd..."

pushd $tdhome
tdhome_abs=`pwd`
popd

pushd main_src

mkdir -pv build
cd build
echo "cmake -DCMAKE_BUILD_TYPE=Release -DTd_DIR=$tdhome_abs/example/cpp/td/lib/cmake/Td .."
cmake -DCMAKE_BUILD_TYPE=Release -DTd_DIR=$tdhome_abs/example/cpp/td/lib/cmake/Td ..
echo "cmake --build ."
cmake --build .

echo "Documentation for all available classes and methods can be found at https://core.telegram.org/tdlib/docs ."
echo "To run this, you may need to manually copy a tdjson shared library from $tdhome_abs/bin to a directory containing built binaries."

#cp -v $tdhome/bin/tdjson.so

popd
