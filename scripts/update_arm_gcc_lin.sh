#!/usr/bin/env bash

set -e

# If we already have both programs installed, don't do anything
if [[ -f arm_gcc/bin/arm-none-eabi-gcc && -f arm_qemu/bin/qemu-system-gnuarmeclipse ]]; then
	exit 0
fi

rm -rf arm_gcc
rm -rf arm_qemu

curl -L -o gcc-arm-none-eabi.tar.gz https://s3.amazonaws.com/arch-public-static-files-11ca2993de6b03471b7b1f1f704cb58f/gcc-arm-none-eabi-7-2017-q4-major-linux.tar.bz2
mkdir -p arm_gcc
tar -jxf gcc-arm-none-eabi.tar.gz -C arm_gcc --strip-components 1
rm gcc-arm-none-eabi.tar.gz

curl -L -o qemu.tar.gz https://s3.amazonaws.com/arch-public-static-files-11ca2993de6b03471b7b1f1f704cb58f/gnuarmeclipse-qemu-debian64-2.8.0-201612271623-dev.tgz
mkdir -p arm_qemu
tar -zxf qemu.tar.gz -C arm_qemu --strip-components 2
rm qemu.tar.gz
