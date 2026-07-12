# StadiumOS AI - Security Documentation

## Authentication Flow

```
┌──────────┐      ┌──────────────┐      ┌───────────────┐
│  Client   │─────→│  OAuth2 /    │─────→│  Identity     │
│           │      │  Identity    │      │  Platform     │
│           │←─────│  Platform    │←─────│  (Google)     │
└─────┬─────┘      └──────────────┘      └───────────────┘
      │
      │ JWT access_token + refresh_token
      ▼
┌─────────────────────────────────────────────────────────┐
│                    API Request                           │
│  Authorization: Bearer <access_token>                   │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              JWT VERIFICATION                           │
│  1. Validate signature (HS256)                          │
│  2. Check expiration (exp claim)                        │
│  3. Verify token type (access vs refresh)               │
│  4. Extract payload (sub, role, stadium_id)             │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              ROLE-BASED ACCESS CONTROL                  │
│  Map role → permitted endpoints                         │
└─────────────────────────────────────────────────────────┘
```

### Token Structure

**Access Token** (expires in 60 minutes):
```json
{
  "sub": "user-uuid",
  "exp": 1689000000,
  "iat": 1688996400,
  "type": "access",
  "role": "FAN",
  "stadium_id": "stadium-uuid",
  "jti": "user-uuid_1688996400"
}
```

**Refresh Token** (expires in 7 days):
```json
{
  "sub": "user-uuid",
  "exp": 1689604800,
  "iat": 1688996400,
  "type": "refresh",
  "role": "FAN",
  "stadium_id": "stadium-uuid",
  "jti": "refresh_user-uuid_1688996400"
}
```

### Token Lifecycle

1. **Issuance**: Client authenticates via OAuth2 → receives access + refresh tokens
2. **Usage**: Client sends access token in `Authorization: Bearer <token>` header
3. **Refresh**: When access token expires, client uses refresh token to get new access token
4. **Revocation**: Tokens cannot be revoked server-side (stateless JWT); short expiry mitigates risk

---

## Authorization Model

### Role Hierarchy

```
ADMIN
  ├── SECURITY
  ├── MEDICAL
  ├── STAFF
  ├── VOLUNTEER
  └── FAN (lowest)
```

### Endpoint Permissions

| Endpoint | FAN | STAFF | ADMIN | SECURITY | MEDICAL |
|----------|-----|-------|-------|----------|---------|
| `POST /chat` | R | R | R | R | R |
| `GET /chat/*` | R | R | R | R | R |
| `POST /alerts` | R | RW | RW | RW | R |
| `GET /alerts` | R | R | R | R | R |
| `POST /alerts/{id}/escalate` | - | RW | RW | RW | - |
| `POST /alerts/{id}/resolve` | - | RW | RW | RW | - |
| `POST /incidents` | R | RW | RW | RW | R |
| `POST /incidents/{id}/assign` | - | RW | RW | RW | - |
| `POST /incidents/{id}/resolve` | - | RW | RW | RW | - |
| `GET /dashboard/*` | - | RW | RW | RW | RW |
| `POST /events` | - | RW | RW | - | - |
| `POST /feedback` | RW | RW | RW | RW | RW |
| `POST /speech/*` | R | R | R | R | R |
| `POST /translation/*` | R | R | R | R | R |
| `POST /vision/*` | - | RW | RW | RW | - |
| `POST /notifications/send` | - | RW | RW | RW | - |
| `POST /notifications/broadcast` | - | - | RW | RW | - |

**R** = Read, **RW** = Read/Write, **-** = No access

---

## Data Encryption

### At Rest
- **Firestore**: All data encrypted at rest by default (AES-256)
- **GCS**: Server-side encryption (SSE-GCS) enabled on all buckets
- **BigQuery**: Data encrypted at rest with Google-managed keys
- **Secret Manager**: All secrets encrypted with Cloud KMS

### In Transit
- All API traffic over HTTPS (TLS 1.2+)
- Internal service communication over Google's private network
- No plaintext secrets in logs or environment variables

### Application-Level
- Sensitive fields (emergency contacts, phone numbers) stored as plaintext in Firestore (encrypted at rest)
- JWT tokens signed with HMAC-SHA256
- OAuth2 client secrets stored in Secret Manager

---

## API Security

### Rate Limiting

Implemented via `RateLimiterMiddleware`:

| Client Type | Limit | Window |
|-------------|-------|--------|
| Anonymous | 60 req/min | Rolling |
| Authenticated | 120 req/min | Rolling |
| Admin | 300 req/min | Rolling |

Rate limit headers returned:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in window
- `X-RateLimit-Reset`: UTC timestamp when window resets

### Input Validation

All request bodies validated via Pydantic models:
- String length limits (min/max)
- Numeric range validation (ge/le)
- UUID format validation
- Enum value validation
- Required field enforcement

