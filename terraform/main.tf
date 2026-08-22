# ── PROVIDER ──
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  required_version = ">= 1.0"
}

provider "aws" {
  region = var.aws_region
}

# ── DYNAMODB TABLE ──
resource "aws_dynamodb_table" "fault_history" {
  name         = var.dynamodb_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "fault_id"
  range_key    = "timestamp"

  attribute {
    name = "fault_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  tags = {
    Project     = var.project_name
    Environment = "portfolio"
    ManagedBy   = "terraform"
  }
}

# ── SQS DEAD LETTER QUEUE ──
resource "aws_sqs_queue" "fault_dlq" {
  name                      = "${var.project_name}-fault-dlq"
  message_retention_seconds = 86400

  tags = {
    Project   = var.project_name
    ManagedBy = "terraform"
  }
}

# ── SQS MAIN FAULT QUEUE ──
resource "aws_sqs_queue" "fault_queue" {
  name                       = "${var.project_name}-fault-queue"
  visibility_timeout_seconds = 35
  message_retention_seconds  = 86400

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.fault_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Project   = var.project_name
    ManagedBy = "terraform"
  }
}

# ── IAM ROLE FOR IOT → SQS ──
resource "aws_iam_role" "iot_sqs_role" {
  name = "${var.project_name}-iot-sqs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "iot.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = {
    Project   = var.project_name
    ManagedBy = "terraform"
  }
}

resource "aws_iam_role_policy" "iot_sqs_policy" {
  name = "${var.project_name}-iot-sqs-policy"
  role = aws_iam_role.iot_sqs_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "sqs:SendMessage"
      Resource = aws_sqs_queue.fault_queue.arn
    }]
  })
}

# ── IAM ROLE FOR LAMBDA ──
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })

  tags = {
    Project   = var.project_name
    ManagedBy = "terraform"
  }
}

# ── IAM POLICY FOR LAMBDA ──
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DynamoDBAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = aws_dynamodb_table.fault_history.arn
      },
      {
        Sid    = "SQSAccess"
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.fault_queue.arn
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:*:*"
      }
    ]
  })
}

# ── ATTACH BASIC LAMBDA EXECUTION POLICY ──
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# ── LAMBDA FUNCTION ──
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda"
  output_path = "${path.module}/lambda_deploy.zip"
  excludes    = ["lambda_deploy.zip", "__pycache__"]
}

resource "aws_lambda_function" "fault_processor" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = var.lambda_function_name
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambda_function.handler"
  runtime          = "python3.11"
  timeout          = 30
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE  = var.dynamodb_table_name
      AWS_REGION_NAME = var.aws_region
      MOCK_MODE       = "true"
    }
  }

  tags = {
    Project   = var.project_name
    ManagedBy = "terraform"
  }
}

# ── LAMBDA READS FROM SQS ──
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.fault_queue.arn
  function_name    = aws_lambda_function.fault_processor.arn
  batch_size       = 10
  enabled          = true
}

# ── IOT POLICY ──
resource "aws_iot_policy" "ecu_policy" {
  name = "ecu-simulator-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "iot:Connect"
        Resource = "arn:aws:iot:${var.aws_region}:*:client/${var.iot_thing_name}"
      },
      {
        Effect   = "Allow"
        Action   = "iot:Publish"
        Resource = "arn:aws:iot:${var.aws_region}:*:topic/ecu/faults"
      },
      {
        Effect   = "Allow"
        Action   = "iot:Subscribe"
        Resource = "arn:aws:iot:${var.aws_region}:*:topicfilter/ecu/faults"
      },
      {
        Effect   = "Allow"
        Action   = "iot:Receive"
        Resource = "arn:aws:iot:${var.aws_region}:*:topic/ecu/faults"
      }
    ]
  })
}

# ── IOT THING ──
resource "aws_iot_thing" "simulated_ecu" {
  name = var.iot_thing_name

  attributes = {
    vehicle_type = "simulated"
    project      = var.project_name
  }
}

# ── IOT RULE → SQS ──
resource "aws_iot_topic_rule" "fault_rule" {
  name        = "ProcessECUFault"
  enabled     = true
  sql         = "SELECT * FROM 'ecu/faults'"
  sql_version = "2016-03-23"

  sqs {
    queue_url  = aws_sqs_queue.fault_queue.url
    role_arn   = aws_iam_role.iot_sqs_role.arn
    use_base64 = false
  }

  tags = {
    Project   = var.project_name
    ManagedBy = "terraform"
  }
}

# ── CLOUDWATCH ALARM — LAMBDA ERRORS ──
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "ECU-Lambda-Error-Alert"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "Alert when Lambda function throws errors"

  dimensions = {
    FunctionName = var.lambda_function_name
  }

  tags = {
    Project   = var.project_name
    ManagedBy = "terraform"
  }
}

# ── CLOUDWATCH ALARM — DLQ MESSAGES ──
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  alarm_name          = "ECU-DLQ-Messages-Alert"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "Faults landing in DLQ after 3 failed retries"

  dimensions = {
    QueueName = aws_sqs_queue.fault_dlq.name
  }

  tags = {
    Project   = var.project_name
    ManagedBy = "terraform"
  }
}