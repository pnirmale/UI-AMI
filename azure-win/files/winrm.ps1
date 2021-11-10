Write-Host "Create a new WinRM listener and configure"
winrm create winrm/config/listener?Address=*+Transport=HTTP
winrm set winrm/config/winrs '@{MaxMemoryPerShellMB="0"}'
winrm set winrm/config '@{MaxTimeoutms="7200000"}'
winrm set winrm/config/service '@{AllowUnencrypted="true"}'
winrm set winrm/config/service '@{MaxConcurrentOperationsPerUser="12000"}'
winrm set winrm/config/service/auth '@{Basic="true"}'
winrm set winrm/config/client/auth '@{Basic="true"}'

Write-Host "Configure UAC to allow privilege elevation in remote shells"
$Key = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System'
$Setting = 'LocalAccountTokenFilterPolicy'
Set-ItemProperty -Path $Key -Name $Setting -Value 1 -Force

Write-Host "turn off PowerShell execution policy restrictions"
Set-ExecutionPolicy -ExecutionPolicy Unrestricted

Write-Host "Configure and restart the WinRM Service; Enable the required firewall exception"
Stop-Service -Name WinRM
Set-Service -Name WinRM -StartupType Automatic
netsh advfirewall firewall set rule name="Windows Remote Management (HTTP-In)" new action=allow localip=any remoteip=any
Start-Service -Name WinRM

Write-Host "Config custom"
$url = "https://raw.githubusercontent.com/ansible/ansible/devel/examples/scripts/ConfigureRemotingForAnsible.ps1"
$file = "$env:temp\ConfigureRemotingForAnsible.ps1"
(New-Object -TypeName System.Net.WebClient).DownloadFile($url, $file)
powershell.exe -ExecutionPolicy ByPass -File $file

$url = 'https://github.com/PowerShell/Win32-OpenSSH/releases/latest/'
## Create a web request to retrieve the latest release download link
$request = [System.Net.WebRequest]::Create($url)
$request.AllowAutoRedirect=$false
$response=$request.GetResponse()
$source = $([String]$response.GetResponseHeader("Location")).Replace('tag','download') + '/OpenSSH-Win64.zip'
## Download the latest OpenSSH for Windows package to the current working directory
$webClient = [System.Net.WebClient]::new()
$webClient.DownloadFile($source, (Get-Location).Path + '\OpenSSH-Win64.zip')

Get-ChildItem *.zip
# Extract the ZIP to a temporary location
Expand-Archive -Path .\OpenSSH-Win64.zip -DestinationPath ($env:temp) -Force
# Move the extracted ZIP contents from the temporary location to C:\Program Files\OpenSSH\
Move-Item "$($env:temp)\OpenSSH-Win64" -Destination "C:\Program Files\OpenSSH\" -Force
# Unblock the files in C:\Program Files\OpenSSH\
Get-ChildItem -Path "C:\Program Files\OpenSSH\" | Unblock-File
& 'C:\Program Files\OpenSSH\install-sshd.ps1'
Set-Service sshd -StartupType Automatic
Start-Service sshd
New-NetFirewallRule -Name sshd -DisplayName 'Allow SSH' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22