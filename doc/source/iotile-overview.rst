IOTile Overview
===============

This section provides a basic overview of how IOTile works and how CoreTools 
interacts with IOTile devices.  


The goal of the IOTile framework is to allow anyone to build and deploy
connected devices.  That means that IOTile includes all of the pieces necessary
to:

1. Design and build embedded hardware and firmware
2. Debug and control embedded devices
3. Securely receive data from deployed devices
4. Securely communicate with and remotely update deployed devices
5. Store and display data from devices in the cloud
   
In order to achieve these five goals, all IOTile devices, though they may look
very different, have the same basic architecture and core functionality.

Devices, Tiles, RPCs and Reports
--------------------------------

An IOTile device, at its core, is a circuit 