# based on https://github.com/tdlib/td/tree/master/example/cpp instructions.

. ./build_env_local.sh

echo "building td..."

cores=$((`grep processor /proc/cpuinfo | wc -l`-1))
echo using $cores cpu cores.

pushd $tdhome

mkdir -pv build
cd build

echo "Also see https://github.com/tdlib/td#building for additional details on TDLib building."

#build_type="Release"
build_type="Debug"
cmake -DCMAKE_BUILD_TYPE=$build_type -DCMAKE_INSTALL_PREFIX:PATH=../example/cpp/td ..
cmake --build . -j $cores --target install

popd

echo "building td done."

echo "now run:"
echo "  $ ./build-tdlib-rest.sh"
