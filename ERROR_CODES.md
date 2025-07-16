# Error Codes Reference

This project uses numeric codes to help the frontend understand the reason behind a failed request. These codes are returned inside the `code` field of `ErrorSchema` responses.

## Reservation Errors (100-199)

| Code | Meaning |
|------|---------|
|100|Unknown reservation error|
|101|No availability for the selected dates|
|102|Invalid check-in/check-out dates|
|103|Payment failure or invalid signature|
|104|Reservation or property not found|

The frontend can map these codes to custom messages for the user.

## Property Errors (200-299)

| Code | Meaning |
|------|---------|
|200|Invalid check-in date|
|201|Check-in date cannot be after check-out date|
|202|Property not found|
|203|Could not parse rates|
|204|No price found for requested guests|
|205|No availability for the selected dates|
|206|Room not found|
|207|Zone ID or Property ID is required|

## Customer Errors (300-399)

| Code | Meaning |
|------|---------|
|300|Email already exists|
|301|User is inactive|
|302|Invalid credentials|
|303|User not found|
|304|User not authenticated|
|305|Refresh token invalid or expired|
|306|Token invalid or expired|

## Security Errors (400-499)

| Code | Meaning |
|------|---------|
|400|Access denied|
