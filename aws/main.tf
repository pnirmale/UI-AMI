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
        from_port = 22
        to_port = 22
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    ingress {
        from_port = 8080
        to_port = 8080
        protocol = "tcp"
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

  provisioner "remote-exec" {
  
    inline = [
     "mkdir newDir",
     "rmdir newDir"
    ]
    
    connection {
      type = "ssh"
      host = self.public_ip
      user = var.user
      private_key = file(var.private_key_location)
    }
  }

  provisioner "local-exec" {
    command = "ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -u ${var.user}   -i ${self.public_ip}, --private-key ${var.private_key_location} ../ansible/linux_playbook.yml"
  }

  tags = {
    Name = "${var.prefix}-Terraform"
  }
}

resource "aws_ami_from_instance" "ami" {
  name               = "linux_ami"
  source_instance_id = aws_instance.web.id
  depends_on = [
    aws_instance.web
  ]
}