provider "aws" {
  region = var.aws_region
}

resource "aws_instance" "edim_server" {

  ami           = var.ami
  instance_type = var.instance_type

  key_name = var.key_name

  vpc_security_group_ids = [
    aws_security_group.edim_sg.id
  ]

  user_data = file("${path.module}/user_data.sh")

  tags = {
    Name = "edim-server"
  }
}