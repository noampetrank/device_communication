# Device communication

This project contains interfaces and implementations to enable communicating with devices (currently Android).
The main components:
- Python:
	- `InternalAdbConnection` allows to communicate with an Android device using ADB and troubleshoots conneciton problems.
	- `AndroidDeviceUtils` allows to run common commands on an Android device.
	- `FileBridge` allows communicating with a device using files pushed/pulled via ADB.
	- Benchmarks and tests for the above components
	- RPC client that communicates with a server using gRPC.
- C++
	- RPC server and client interfaces and implementation using gRPC.
- Java
	- RPC server interface and implementation using gRPC.


Clone using:

`git clone --recurse-submodules git@github.com:Bugatone/device_communication.git`

or 

`git clone --recurse-submodules https://github.com/Bugatone/device_communication.git`


If you have already cloned, use

`git submodule update --init --recursive`
