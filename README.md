# Veeam compare prod vm to backuped vm
Script for searching productive VMs from VMware in backup tasks. You can use several servers of vCenter and/or several servers VBR. At the output, you will receive a CSV file with the following contents. If the virtual machine is in multiple tasks, the script also recognizes such situations.

| VM name  | Resource Pool | vCenter IP | Job name|
| ------------- | ------------- |------------- |------------- |
| VM1  | Pool1  | 192.168.1.200| Job A |
| VM2  | Pool1  | 192.168.1.200| Job A |
| VM3  | Pool1  | 192.168.1.210| Job B |
| VM4  | Pool2  | 192.168.1.210| Job A, Job B |


Required for work PowerCli and Veeam.Backup.PowerShell for PS servion

Required for work pyVmomi for Python vervion. Use:
```
pip install -r requirements.txt
```
