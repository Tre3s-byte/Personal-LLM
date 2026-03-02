# Security Policy

## Scope

Personal AI Server is designed for private/self-hosted environments with strong local control.

## Supported Security Posture

Current security model emphasizes:
- Authenticated API access (JWT-based pattern)
- Restricted filesystem access via allowlists
- Restricted automation actions via predefined command mapping
- VPN-first remote access strategy

## Responsible Disclosure

If you discover a vulnerability, please report it privately to the repository maintainer.

Include:
- Affected component(s)
- Reproduction steps
- Impact assessment
- Suggested remediation (optional)

Please do **not** open a public issue with exploit details before maintainers can patch.

## Hardening Recommendations

- Never expose backend directly to the public internet without additional controls.
- Use a private overlay network (for example Tailscale).
- Store secrets in environment variables, never in source control.
- Rotate JWT secrets and API credentials periodically.
- Keep dependencies updated and pin production versions.

## Secure Development Checklist

- Validate all user-provided paths and inputs.
- Enforce allowlists for file and automation operations.
- Avoid arbitrary command execution pathways.
- Log security-relevant events (auth failures, denied actions).
- Review endpoint auth requirements whenever adding new routes.
