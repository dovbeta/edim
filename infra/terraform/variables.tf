variable "aws_region" {
  default = "eu-central-1"
}

variable "instance_type" {
  default = "t3.small"
}

variable "key_name" {
  description = "AWS key pair name"
}

variable "ami" {
  description = "Ubuntu AMI"
  default     = "ami-0e872aee57663ae2d"
}