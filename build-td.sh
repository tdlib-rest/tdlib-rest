# based on https://github.com/tdlib/td/tree/master/example/cpp instructions.

. ./tdenv_local.sh

echo "building td..."

pushd $tdhome

mkdir -pv build
cd build

# Also see https://github.com/tdlib/td#building for additional details on TDLib building.

cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX:PATH=../example/cpp/td ..
cmake --build . --target install

popd

echo "building td done."

echo "now run . ./build-examples.sh"
