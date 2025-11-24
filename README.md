# Elder Advice Agent

## Description

Elder Advice Agent gives gentle, general guidance for older adults and caregivers.
It can respond to questions about aches, sleep, mood, safety, medication
organisation, and daily routines. It does **not** diagnose problems, prescribe
medicines, or handle emergencies.

## Endpoints

### Health check

- **GET** `/api/elder-advice-agent/health`

Response example:

```json
{
  "status": "ok",
  "agent_name": "elder-advice-agent",
  "ready": true
}
```
