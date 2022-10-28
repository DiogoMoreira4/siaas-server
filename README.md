# siaas-server

_Intelligent System for Automation of Security Audits (SIAAS) - Server Module_

In the context of the MSc in Telecommunications and Computer Engineering, at ISCTE - Instituto Universitário de Lisboa.

By João Pedro Seara, supervised by teacher Carlos Serrão (PhD).

__

**Instructions (tested on Ubuntu 20.04 "Focal")**

 - Set up system and Pyhon packages: `sudo ./siaas_server_install_and_configure.sh`
 
 - How to initialize MongoDB: `sudo ./siaas_server_initialize_mongodb.sh`

 - How to run: `sudo ./siaas_server_run.sh`

 - How to stop: `sudo ./siaas_server_kill.sh`

 - RECOMMENDED WAY TO START/STOP SERVICES: `sudo systemctl [start/stop/restart] siaas-server`

 - Logs: `tail -100f /var/log/siaas/siaas-server.log`

 - How to generate a project archive (it is recommended to stop all processes before): `sudo ./siaas_server_archive.sh`
