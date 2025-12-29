# Playground Chatbot

An experimental DevOps assistant exploring generic tool usage patterns for AI agents.

> **Built with [MACSDK](https://github.com/juanje/macsdk)** - A Multi-Agent Chatbot SDK that provides the foundation for agent orchestration, tool management, and chat interfaces.

## Project Purpose

This project explores how AI agents can use **generic, reusable tools** instead of hardcoded, task-specific functions. The goal is to demonstrate patterns where agents:

1. **Learn dynamically** - Discover available capabilities through tool exploration
2. **Use generic interfaces** - Work with flexible tools that adapt to different scenarios
3. **Follow progressive disclosure** - Access general guidance first, then dive into specifics
4. **Calculate reliably** - Delegate math to tools instead of relying on LLM arithmetic

## Tool Architecture

### Skills System (Progressive Disclosure)

Skills are markdown files that teach the agent how to perform tasks:

- **General skills** (`skills/check-service-health.md`) - Overview and common patterns
- **Specific skills** (`skills/check-service-health/api-gateway.md`) - Deep-dive troubleshooting
- **Dynamic discovery** - Agent uses `list_skills()` and `read_skill()` to learn

Example workflow:
```
User: "Why is API Gateway slow?"
→ list_skills() → Finds general and specific skills
→ read_skill("check-service-health.md") → Gets overview
→ read_skill("check-service-health/api-gateway.md") → Gets detailed steps
→ Follows instructions to investigate
```

### Facts System (Contextual Knowledge)

Facts provide domain-specific information the agent needs:

- **Service catalog** - Details about each service (IDs, owners, SLAs, dependencies)
- **Deployment policies** - Environment configurations, approval workflows
- **Incident protocols** - Response procedures, escalation paths, on-call schedules

Facts prevent hallucination by providing verifiable, up-to-date information.

### Calculate Tool (Safe Math)

A secure calculation tool using `simpleeval`:

- **Sandboxed execution** - Only mathematical operations, no file/network access
- **Reliable results** - LLMs delegate all arithmetic to this tool
- **Rich math support** - Basic operators, functions (sqrt, sin, log), constants (pi, e)

Example:
```python
calculate("(5 / 6) * 100")  # → "83.33333333333334"
calculate("sin(pi/2)")       # → "1.0"
```

### Generic API Tools

Provided by [MACSDK](https://github.com/juanje/macsdk):

- **api_get** - Generic REST API calls to registered services
  - Supports service registration, authentication, retries
  - Works with any REST API, not endpoint-specific
- **fetch_file** - Download and optionally filter remote files
  - Supports logs, configs, or any text content
  - Optional line filtering with regex patterns

These tools demonstrate the power of **generic interfaces** - they work with any API or file, making agents more flexible and maintainable than hardcoded, endpoint-specific functions.

## Example Agent: DevOps Toolbox

The included `toolbox` agent demonstrates these concepts:

**Available Tools:**
- `api_get` - Query DevOps monitoring API
- `fetch_file` - Download log files
- `calculate` - Perform calculations safely
- `list_skills` / `read_skill` - Discover and learn task instructions
- `list_facts` / `read_fact` - Access contextual information

**Example Interactions:**

```
User: "Are there any critical alerts?"
Agent: Uses skills to learn how → Calls API → Reports findings

User: "What percentage of services meet SLA?"
Agent: Gets service data → Counts → calculate("(5/6)*100") → Reports 83.33%

User: "Why is auth-service having issues?"
Agent: Reads general skill → Reads specific skill → Checks dependencies → Investigates
```

## Technical Foundation

This project is built on **[MACSDK](https://github.com/juanje/macsdk)** (Multi-Agent Chatbot SDK), which provides:

- **Supervisor orchestration** - Intelligent routing between specialist agents
- **Tool framework** - Generic tools like `api_get` and `fetch_file`
- **Chat interfaces** - Both CLI and Web UI with streaming support
- **Agent management** - Easy registration and composition of multiple agents
- **Context handling** - Automatic message compression and history management

MACSDK handles the infrastructure so this project can focus on exploring **generic tool patterns** and **externalized knowledge systems** (skills/facts).

## Installation

```bash
uv sync
```

This will install all dependencies, including MACSDK (referenced as an editable local dependency in `pyproject.toml`).

## Configuration

Before running the chatbot, you need to configure your Google API key.

### Option 1: Environment file (recommended)

Copy the example file and add your API key:

```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

### Option 2: YAML configuration

Copy the example config and customize:

```bash
cp config.yml.example config.yml
# Edit config.yml to customize LLM models, temperatures, etc.
```

Note: API keys should always be in `.env`, not in `config.yml`.

### Option 3: Environment variable

Export the variable directly:

```bash
export GOOGLE_API_KEY=your_key_here
```

You can get an API key from: https://aistudio.google.com/apikey

### Configuration Options in config.yml

```yaml
# LLM Configuration
llm_model: gemini-2.5-flash      # Model for responses
llm_temperature: 0.3             # Creativity (0.0 - 1.0)
llm_reasoning_effort: medium     # low, medium, high

# Classifier (for query routing)
classifier_model: gemini-2.5-flash
classifier_temperature: 0.0

# Server settings (for web interface)
server_host: 0.0.0.0
server_port: 8000
```

## Usage

### Show Commands

```bash
uv run playground-chatbot
```

### Interactive Chat (CLI)

```bash
uv run playground-chatbot chat
```

### Web Interface

```bash
uv run playground-chatbot web
# Open http://localhost:8000
```

### List Agents

```bash
uv run playground-chatbot agents
```

### Show Configuration

```bash
uv run playground-chatbot info
```

## Skills and Facts

### Directory Structure

```
skills/                              # Task instructions
├── check-service-health.md          # General: service health overview
├── check-service-health/            # Specific: per-service details
│   ├── api-gateway.md
│   ├── auth-service.md
│   └── postgres-primary.md
├── investigate-pipeline-failures.md
└── monitor-critical-alerts.md

facts/                               # Contextual knowledge
├── devops-services-catalog.md       # Service details and dependencies
├── deployment-environments.md       # Deployment policies
└── company-incident-response-protocol.md  # Incident procedures
```

### Creating Skills

Skills use YAML frontmatter:

```markdown
---
name: my-skill-name
description: What this skill teaches the agent to do
---

# My Skill Name

[Instructions the agent will follow...]

## When to Use
- Situation 1
- Situation 2

## Steps
1. First step
2. Second step
```

### Creating Facts

Facts provide verifiable information:

```markdown
---
name: my-fact-name
description: What information this fact contains
---

# My Fact

[Detailed, accurate information the agent needs...]

## Key Details
- Detail 1
- Detail 2
```

### Configuration

Customize skill/fact directories in `config.yml`:

```yaml
# Default: skills/ and facts/ in project root
skills_dir: skills
facts_dir: facts
```

## Customization

### Adding Agents

Use the MACSDK CLI to add agents:

```bash
macsdk add-agent . --package my-agent
```

Or manually edit `src/playground_chatbot/agents.py`.

### Customizing Behavior

Edit `src/playground_chatbot/prompts.py` to customize:
- Chatbot name and description
- Additional context for the supervisor
- Response guidelines

### Custom Configuration

Edit `src/playground_chatbot/config.py` to add your own settings.

## Key Concepts Demonstrated

### 1. Generic Tools Over Specific Functions

Instead of:
```python
def check_api_gateway_health():
    # Hardcoded logic
```

Use:
```python
api_get(service="devops", endpoint="/services/2")
```

### 2. Progressive Disclosure

Agents learn hierarchically:
- General skill → Understand the domain
- Specific skill → Deep-dive into details
- Facts → Get accurate context

### 3. Externalized Knowledge

Agent behavior comes from files (skills/facts), not code:
- Update a skill → Agent learns new approach
- Add a fact → Agent has new information
- No code changes needed

### 4. Reliable Computation

LLMs are poor at math, so delegate:
```python
# Bad: Agent calculates mentally → "approximately 83%"
# Good: Agent uses tool → calculate("(5/6)*100") → "83.33333333333334"
```

## 🤖 AI Tools Disclaimer

This project was developed with the assistance of artificial intelligence tools:

**Tools used:**
- **Cursor**: Code editor with AI capabilities
- **Claude-4-Sonnet**: Anthropic's language model

**Division of responsibilities:**

**AI (Cursor + Claude-4-Sonnet)**:
- 🔧 Initial code prototyping
- 📝 Generation of examples and test cases
- 🐛 Assistance in debugging and error resolution
- 📚 Documentation and comments writing
- 💡 Technical implementation suggestions

**Human (Juanje Ojeda)**:
- 🎯 Specification of objectives and requirements
- 🔍 Critical review of code and documentation
- 💬 Iterative feedback and solution refinement
- 📋 Definition of project's educational structure
- ✅ Final validation of concepts and approaches

**Collaboration philosophy**: AI tools served as a highly capable technical assistant, while all design decisions, educational objectives, and project directions were defined and validated by the human.

## Author

**Juanje Ojeda**  
Email: juanje@redhat.com  
GitHub: https://github.com/juanje/
