VZSandbox
=========

This module configures a sandbox environment of disposable Linux machines in OpenVZ.
It is intended for classroom use, where you need to provide a large number of Linux machines
to students quickly, where they have root access to practice administration but are jailed
so they cannot interfere with each other.  This module is intended to configure multiple servers:

* Multiple OpenVZ hypervisors.  This solution is designed to scale horosontially, not vertically, for speed.  Multiple small - medium sized hyps will offer superior performance to one big one.
* A load balancer for distributing VM requests to the hypervisors
* A gateway shell server which offers a pseudo-login shell for the users.  This shell will request a sandbox VM and log the user into their sandbox.

The environment this module configures is volatile by design.
It was designed for classroom use where students will use, and likely abuse, these containers and require a clean environment upon each login.
The containers will not be cleaned as long as they have a user logged in over SSH, but will be automatically destroyed and rebuilt once they are idle.
Currently containers are flagged as in use if they have an active ssh process via /proc.
This method was chosen as it is reliable even if someone completely destroys the continer filesystem.

The current use is as follows:
* A user SSH's in to the gateway server as a user with a shell of /usr/local/bin/vzsandbox-shell.py
* The vzsandbox-shell script makes a request to the load balancer for a container
* The load balancer requests a container from one of the hypervisors
* The hypervisor powers on and returns details of the container to use
* The shell uses expect to SSH into the container
* The user interacts with the container as if they logged in directly

As speed is a key need here, the hypervisors will keep a cache of "clean" containers on hand.
The hypervisors track the container states, and favor containers from the "clean" cache before overwriting dirty containers or building more.
There is a cron job on the hyps which clean up idle containers for future use, and build more containers to maintain the cache.
Each hyp has a defined maximum of containers to avoid issues with resource depletion or full disk.

APIs are currently implemented via flask-resful in Python.
There is no API security at this time.
The APIs currently need to be run on trusted networks, a dedicated VLAN with proper hyp firewall rules is recommended.
