module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = "my-vpc"
  cidr = var.vpc_cidr_block

  azs             = [var.avail_zone]
  public_subnets  = [var.subnet_cidr_block]

  public_subnet_tags = {
      Name = "${var.prefix}-subnet-1"
  }

  tags = {
      Name = "${var.prefix}-vpc"
  }
}

resource aws_security_group "myapp-sg" {
    vpc_id =  module.vpc.vpc_id
    name = "${var.prefix}-sg"

    ingress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }

    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]
        prefix_list_ids = []
    }

    tags = {
        Name = "${var.prefix}-default-sg"
    }
}

resource "aws_key_pair" "deployer" {
  key_name   = "${var.prefix}-key"
  public_key = file(var.public_key_location)
}

resource "aws_instance" "web" {

  ami           = var.ami_id
  instance_type = var.instance_type

  key_name = aws_key_pair.deployer.key_name

  subnet_id = module.vpc.public_subnets[0]
  availability_zone = var.avail_zone
  vpc_security_group_ids = [aws_security_group.myapp-sg.id]
  associate_public_ip_address = true

   user_data     = <<EOF
    <powershell>
    net user ${var.user} '${var.password}' /add /y
    net localgroup administrators ${var.user} /add
    winrm quickconfig -q
    winrm set winrm/config/winrs '@{MaxMemoryPerShellMB="300"}'
    winrm set winrm/config '@{MaxTimeoutms="1800000"}'
    winrm set winrm/config/service '@{AllowUnencrypted="true"}'
    winrm set winrm/config/service/auth '@{Basic="true"}'
    netsh advfirewall firewall add rule name="WinRM 5985" protocol=TCP dir=in localport=5985 action=allow
    netsh advfirewall firewall add rule name="WinRM 5986" protocol=TCP dir=in localport=5986 action=allow
    net stop winrm
    sc.exe config winrm start=auto
    net start winrm
    
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
    </powershell>
    EOF

  provisioner "remote-exec" {
    connection {
      host     = coalesce(self.public_ip, self.private_ip)
      type     = "winrm"
      port     = 5985
      https    = false
      timeout  = "5m"
      user     = "${var.user}"
      password = "${var.password}"
    }
    inline = [
      "mkdir helloworld",
    ]
  }
  provisioner "local-exec" {
    command="echo ansible_host_1 ansible_host=${self.public_ip} ansible_user=${var.user} ansible_password=${var.password} ansible_connection=${var.connection_type} ansible_winrm_server_cert_validation=ignore ansible_port=5985 > hosts"
  }
  provisioner "local-exec" {
    command = format("%s %s","ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i hosts  ../ansible/windows_playbook.yml",var.ansible_command)
  }
  provisioner "local-exec" {
    command = "rm -rf hosts"
  }

  tags = {
    Name = "${var.prefix}-Terraform"
  }
}

resource "aws_ami_from_instance" "ami" {
  name               = "win_ami"
  source_instance_id = aws_instance.web.id
  depends_on = [
    aws_instance.web
  ]
}