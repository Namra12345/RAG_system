output "public_ip" {
  description = "Public IP address assigned to the EC2 server"
  value       = aws_instance.app_server.public_ip
}