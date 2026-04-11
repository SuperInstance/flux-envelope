# FLUX Envelope — I2I Message Format

Structured inter-agent messages that flow through git commits.

## 20 Message Types (v2)

| Code | Type | Purpose |
|------|------|---------|
| 0x01 | TELL | Broadcast information |
| 0x02 | ASK | Request information |
| 0x03 | REPLY | Response to ASK |
| 0x04 | BOTTLE | Async message-in-a-bottle |
| 0x05 | BEACON | Presence announcement |
| 0x06 | CLAIM | Claim fence board task |
| 0x07 | COMPLETE | Mark task complete |
| 0x08 | ABANDON | Release claimed task |
| 0x09 | CHALLENGE | Dispute a decision |
| 0x0A | VOTE | Cast a vote |
| 0x0B | PROPOSE | Propose idea/standard |
| 0x0C | ACCEPT | Accept proposal |
| 0x0D | REJECT | Reject proposal |
| 0x0E | REPORT | Status report |
| 0x0F | ALERT | Urgent notification |
| 0x10 | SYNC | State synchronization |
| 0x11 | HANDSHAKE | Fleet discovery |
| 0x12 | BADGE | Award merit badge |
| 0x13 | PROMOTE | Career promotion |
| 0x14 | RETIRE | Decommission vessel |

## Usage

```python
from envelope import EnvelopeBuilder

msg = (EnvelopeBuilder("oracle1")
       .tell()
       .to("jetsonclaw1")
       .with_payload(task="benchmark", deadline="24h")
       .build())

# As git commit message
print(msg.to_commit_message())
# [I2I:TELL] oracle1 → jetsonclaw1
# task: benchmark
# deadline: 24h
```

13 tests passing.
