variable "app_name" {
  description = "Application name prefix for EC2 resources"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where the EC2 instance and Security Group will reside"
  type        = string
}

variable "public_subnet_id" {
  description = "Public Subnet ID where the EC2 instance is launched"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance size"
  type        = string
}