variable "access_key" {
    description = "Specify aws ACCESS_KEY"
    
   
}

variable "secret_key" {
    description = "Specify aws SECRET_ACCESS_KEY"
    
}

variable public_key_location {
    description = "Specify location for your public key generated via (ssh-keygen)"
    default = "~/.ssh/id_rsa.pub"
}

variable private_key_location {
    description = "Specify location for your private key generated via (ssh-keygen)"
    default = "~/.ssh/id_rsa"
}

variable prefix {
    description = "The prefix which should be used for all resources"
    default = "automation"
}

variable vpc_cidr_block {
    description = "Specify vpc cidr block"
    default = "10.0.0.0/16"
}

variable subnet_cidr_block {
    description = "Specify subnet cidr block"
    default = "10.0.10.0/24"
}

variable avail_zone {
    description = "Specify availability zone"
    default = "ap-south-1a"
}

variable "region" {
    description = " Specify region"
    default = "ap-south-1"
}

variable "ami_id" {
    description = "Specify linux ami id"
    default = "ami-0c1a7f89451184c8b"
}

variable user {
    description = "Specify default user associated with given ami_id"
    default = "ubuntu"
}

variable instance_type {
    description = "Specify instance type"
    default = "t2.micro"
}