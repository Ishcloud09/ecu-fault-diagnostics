# P1 — Systems Requirements Specification
## AI-Assisted ECU Fault Diagnostics Pipeline

> This document maps each architectural decision in the pipeline
> to a systems engineering rationale — connecting implementation
> choices to compliance principles and operational requirements.

---

## SR-01 — Message Durability Under Burst Traffic

**Requirement:** No fault message shall be lost during peak fleet
reporting periods, even if processing capacity is temporarily exceeded.

**Design decision:** SQS queue with Dead Letter Queue (maxReceiveCount: 3)
between IoT Core and Lambda.

**Rationale:** Decouples ingestion rate from processing rate. Messages
queue durably regardless of Lambda concurrency. DLQ captures messages
that fail after 3 retries for investigation — no silent loss.

**Verification:** DLQ CloudWatch alarm fires if any message reaches
the dead letter queue. SQS ApproximateNumberOfMessages monitored
to detect processing backlogs.

---

## SR-02 — Device Identity Verification

**Requirement:** Only authenticated, registered devices shall be
permitted to publish fault data to the cloud backend.

**Design decision:** Mutual TLS authentication using X.509 certificates
with AWS IoT Core. Each device has a unique certificate attached to
an IoT Policy scoped to its specific client ID and topic.

**Rationale:** Aligned to UN R155 (Cybersecurity Management System)
communication security requirements. Prevents spoofed or malicious
devices from injecting false fault data into the diagnostic pipeline.
Certificates can be individually revoked per device without affecting
the fleet.

**Verification:** IoT Core rejects any connection without a valid,
active, policy-attached certificate. Certificate status monitored
in IoT Core console.

---

## SR-03 — Least Privilege Access Control

**Requirement:** Each component shall have only the minimum permissions
required to perform its specific function.

**Design decision:** Separate IAM roles and inline policies for each
service. Lambda execution role grants only dynamodb:PutItem/GetItem/Query
on the specific ECUFaultHistory table ARN, and sqs:ReceiveMessage/
DeleteMessage on the specific fault queue ARN.

**Rationale:** Security boundary definition aligned to UN R155
cybersecurity principles. Limits blast radius if any credential
is compromised — Lambda credentials cannot affect IoT, S3, or
other unrelated services.

**Verification:** IAM policy simulator confirms permissions are
scoped correctly. No wildcard resource ARNs in production policies.

---

## SR-04 — Pipeline Failure Detection

**Requirement:** Processing failures shall be detected and alerted
within 5 minutes of occurrence.

**Design decision:** Two CloudWatch alarms — Lambda Errors metric
(threshold: > 0 in 5-minute window) and SQS DLQ ApproximateNumberOfMessages
(threshold: > 0 in 5-minute window). Both route to SNS topic with
email subscription.

**Rationale:** Observability requirement for production IoT systems.
Dual alarm approach covers both immediate processing failures (Lambda
errors) and repeated failure patterns (DLQ accumulation) — different
failure modes requiring different investigation paths.

**Verification:** Alarm tested during Day 8 build by deliberately
misconfiguring DynamoDB table name — alarm fired within 5 minutes,
email received at ish.cloudwork@gmail.com confirming end-to-end
alert path.

---

## SR-05 — Network Isolation and Traffic Control

**Requirement:** Processing components shall not be directly
accessible from the public internet, and AWS service traffic
shall not traverse the public internet unnecessarily.

**Design decision:** Lambda deployed in private VPC subnets
(eu-west-2a, eu-west-2b) with no inbound internet access.
DynamoDB Gateway Endpoint and SQS Interface Endpoint route
AWS service traffic through AWS private network. NAT Gateway
provides outbound-only internet access for external API calls.

**Rationale:** Network segmentation principle aligned to
UN R155 cybersecurity requirements. Reduces attack surface —
Lambda cannot be reached from internet, AWS service traffic
never traverses public network, only external dependency
(Claude API) uses NAT Gateway.

**Verification:** Security group has no inbound rules.
VPC flow logs would confirm traffic routing in production.
DynamoDB and SQS traffic confirmed to bypass NAT Gateway
via VPC Endpoint route table entries.

---

## SR-06 — Infrastructure Reproducibility

**Requirement:** The complete pipeline infrastructure shall be
reproducible from source code without manual console configuration.

**Design decision:** All 15 AWS resources defined in Terraform HCL
(main.tf, variables.tf, outputs.tf). State managed in terraform.tfstate.
GitHub Actions CI/CD deploys Lambda automatically on every push to main.

**Rationale:** Eliminates configuration drift — the code is the
single source of truth for infrastructure state. Supports disaster
recovery, environment replication, and audit requirements. Demonstrates
DevSecOps maturity aligned to modern automotive software delivery.

**Verification:** terraform destroy followed by terraform apply
successfully rebuilds all 15 resources from scratch. GitHub Actions
pipeline deploys in 43 seconds with zero manual intervention.

---

## SR-07 — AI Diagnosis Traceability

**Requirement:** Every AI diagnosis shall be traceable to the
specific fault event, sensor context, and prompt used to generate it.

**Design decision:** DynamoDB record stores fault_id (partition key),
timestamp (sort key), original sensor_data, ai_diagnosis (structured),
processed_at, and prompt_used fields together in a single record.

**Rationale:** Audit and traceability requirement. In a production
connected vehicle system, AI diagnostic decisions must be explainable
and auditable — regulators, insurers, and OEM quality teams need
to understand why a specific diagnosis was generated for a specific
fault event at a specific moment.

**Verification:** DynamoDB records inspected — all fields present
per fault_schema.json specification. prompt_used field confirms
exact input to AI classifier for every record.

---

## Compliance Alignment Summary

| Requirement | Standard | Implementation |
|---|---|---|
| Device authentication | UN R155 — communication security | Mutual TLS, X.509, IoT Policy |
| Least privilege access | UN R155 — cybersecurity principles | Scoped IAM policies per service |
| Network segmentation | UN R155 — attack surface reduction | Private VPC, VPC Endpoints |
| Failure detection | Production IoT observability | CloudWatch alarms, SNS alerts |
| Message integrity | Fleet data reliability | SQS DLQ, retry policy |
| Infrastructure audit | DevSecOps, ISO 27001 alignment | Terraform IaC, GitHub Actions |
| AI decision traceability | Emerging AI governance | Full audit trail in DynamoDB |