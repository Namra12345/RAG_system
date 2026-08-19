output "ec2_public_ip" {
  description = "Public IP of EC2 Instance for live app access"
  value       = module.ec2.public_ip
}

output "ecr_frontend_repository_url" {
  description = "Target ECR URL for Frontend"
  value       = module.ecr.frontend_repository_url
}

output "ecr_backend_repository_url" {
  description = "Target ECR URL for Backend"
  value       = module.ecr.backend_repository_url
}