output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = aws_dynamodb_table.fault_history.name
}

output "dynamodb_table_arn" {
  description = "DynamoDB table ARN"
  value       = aws_dynamodb_table.fault_history.arn
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.fault_processor.function_name
}

output "lambda_function_arn" {
  description = "Lambda function ARN"
  value       = aws_lambda_function.fault_processor.arn
}

output "iot_thing_name" {
  description = "IoT Thing name"
  value       = aws_iot_thing.simulated_ecu.name
}

output "iot_policy_name" {
  description = "IoT Policy name"
  value       = aws_iot_policy.ecu_policy.name
}