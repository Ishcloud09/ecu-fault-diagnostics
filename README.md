# ECU Fault Diagnostics — AI-Assisted Pipeline

A system that simulates CAN bus vehicle fault data, streams it to 
AWS IoT Core in real time, and uses AI to automatically classify 
and explain ECU fault codes — mimicking the diagnostic automation 
used by automotive OEMs for connected vehicle fleets.

## Problem It Solves
Modern connected vehicles generate thousands of fault events per day 
across a fleet. Manual diagnosis by technicians cannot scale to this 
volume. This pipeline automates fault classification and root cause 
analysis using AI, reducing diagnostic time from 30+ minutes to 
under 3 seconds per fault.

## Architecture
Python CAN Simulator → MQTT → AWS IoT Core → Lambda → AI API → DynamoDB

## Tech Stack
- **Python** — CAN bus fault simulator
- **AWS IoT Core + MQTT** — real-time message streaming
- **AWS Lambda** — serverless fault processing
- **Claude/OpenAI API** — AI fault classification and root cause analysis
- **AWS DynamoDB** — fault history and diagnosis storage
- **Terraform** — infrastructure as code
- **GitHub Actions** — CI/CD pipeline

## Status
🔧 In progress — Day 1 environment setup complete

## How to Run (coming soon)
Instructions will be added as each phase is completed.

## Author
Iswarya Thiagarajan  
[LinkedIn](#) | [GitHub](#)