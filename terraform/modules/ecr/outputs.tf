output "frontend_repository_url" {
  description = "Repository URL for Frontend container image"
  value       = aws_ecr_repository.frontend.repository_url
}

output "backend_repository_url" {
  description = "Repository URL for Backend container image"
  value       = aws_ecr_repository.backend.repository_url
}