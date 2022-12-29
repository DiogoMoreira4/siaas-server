# siaas-server

_Intelligent System for Automation of Security Audits (SIAAS) - Server_

In the context of the MSc in Telecommunications and Computer Engineering, at ISCTE - Instituto Universitário de Lisboa.

By João Pedro Seara, supervised by teacher Carlos Serrão (PhD), 2023

__

**Instructions (tested on Ubuntu 20.04 "Focal")**

 - Install and configure: `sudo ./siaas_server_install_and_configure.sh`

 - Start: `sudo systemctl start siaas-server` or `sudo ./siaas_server_run.sh`

 - Stop: `sudo systemctl stop siaas-server` or `sudo ./siaas_server_kill.sh`

 - Logs: `tail -100f /var/log/siaas-server/siaas-server.log` or `tail -100f ./log/siaas-server.log`

 - Generate a project archive (it is recommended to stop all processes before): `sudo ./siaas_server_archive.sh`

 - Remove: `sudo ./siaas_server_remove.sh`
