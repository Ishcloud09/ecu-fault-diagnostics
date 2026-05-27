variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "eu-west-2"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "ecu-fault-diagnostics"
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name for fault history"
  type        = string
  default     = "ECUFaultHistory"
}

variable "iot_thing_name" {
  description = "AWS IoT Thing name for simulated ECU"
  type        = string
  default     = "simulated-ecu-01"
}

variable "lambda_function_name" {
  description = "Lambda function name"
  type        = string
  default     = "ecu-fault-processor"
}