### CORS Configuration

```python
CORS_ORIGINS = [
    "http://localhost:5173",     # Local dev
    "https://stadiumos-ai.web.app",  # Production frontend
]
```

### Security Headers

- `X-Request-ID`: Unique request identifier
- `X-Process-Time`: Server processing time
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`

---

## Firestore Security Rules

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // Users can read/write their own data
    match /stadiumos_users/{userId} {
      allow read: if request.auth != null && request.auth.uid == userId;
      allow write: if request.auth != null && request.auth.uid == userId;
    }

    // Conversations: owner or assigned staff can access
    match /stadiumos_conversations/{convId} {
      allow read: if request.auth != null;
      allow create: if request.auth != null;
      allow update: if request.auth != null;
    }

    // Messages: part of a conversation
    match /stadiumos_messages/{msgId} {
      allow read: if request.auth != null;
      allow create: if request.auth != null;
    }

    // Alerts: staff and above can read/write
    match /stadiumos_alerts/{alertId} {
      allow read: if request.auth != null;
      allow create: if request.auth != null;
      allow update: if request.auth != null;
    }

    // Incidents: staff and above
    match /stadiumos_incidents/{incidentId} {
      allow read: if request.auth != null;
      allow create: if request.auth != null;
      allow update: if request.auth != null;
    }

    // Events: authenticated users can read, staff can write
    match /stadiumos_events/{eventId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null;
    }

    // Feedback: owner can read/write their own
    match /stadiumos_feedback/{feedbackId} {
      allow read: if request.auth != null;
      allow create: if request.auth != null;
    }
  }
}
```

---

## Secret Management

### Secret Storage

| Secret | Storage | Access |
|--------|---------|--------|
| JWT Secret Key | Environment / Secret Manager | Backend SA |
| OAuth2 Client Secret | Secret Manager | Backend SA |
| Google Maps API Key | Secret Manager | Backend SA |
| GCP Service Account Key | Cloud Run managed | Auto-mounted |

### Secret Rotation

- **JWT Secret**: Rotate quarterly; old tokens remain valid until expiry
- **OAuth2 Client Secret**: Rotate annually or on compromise
- **Service Account Keys**: Use Cloud Run managed service accounts (no key files in production)

### Best Practices

- Never commit secrets to source control
- Use `.env.example` with placeholder values
- Access secrets via `settings` object, not raw environment reads
- Use Secret Manager for production deployments
- Enable audit logging for Secret Manager access

---

## Incident Response Procedures

### Security Incident (AI-Flagged)

```
1. SecurityAgent detects anomaly
   │
   ├─→ Auto-creates Alert (TRIGGERED, priority=HIGH)
   │
   ├─→ Publishes to Pub/Sub topic "stadiumos-alerts"
   │
   └─→ Logs to BigQuery for audit trail
         │
         ▼
2. AlertService.escalate_alert()
   │
   ├─→ Increases escalation_level
   ├─→ Notifies security command center
   └─→ Triggers emergency broadcast if critical
         │
         ▼
3. Human operator acknowledges
   │
   ├─→ AlertService.acknowledge_alert()
   ├─→ Assigns responder
   └─→ Creates Incident if needed
         │
         ▼
4. Incident resolution
   │
   ├─→ IncidentService.resolve_incident()
   ├─→ Adds resolution notes
   └─→ Updates alert status to RESOLVED
```

### Data Breach Response

1. **Detect**: Monitor BigQuery anomalies, Firestore access patterns
2. **Contain**: Rotate affected credentials immediately
3. **Investigate**: Pull Cloud Logging audit trails
4. **Notify**: Contact GCP support, affected users, legal team
5. **Remediate**: Patch vulnerability, update security rules

### AI Safety Incidents

1. **Detect**: Content moderation flags, safety labels from Vision API
2. **Contain**: Soft-delete flagged messages (`is_visible=False`)
3. **Review**: Admin dashboard review of flagged content
4. **Action**: Update content moderation rules, retrain if needed

---

## Compliance Considerations

### GDPR
- User data export via Firestore API
- Right to deletion: `UserRepository.delete()` + Firestore cascade
- Data minimization: Collect only necessary fields
- Consent tracking: `user.metadata` field for consent flags

### CCPA
- Similar to GDPR requirements
- Do Not Sell: Flag in user metadata

### HIPAA (Medical Data)
- Medical incidents stored with `public_visibility=False`
- No PHI in logs (structured logger filters sensitive fields)
- Access controls restrict medical data to MEDICAL role

### FIFA/Event Requirements
- Multi-language support for all 20+ FIFA languages
- Real-time translation for live communications
- Accessibility compliance (WCAG 2.1 AA)
- Emergency broadcast capability for safety alerts
