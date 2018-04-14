#!/usr/bin/env bash

set -e

# If we already have both programs installed, don't do anything
if [[ -f arm_gcc/bin/arm-none-eabi-gcc && -f arm_qemu/bin/qemu-system-gnuarmeclipse ]]; then
	exit 0
fi

rm -rf arm_gcc
rm -rf arm_qemu

curl -L -o gcc-arm-none-eabi.tar.gz https://developer.arm.com/-/media/Files/downloads/gnu-rm/7-2017q4/gcc-arm-none-eabi-7-2017-q4-major-mac.tar.bz2?revision=7f453378-b2c3-4c0d-8eab-e7d5db8ea32e?product=GNU%20Arm%20Embedded%20Toolchain,64-bit,,Mac%20OS%20X,7-2017-q4-major
mkdir -p arm_gcc
tar -jxf gcc-arm-none-eabi.tar.gz -C arm_gcc --strip-components 1
rm gcc-arm-none-eabi.tar.gz

curl -L -o qemu.tar.gz https://github.com/gnu-mcu-eclipse/qemu/releases/download/gae-2.8.0-20170301/gnuarmeclipse-qemu-osx-2.8.0-201703012029-head.tgz
mkdir -p arm_qemu
tar -zxf qemu.tar.gz -C arm_qemu --strip-components 2
rm qemu.tar.gz
