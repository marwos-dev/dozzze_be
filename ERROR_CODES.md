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
