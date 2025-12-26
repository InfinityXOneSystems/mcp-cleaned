# Security Upgrades

## API Gateway Enhancements
- Implement rate limiting using tools like `flask-limiter`.
- Add IP whitelisting for sensitive endpoints.
- Use OAuth2 for authentication and authorization.

## Environment Secrets
- Store sensitive data like API keys in Google Secret Manager.
- Update MCP system to fetch secrets dynamically at runtime.

## Audit Logging
- Log all sensitive operations, including authentication attempts, data modifications, and administrative actions.
- Use structured logging for better analysis.