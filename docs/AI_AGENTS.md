# StadiumOS AI - AI Agents Documentation

## Architecture Overview

```
User Query
    │
    ▼
AgentRouter.route_query()
    │
    ├─ Score categories via keyword matching
    ├─ Apply priority tie-breaking
    └─ Return best agent name
         │
         ▼
AgentRouter.process_query()
    │
    ├─ Get agent instance
    ├─ agent.process(query, context)
    │     │
    │     ├─ Classify intent/category (internal)
    │     ├─ Build enriched context
    │     ├─ Build prompt (system + context + query)
    │     ├─ Call Vertex AI Gemini
    │     ├─ Parse response (actions, sources)
    │     ├─ Compute confidence score
    │     └─ Return AgentResponse
    │
    └─ Return AgentResponse to ChatService
```

All agents inherit from `BaseAgent` and share:
- A system prompt defining their role and behavior
- Vertex AI Gemini model for text generation
- Retry logic with exponential backoff (3 attempts)
- Response parsing for actions and sources
- Confidence scoring

---

## Agent Capabilities

### FanAgent

**Purpose**: General fan experience and visitor services.

**Intents Handled**:
| Intent | Keywords | Auto-Action |
|--------|----------|-------------|
| `match_info` | schedule, game, score, team | `lookup_match_schedule` |
| `seating` | seat, section, gate, upgrade | `get_stadium_map` |
| `food` | food, drink, concession, menu | `get_concession_info` |
| `restroom` | bathroom, toilet, WC | - |
| `merchandise` | store, jersey, souvenir | `get_merchandise_info` |
| `events` | halftime, concert, activities | - |
| `amenities` | wifi, charging, lost and found | - |
| `policies` | rule, bag, re-entry | - |
| `general` | (fallback) | - |

**Example Interaction**:
```
User: "Where can I get a hot dog?"
FanAgent: Intent=food, Action=get_concession_info
Response: "The nearest food court is in Section A5, Gate 2 entrance.
           They have hot dogs, pretzels, and craft beer. Current wait: ~5 min."
```

---

### SecurityAgent

**Purpose**: Stadium safety and security operations.

**Categories Handled**:
| Category | Keywords | Severity |
|----------|----------|----------|
| `incident_report` | theft, assault, fight | varies |
| `threat_assessment` | suspicious, unattended | varies |
| `emergency_protocol` | emergency, code red | critical |
| `evacuation` | evacuate, fire alarm | critical |
| `access_control` | credential, badge, restricted | varies |
| `crowd_safety` | crush, stampede, surge | high |
| `lost_person` | lost, missing, child | medium |

**Severity Assessment**:
- **Critical**: active shooter, bomb, fire, explosion
- **High**: weapon, assault, injury, fighting
- **Medium**: suspicious, theft, trespassing
- **Low**: informational, routine check

**Auto-Actions**:
- Critical/High severity → `escalate_security`
- Incident reports → `log_incident`
- Evacuation → `activate_evacuation_protocol`

---

### MedicalAgent

**Purpose**: Health and medical support services.

**Categories**:
| Category | Keywords | Auto-Action |
|----------|----------|-------------|
| `first_aid` | bandage, wound, headache | `dispatch_first_aid` |
| `emergency_medical` | heart attack, stroke, seizure | `activate_emergency_medical` |
| `medical_station` | clinic, doctor, medical station | `get_nearest_medical_station` |
| `health_alert` | heat, dehydration, UV | - |
| `mental_health` | anxiety, panic, overwhelmed | - |
| `medication` | pills, insulin, epipen | - |

**Critical Rules**:
- NEVER provides diagnosis or prescriptions
- Always directs serious conditions to professional staff
- Immediately activates emergency protocols for life-threatening situations

---

### TransportAgent

**Purpose**: Transportation services and traffic management.

**Transport Modes**:
| Mode | Keywords | Auto-Action |
|------|----------|-------------|
| `parking` | park, garage, lot | `get_parking_status` |
| `transit` | bus, train, metro, subway | `get_transit_schedule` |
| `rideshare` | uber, lyft, taxi | `get_rideshare_zone` |
| `shuttle` | shuttle, park and ride | - |
| `traffic` | traffic, congestion, delay | - |
| `bicycle` | bike, scooter, cycling | - |

**Direction Detection**: Automatically detects arrival vs departure context.

---

### OperationsAgent

**Purpose**: Facility management and stadium operations.

**Responsibilities**:
- HVAC, lighting, plumbing, structural systems
- Crowd flow and capacity monitoring
- Staff scheduling and logistics
- Vendor and concession management
- Power and utility management
- Maintenance scheduling

---

