"""
FLUX Envelope — Structured I2I message format.

Every inter-agent message follows this envelope:
  [HEADER][TYPE][FROM][TO][TIMESTAMP][PAYLOAD_LEN][PAYLOAD][SIGNATURE]

The envelope IS the protocol. No separate message broker needed.
Messages are encoded as FLUX bytecodes and stored as git commits.
"""
import json
import struct
import hashlib
import time
from datetime import datetime, timezone
from enum import IntEnum
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any


class MsgType(IntEnum):
    # Core I2I types (v2 spec)
    TELL = 0x01       # Broadcast information
    ASK = 0x02        # Request information
    REPLY = 0x03      # Response to ASK
    BOTTLE = 0x04     # Async message-in-a-bottle
    BEACON = 0x05     # Presence announcement
    CLAIM = 0x06      # Claim a fence board task
    COMPLETE = 0x07   # Mark fence board complete
    ABANDON = 0x08    # Release a claimed fence
    CHALLENGE = 0x09  # Dispute a decision
    VOTE = 0x0A       # Cast a vote
    PROPOSE = 0x0B    # Propose a new idea/standard
    ACCEPT = 0x0C     # Accept a proposal
    REJECT = 0x0D     # Reject a proposal
    REPORT = 0x0E     # Status report
    ALERT = 0x0F      # Urgent notification
    SYNC = 0x10       # Request state synchronization
    HANDSHAKE = 0x11  # Fleet discovery handshake
    BADGE = 0x12      # Award merit badge
    PROMOTE = 0x13    # Career stage promotion
    RETIRE = 0x14     # Decommission a vessel

    # Extended types
    VOCAB_SHARE = 0x20   # Share vocabulary collection
    VOCAB_PRUNE = 0x21   # Prune vocabulary (tombstone)
    BENCHMARK = 0x22     # Share benchmark results
    SENSOR = 0x23        # Sensor data from hardware
    ERROR = 0x30         # Error report
    HEARTBEAT = 0xFF     # Keep-alive


