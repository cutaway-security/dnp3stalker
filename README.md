# DNP3 Stalker

## Purpose

DNP3 Stalker is a project to analyze and interact with DNP3 devices.

## Modules and Scripts

* dnp3stalker_serial.py - Interact with DNP3 devices via serial connections.
* serial_stub.py - Serial stub to accept serial data and return received data.

## Usage

The current implementation is very basic. User needs to update source and destination addresses by hand. Command selection is very basic and requires reviewing the code to understand what to send.

## Requirements

* CRCMOD - module for computing DNP Cyclic Redundancy Check (CRC) which is CRC-16 implementation specific to DNP. 
* Serial - module for serial communications

## TODO
* Allow user to update source and destination addresses on command line.
* Allow user to select serial mode options via command line.
* Allow user to select a command type by option selection or via a menu.
