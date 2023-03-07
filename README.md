Ankermake M5 protocols
======================

This repository tries to document and implement the various APIs associated with
Ankermake M5 3D printers.

For now, MQTT and PPPP have reasonable coverage.

The protocol specifications themselves are written as [Simple Type
Format](https://github.com/chrivers/transwarp#stf-specifications) files.

Simple Type Format (`.stf`) files are lightly-structured, and can be used with
project-specific template files, to generate any type of desired
protocol-related output.

In this repository, we use the
[Transwarp](https://github.com/chrivers/transwarp#transwarp) compiler to compile
the `.stf` files into python code files that implement the various protocols.

In the future, we might also generate C header files, reference documentation,
etc, from the same `.stf` source files:

 - [PPPP specification (stf)](specification/pppp.stf)
 - [MQTT specification (stf)](specification/mqtt.stf)