### AccessibilityAgent

**Purpose**: Inclusive stadium experience for all visitors.

**Responsibilities**:
- Wheelchair and mobility device routing
- Hearing assistance services
- Visual aids and Braille guides
- Sensory room locations
- Companion seating
- Accessible parking arrangements

---

### VolunteerAgent

**Purpose**: Volunteer coordination and management.

**Responsibilities**:
- Task assignment based on skills
- Training guidance
- Shift scheduling
- Equipment coordination
- Onboarding new volunteers

---

### SustainabilityAgent

**Purpose**: Environmental responsibility.

**Responsibilities**:
- Recycling guidance
- Energy optimization
- Water conservation
- Carbon footprint tracking
- Green initiatives promotion

---

## System Prompts

Each agent has a detailed system prompt stored in `app/ai/prompts/system_prompts.py`. The prompt defines:

1. **Identity**: Who the agent is (role name)
2. **Core Responsibilities**: What the agent handles
3. **Response Guidelines**: How to respond (tone, format, escalation rules)
4. **Critical Rules**: Safety-critical constraints (especially for Security/Medical)
5. **Format Instructions**: Output structure (bullets, numbered lists, severity levels)

---

## Function Tools

Agents can trigger actions by including `[ACTION: action_name]` in their responses. The response parser extracts these and returns them in the `actions` field of `AgentResponse`.

Available actions:

| Action | Agent | Description |
|--------|-------|-------------|
| `lookup_match_schedule` | Fan | Fetch upcoming matches |
| `get_stadium_map` | Fan | Return stadium section map |
| `get_concession_info` | Fan | Food vendor details |
| `get_merchandise_info` | Fan | Store locations and stock |
| `escalate_security` | Security | Notify security command |
| `log_incident` | Security | Create incident record |
| `activate_evacuation_protocol` | Security | Trigger evacuation |
| `dispatch_first_aid` | Medical | Send first aid team |
| `activate_emergency_medical` | Medical | Call ambulance/EMT |
| `get_nearest_medical_station` | Medical | Find closest clinic |
| `get_parking_status` | Transport | Real-time parking data |
| `get_transit_schedule` | Transport | Bus/train schedules |
| `get_rideshare_zone` | Transport | Pickup/dropoff locations |

---

## RAG Configuration

The `RAGService` provides document retrieval for grounded responses:

- **Indexing**: Documents stored in Vertex AI Vector Search
- **Query**: Semantic search over indexed documents
- **Collections**: Separate collections per domain (stadium_info, safety_protocols, etc.)
- **Hybrid Search**: Combines keyword and semantic matching with configurable weights

---

## How to Add a New Agent

### 1. Create Agent Class

```python
# app/ai/agents/my_agent.py

from app.ai.agents.base_agent import BaseAgent, AgentResponse
from app.ai.prompts.system_prompts import MY_AGENT_PROMPT

class MyAgent(BaseAgent):
    @property
    def agent_name(self) -> str:
        return "MyAgent"

    @property
    def system_prompt(self) -> str:
        return MY_AGENT_PROMPT

    def process(self, query: str, context: dict) -> AgentResponse:
        category = self._classify_category(query.lower())

        enriched_context = {
            **context,
            "my_category": category,
            "service_type": "my_service",
        }

        prompt_parts = self._build_prompt(query, enriched_context)
        raw_response = self._call_gemini(prompt_parts)
        parsed = self._parse_response(raw_response)
        confidence = self._compute_confidence(parsed["clean_text"], query)

        return AgentResponse(
            response_text=parsed["clean_text"],
            agent_name=self.agent_name,
            confidence=confidence,
            metadata={"category": category, "raw_query": query},
            actions=parsed["actions"],
            sources=parsed["sources"],
        )

    def _classify_category(self, query_lower: str) -> str:
        # Implement keyword-based classification
        ...
```

### 2. Add System Prompt

```python
# app/ai/prompts/system_prompts.py

MY_AGENT_PROMPT = """You are StadiumOS MyAgent, specialized in ...
CORE RESPONSIBILITIES:
- ...
"""
```

### 3. Register in AgentRouter

```python
# app/ai/router/agent_router.py

from app.ai.agents.my_agent import MyAgent

AGENT_KEYWORDS["my_category"] = ["keyword1", "keyword2", ...]
CATEGORY_PRIORITY.insert(N, "my_category")  # Set priority

class AgentRouter:
    def __init__(self):
        self._agents["my_category"] = MyAgent()
```

### 4. Write Tests

```python
# backend/tests/ai/test_agents.py (add to parametrize list)
# backend/tests/unit/test_agent_router.py (add routing tests)
```
