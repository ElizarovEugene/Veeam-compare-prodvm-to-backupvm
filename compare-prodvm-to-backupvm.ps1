Get-Module -ListAvailable -Name Veeam.Backup.PowerShell | Import-Module -ea SilentlyContinue 
Get-Module -Name VMware* -ListAvailable | Import-Module -ea SilentlyContinue 

$vmhash = @{};

$viservers = ('vcenter_IP1', 'vcenter_IP2', 'vcenter_IP3')
foreach ($viserver in $viservers) {
    Connect-VIServer $viserver -User USER -Password PASSWORD
    Get-VM | sort Name | %{ $vmhash[$_.Name] = @{}; $vmhash[$_.Name][0] = $_.ResourcePool.Name ; $vmhash[$_.Name][1] = $viserver }
    Disconnect-VIServer $viserver -Confirm:$false
}

$vbrservers = ('vbr_IP1', 'vbr_IP2')
foreach ($vbrserver in $vbrservers)
{
    Connect-VBRServer -Server $vbrserver -User USER -Password PASSWORD
    foreach($job in Get-VBRBackup)
    {
	   ($job).GetObjectOibsAll() | %{ if ($_.VmName) { if ($vmhash[$_.VmName]) {$vmhash[ $_.VmName ][2] += $job.Name + ', '  } } } 
    }
    Disconnect-VBRServer
}

Remove-Item –path 'C:\backupvms.csv'
foreach ($vm in $vmhash.keys)
{
    $vm + ';' + $vmhash[$vm][0] + ';' + $vmhash[$vm][1] + ';' + $vmhash[$vm][2] >> 'C:\backupvms.csv'
} 
