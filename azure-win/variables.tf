variable "tenant_id" {}
variable "client_id" {}
variable "client_secret" {}

variable public_key_location {
    description = "Specify location for your public key generated via (ssh-keygen)"
    default = "~/.ssh/id_rsa.pub"
}

variable private_key_location {
    description = "Specify location for your private key generated via (ssh-keygen)"
    default = "~/.ssh/id_rsa"
}

variable user {
    description = "Specify user's name that will be used for creating VM's"
    default = "automation"
}

variable password {
    description = " Specify password"
    default = "N@rahari12345!"
}

variable prefix {
    description = "The prefix which should be used for all resources"
    default = "automation"
}

variable "location" {
  description = "The Azure Region in which all resources in this example should be created."
  default = "westeurope"
}

variable "vpc_cidr_block" {
    description = "specify VPC cidr block"
    default = "10.0.0.0/16"
}

variable "subnet_cidr_block" {
    description = "specify subnet cidr block"
    default = "10.0.0.0/24"
}

variable "publisher" {
     description = "specify source image reference publisher" 
     default = "MicrosoftWindowsServer" 
}

variable "offer" {  
    description = "specify source image reference offer"
    default     = "WindowsServer" 
}

variable "sku" {  
    description = "specify source image reference sku" 
    default       = "2019-Datacenter" 
}

variable "image_version" { 
    description = "specify source image reference version"
    default   = "latest" 
}

variable vm_size {
    description = "Specify vm size"
    default = "Standard_DS1_v2"
}
variable ansible_command {
    description = "Command to pass variables to ansible playbook"   
}