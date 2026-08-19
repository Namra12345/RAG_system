module "vpc" {
  source   = "./modules/vpc"
  app_name = var.app_name
}

module "ecr" {
  source   = "./modules/ecr"
  app_name = var.app_name
}

module "ec2" {
  source           = "./modules/ec2"
  app_name         = var.app_name
  vpc_id           = module.vpc.vpc_id
  public_subnet_id = module.vpc.public_subnet_id
  instance_type    = var.instance_type
}