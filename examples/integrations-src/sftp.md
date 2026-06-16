# Partner SFTP
Nightly file exchange with the billing partner over SFTP (host sftp.partner.com, key-based
auth). We drop CSV invoices to /outbound at 02:00 UTC and pick up acknowledgements from
/inbound. Failures retry 3x then alert #ops.
