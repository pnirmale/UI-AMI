resource "azurerm_resource_group" "main" {
  name     = "${var.prefix}-resources"
  location = var.location
}

resource "azurerm_virtual_network" "main" {
  name                = "${var.prefix}-network"
  address_space       = [var.vpc_cidr_block]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
}

resource "azurerm_network_security_group" "example" {
  name                = "${var.prefix}-sg"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  security_rule {
    name                       = "RDP"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "3389"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  security_rule {
    name                       = "WinRM"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "5985"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  security_rule {
    name                       = "WinRM-https"
    priority                   = 200
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "5986"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  security_rule {
    name                       = "HTTP"
    priority                   = 120
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
  security_rule {
    name                       = "SSH"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "22"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = {
    environment = "DEV"
  }
}

resource "azurerm_subnet" "internal" {
  name                 = "${var.prefix}-subnet"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = [var.subnet_cidr_block]
}

resource "azurerm_public_ip" "main" {
  name                = "${var.prefix}-pip"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  allocation_method   = "Static"
}

resource "azurerm_network_interface" "main" {
  name                = "${var.prefix}-nic"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  ip_configuration {
    name                          = "${var.prefix}-ip-conf"
    subnet_id                     = azurerm_subnet.internal.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.main.id
  }
}

resource "azurerm_network_interface_security_group_association" "example" {
  network_interface_id      = azurerm_network_interface.main.id
  network_security_group_id = azurerm_network_security_group.example.id
}

resource "azurerm_virtual_machine" "main" {
  name                            = "${var.prefix}-vm"
  resource_group_name             = azurerm_resource_group.main.name
  location                        = azurerm_resource_group.main.location
  vm_size                         = var.vm_size

  delete_os_disk_on_termination = true
  delete_data_disks_on_termination = true

  network_interface_ids = [
    azurerm_network_interface.main.id,
  ]

  storage_image_reference {
    publisher = var.publisher
    offer     = var.offer
    sku       = var.sku
    version   = var.image_version
  }

  storage_os_disk {
    name              = "${var.prefix}OS"
    caching           = "ReadWrite"
    create_option     = "FromImage"
    managed_disk_type = "Standard_LRS"
  }
  
  os_profile {
    computer_name  = "${var.user}"
    admin_username = "${var.user}"
    admin_password = "${var.password}"
    custom_data    = "${file("./files/winrm.ps1")}"
  }
  os_profile_windows_config {
    provision_vm_agent = "true"
    timezone           = "Romance Standard Time"
    winrm {
      protocol = "http"
    }
    # Auto-Login's required to configure WinRM
    additional_unattend_config {
      pass         = "oobeSystem"
      component    = "Microsoft-Windows-Shell-Setup"
      setting_name = "AutoLogon"
      content      = "<AutoLogon><Password><Value>${var.password}</Value></Password><Enabled>true</Enabled><LogonCount>1</LogonCount><Username>${var.user}</Username></AutoLogon>"
    }
    additional_unattend_config {
      pass         = "oobeSystem"
      component    = "Microsoft-Windows-Shell-Setup"
      setting_name = "FirstLogonCommands"
      content      = "${file("./files/FirstLogonCommands.xml")}"
    }
  }

  provisioner "remote-exec" {
    connection {
      host     = "${azurerm_public_ip.main.ip_address}"
      type     = "winrm"
      port     = 5985
      https    = false
      timeout  = "5m"
      user     = "${var.user}"
      password = "${var.password}"
    }
    inline = [
      "dir",
    ]
  }
  provisioner "local-exec" {
    command="echo ansible_host_1 ansible_host=${azurerm_public_ip.main.ip_address} ansible_user=${var.user} ansible_password=${var.password} ansible_connection=winrm ansible_winrm_server_cert_validation=ignore ansible_port=5985 > hosts"
  }
  provisioner "local-exec" {
    command = "ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i hosts  ../ansible/windows_playbook.yml"
  }
  provisioner "local-exec" {
    command = "rm -rf hosts"
  }

  provisioner "local-exec" {
    command = "az login --service-principal -u ${var.client_id} --password ${var.client_secret} --tenant ${var.tenant_id}"  
  }

  provisioner "remote-exec" {
    connection {
      host     = "${azurerm_public_ip.main.ip_address}"
      type     = "winrm"
      port     = 5985
      https    = false
      timeout  = "5m"
      user     = "${var.user}"
      password = "${var.password}"
    }
    inline = [
      "C:\\Windows\\System32\\Sysprep\\Sysprep.exe /generalize /oobe /shutdown",
    ]
  }
}

resource "time_sleep" "wait_300_seconds" {
  depends_on = [azurerm_virtual_machine.main]
  create_duration = "300s"
}

resource "null_resource" "next" {
  provisioner "local-exec" {
    command = "az vm generalize --resource-group ${azurerm_resource_group.main.name} --name ${azurerm_virtual_machine.main.name}"
  }
  depends_on = [time_sleep.wait_300_seconds]
}

resource "azurerm_resource_group" "for_image_storage" {
  name     = "${var.prefix}-image-resources"
  location = var.location
}

resource "azurerm_image" "my-image" {
  name                      = "${var.prefix}-image"
  location                  = var.location
  resource_group_name       = azurerm_resource_group.for_image_storage.name
  source_virtual_machine_id = azurerm_virtual_machine.main.id

  depends_on = [null_resource.next]
}