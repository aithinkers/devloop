# Transactional Email
Outbound email goes through AWS SES in us-east-1. Sending domain is mail.acme.com (DKIM +
SPF configured). Templates live in the notifications service. Bounces and complaints are
processed via an SNS topic. Daily send limit is 200k.