class MsgPriority(IntEnum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class FluxEnvelope:
    """Structured I2I message envelope."""
    msg_type: MsgType
    sender: str           # vessel name (e.g., "oracle1")
    recipient: str        # vessel name or "fleet" for broadcast
    payload: Dict[str, Any]
    priority: MsgPriority = MsgPriority.NORMAL
    msg_id: str = ""
    in_reply_to: str = ""  # ID of message this replies to
    timestamp: str = ""
    signature: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if not self.msg_id:
            self.msg_id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate unique message ID from content hash."""
        content = f"{self.sender}:{self.recipient}:{self.msg_type}:{self.timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d["msg_type"] = int(self.msg_type)
        d["priority"] = int(self.priority)
        return d
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, d: dict) -> 'FluxEnvelope':
        d["msg_type"] = MsgType(d["msg_type"])
        d["priority"] = MsgPriority(d.get("priority", 1))
        return cls(**d)
    
    @classmethod
    def from_json(cls, j: str) -> 'FluxEnvelope':
        return cls.from_dict(json.loads(j))
    
    def to_commit_message(self) -> str:
        """Format as git commit message."""
        type_name = MsgType(self.msg_type).name
        subject = f"[I2I:{type_name}] {self.sender} → {self.recipient}"
        
        # Build body from payload
        body_lines = []
        for k, v in self.payload.items():
            body_lines.append(f"{k}: {v}")
        
        if self.in_reply_to:
            body_lines.append(f"in-reply-to: {self.in_reply_to}")
        
        body = "\n".join(body_lines)
        return f"{subject}\n\n{body}" if body else subject
    
    @classmethod
    def from_commit_message(cls, msg: str, author: str = "unknown") -> Optional['FluxEnvelope']:
        """Parse a git commit message into an envelope."""
        if not msg.startswith("[I2I:"):
            return None
        
        # Extract [I2I:TYPE] sender → recipient
        try:
            bracket_end = msg.index("]")
            type_str = msg[5:bracket_end]
            rest = msg[bracket_end+1:].strip()
            
            arrow_parts = rest.split("→")
            sender = arrow_parts[0].strip() if arrow_parts else author
            recipient = arrow_parts[1].strip().split("\n")[0].strip() if len(arrow_parts) > 1 else "fleet"
            
            msg_type = MsgType[type_str]
        except (ValueError, KeyError):
            return None
        
        # Parse body for payload
        payload = {}
        lines = msg.split("\n\n", 1)
        if len(lines) > 1:
            for line in lines[1].split("\n"):
                if ": " in line:
                    k, v = line.split(": ", 1)
                    if k == "in-reply-to":
                        pass  # handled separately
                    else:
                        payload[k] = v
        
        return cls(
            msg_type=msg_type,
            sender=sender,
            recipient=recipient,
            payload=payload,
        )


class EnvelopeBuilder:
    """Fluent builder for I2I messages."""
    
    def __init__(self, sender: str):
        self.sender = sender
        self._type = None
        self._recipient = "fleet"
        self._payload = {}
        self._priority = MsgPriority.NORMAL
        self._reply_to = ""
    
    def tell(self) -> 'EnvelopeBuilder':
        self._type = MsgType.TELL
        return self
    
    def ask(self) -> 'EnvelopeBuilder':
        self._type = MsgType.ASK
        return self
    
    def reply_to(self, msg_id: str) -> 'EnvelopeBuilder':
        self._reply_to = msg_id
        self._type = MsgType.REPLY
        return self
    
    def to(self, recipient: str) -> 'EnvelopeBuilder':
        self._recipient = recipient
        return self
    
    def broadcast(self) -> 'EnvelopeBuilder':
        self._recipient = "fleet"
        return self
    
    def urgent(self) -> 'EnvelopeBuilder':
        self._priority = MsgPriority.URGENT
        return self
    
    def with_payload(self, **kwargs) -> 'EnvelopeBuilder':
        self._payload.update(kwargs)
        return self
    
    def build(self) -> FluxEnvelope:
        if not self._type:
            raise ValueError("Message type not set")
        return FluxEnvelope(
            msg_type=self._type,
            sender=self.sender,
            recipient=self._recipient,
            payload=self._payload,
            priority=self._priority,
            in_reply_to=self._reply_to,
        )


# ── Tests ──────────────────────────────────────────────

import unittest


class TestFluxEnvelope(unittest.TestCase):
    def test_create_tell(self):
        env = FluxEnvelope(msg_type=MsgType.TELL, sender="oracle1", recipient="jetsonclaw1", payload={"info": "test"})
        self.assertEqual(env.msg_type, MsgType.TELL)
        self.assertTrue(env.msg_id)
    
    def test_create_ask(self):
        env = FluxEnvelope(msg_type=MsgType.ASK, sender="oracle1", recipient="fleet", payload={"question": "status?"})
        self.assertEqual(env.msg_type, MsgType.ASK)
    
    def test_to_json_roundtrip(self):
        env = FluxEnvelope(msg_type=MsgType.TELL, sender="oracle1", recipient="fleet", payload={"key": "val"})
        j = env.to_json()
        restored = FluxEnvelope.from_json(j)
        self.assertEqual(restored.sender, "oracle1")
        self.assertEqual(restored.msg_type, MsgType.TELL)
    
    def test_to_dict(self):
        env = FluxEnvelope(msg_type=MsgType.BOTTLE, sender="oracle1", recipient="jetsonclaw1", payload={})
        d = env.to_dict()
        self.assertEqual(d["msg_type"], 0x04)
    
    def test_commit_message_tell(self):
        env = FluxEnvelope(msg_type=MsgType.TELL, sender="oracle1", recipient="jetsonclaw1", payload={"status": "active"})
        msg = env.to_commit_message()
        self.assertIn("[I2I:TELL]", msg)
        self.assertIn("oracle1", msg)
        self.assertIn("jetsonclaw1", msg)
    
    def test_from_commit_message(self):
        msg = "[I2I:TELL] oracle1 → jetsonclaw1\n\nstatus: active"
        env = FluxEnvelope.from_commit_message(msg)
        self.assertIsNotNone(env)
        self.assertEqual(env.msg_type, MsgType.TELL)
        self.assertEqual(env.sender, "oracle1")
        self.assertEqual(env.recipient, "jetsonclaw1")
    
    def test_from_commit_message_invalid(self):
        env = FluxEnvelope.from_commit_message("regular commit message")
        self.assertIsNone(env)
    
    def test_builder_tell(self):
        env = (EnvelopeBuilder("oracle1")
               .tell()
               .to("jetsonclaw1")
               .with_payload(task="benchmark")
               .build())
        self.assertEqual(env.msg_type, MsgType.TELL)
        self.assertEqual(env.recipient, "jetsonclaw1")
        self.assertEqual(env.payload["task"], "benchmark")
    
    def test_builder_ask(self):
        env = (EnvelopeBuilder("oracle1")
               .ask()
               .broadcast()
               .with_payload(question="who has CUDA?")
               .build())
        self.assertEqual(env.msg_type, MsgType.ASK)
        self.assertEqual(env.recipient, "fleet")
    
    def test_builder_urgent(self):
        env = (EnvelopeBuilder("oracle1")
               .tell()
               .urgent()
               .with_payload(alert="system overload")
               .build())
        self.assertEqual(env.priority, MsgPriority.URGENT)
    
    def test_builder_reply(self):
        env = (EnvelopeBuilder("jetsonclaw1")
               .reply_to("abc123")
               .to("oracle1")
               .with_payload(answer="CUDA available")
               .build())
        self.assertEqual(env.msg_type, MsgType.REPLY)
        self.assertEqual(env.in_reply_to, "abc123")
    
    def test_all_msg_types(self):
        """All 20 v2 message types are defined."""
        expected = [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
                    0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10,
                    0x11, 0x12, 0x13, 0x14]
        for code in expected:
            self.assertIsNotNone(MsgType(code))
    
    def test_unique_msg_id(self):
        env1 = FluxEnvelope(msg_type=MsgType.TELL, sender="o1", recipient="fleet", payload={"a": 1})
        time.sleep(0.001)
        env2 = FluxEnvelope(msg_type=MsgType.TELL, sender="o1", recipient="fleet", payload={"a": 1})
        self.assertNotEqual(env1.msg_id, env2.msg_id)


if __name__ == "__main__":
    unittest.main(verbosity=2)
