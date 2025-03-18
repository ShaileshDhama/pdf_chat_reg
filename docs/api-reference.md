# LEGALe TROY API Reference

## API Endpoints

### Authentication
```
POST /api/v1/auth/web3-login
POST /api/v1/auth/refresh-token
```

### Document Management
```
POST   /api/v1/documents/upload
GET    /api/v1/documents/{id}
PUT    /api/v1/documents/{id}
DELETE /api/v1/documents/{id}
GET    /api/v1/documents/search
```

### AI Analysis
```
POST /api/v1/ai/analyze
POST /api/v1/ai/summarize
POST /api/v1/ai/compare
POST /api/v1/ai/translate
```

### Blockchain Operations
```
POST /api/v1/blockchain/sign
GET  /api/v1/blockchain/verify/{hash}
POST /api/v1/blockchain/store
GET  /api/v1/blockchain/retrieve/{cid}
```

### AR Features
```
GET  /api/v1/ar/model/{document_id}
POST /api/v1/ar/interact
GET  /api/v1/ar/voice-command
```

### Real-Time Collaboration
```
WS   /ws/document/{id}
POST /api/v1/collaboration/invite
GET  /api/v1/collaboration/sessions
```

## WebSocket Events

### Document Collaboration
- `document.update`: Real-time document updates
- `cursor.move`: Cursor position updates
- `comment.add`: New comment added
- `ar.interact`: AR interaction events

## Data Models

### Document
```typescript
interface Document {
  id: string;
  title: string;
  content: string;
  hash: string;
  ipfsCid: string;
  createdAt: string;
  updatedAt: string;
  signatures: Signature[];
}
```

### AI Analysis
```typescript
interface Analysis {
  summary: string;
  keyPoints: string[];
  riskFactors: string[];
  suggestions: string[];
}
```

### Blockchain Transaction
```typescript
interface Transaction {
  hash: string;
  signature: string;
  timestamp: string;
  status: 'pending' | 'confirmed';
}
```

## Error Codes
- 1001: Invalid Web3 signature
- 1002: Document not found
- 1003: Unauthorized access
- 1004: Invalid IPFS operation
- 1005: AI processing error

## Rate Limits
- Authentication: 5 requests/minute
- Document Upload: 10 requests/minute
- AI Analysis: 20 requests/minute
- Blockchain Operations: 30 requests/minute

## Security
All API endpoints require authentication via:
1. JWT token, or
2. Web3 wallet signature
