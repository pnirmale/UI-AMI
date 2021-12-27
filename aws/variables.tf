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
    default = "us-east-1a"
}

variable "region" {
    description = " Specify region"
    default = "us-east-2"
}

variable "ami_id" {
    description = "Specify linux ami id"
    default = "ami-074cce78125f09d61"
}

variable user {
    description = "Specify default user associated with given ami_id"
    default = "ec2-user"
}

variable instance_type {
    description = "Specify instance type"
    default = "t2.micro"
}

variable ansible_command {
    description = "Command to execute ansible playbook"
    
}