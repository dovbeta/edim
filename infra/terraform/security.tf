resource "aws_security_group" "edim_sg" {

  name = "edim-security-group"

  ingress {

    description = "SSH"

    from_port   = 22
    to_port     = 22
    protocol    = "tcp"

    cidr_blocks = ["0.0.0.0/0"]

  }

  ingress {

    description = "API"

    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"

    cidr_blocks = ["0.0.0.0/0"]

  }

  egress {

    from_port   = 0
    to_port     = 0
    protocol    = "-1"

    cidr_blocks = ["0.0.0.0/0"]

  }

}