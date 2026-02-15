# Configuration System

Workshop-Reporter uses a YAML-based configuration system to manage LLM endpoints and credentials securely.

## Quick Start

1. **Copy secrets template:**
   ```bash
   cp secrets.yaml.template secrets.yaml
   ```

2. **Add your API keys to `secrets.yaml`:**
   ```yaml
   OPENAI_API_KEY: "sk-your-actual-key-here"
   ```

3. **Choose endpoint in `configuration.yaml`:**
   ```yaml
   active_endpoint: "nim_spark"  # or "openai"
   ```

4. **Use in your code:**
   ```python
   from llm_client import create_llm_client
   
   client = create_llm_client()
   response = client.chat_completion(messages)
   ```

## Files

### `configuration.yaml`
Main configuration file containing:
- Endpoint definitions (OpenAI, NIM, etc.)
- Model parameters (temperature, max_tokens)
- Application settings

**Safe to commit to git** ✅

### `secrets.yaml`
Credentials file containing:
- API keys
- Passwords
- Tokens

**NEVER commit to git** ❌ (already in .gitignore)

### `secrets.yaml.template`
Template for secrets file. Copy this to `secrets.yaml` and fill in your credentials.

**Safe to commit to git** ✅

## Pre-configured Endpoints

### OpenAI
```yaml
active_endpoint: "openai"
```

- Uses OpenAI API (gpt-4o-mini by default)
- Requires `OPENAI_API_KEY` in secrets.yaml
- Cost: ~$0.15-0.60 per 1M tokens

### NIM on spark-ts (via SSH)
```yaml
active_endpoint: "nim_spark"
```

- Uses NVIDIA NIM on spark-ts via SSH wrapper
- No API key required
- Free (uses your hardware)
- Requires SSH access to spark-ts

### NIM on spark-ts (via Tunnel)
```yaml
active_endpoint: "nim_spark_tunnel"
```

- Uses NVIDIA NIM on spark-ts via SSH tunnel
- Requires manual tunnel setup: `ssh -f -N -L 8000:localhost:8000 spark-ts`
- No API key required
- Slightly faster than SSH wrapper

## Usage Examples

### Basic Usage
```python
from llm_client import create_llm_client

# Uses active_endpoint from configuration.yaml
client = create_llm_client()

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
]

response = client.chat_completion(messages)
print(response)
```

### Switch Endpoints
```python
from llm_client import create_llm_client

# Override active_endpoint
client_openai = create_llm_client(endpoint="openai")
client_nim = create_llm_client(endpoint="nim_spark")
```

### Override Parameters
```python
response = client.chat_completion(
    messages,
    temperature=0.7,      # Override default
    max_tokens=1000,      # Override default
    top_p=0.95            # Override default
)
```

### Access Config Directly
```python
from config_loader import load_config

config = load_config()
print(f"Active: {config.active_endpoint_name}")
print(f"Available: {config.list_endpoints()}")

# Get app settings
data_dir = config.get_app_setting("data_dir")
```

## Adding New Endpoints

### 1. Add to `configuration.yaml`

```yaml
endpoints:
  my_endpoint:
    type: "openai"  # or "nim_ssh"
    base_url: "https://api.example.com/v1"
    model: "my-model-name"
    api_key_env: "MY_API_KEY"
    parameters:
      temperature: 0.3
      max_tokens: 4000
```

### 2. Add credentials to `secrets.yaml`

```yaml
MY_API_KEY: "your-key-here"
```

### 3. Activate it

```yaml
active_endpoint: "my_endpoint"
```

## Supported Endpoint Types

### `type: "openai"`
OpenAI-compatible API endpoints (OpenAI, Azure OpenAI, vLLM, etc.)

**Required fields:**
- `base_url`: API base URL
- `model`: Model name
- `api_key_env`: Environment variable for API key (can be null)

**Example:**
```yaml
my_endpoint:
  type: "openai"
  base_url: "https://api.openai.com/v1"
  model: "gpt-4o-mini"
  api_key_env: "OPENAI_API_KEY"
```

### `type: "nim_ssh"`
NVIDIA NIM accessed via SSH wrapper (no tunnel needed)

**Required fields:**
- `ssh_host`: SSH hostname
- `base_url`: NIM endpoint URL (on remote host)
- `model`: Model name

**Example:**
```yaml
my_nim:
  type: "nim_ssh"
  ssh_host: "spark-ts"
  base_url: "http://localhost:8000/v1"
  model: "meta/llama-3.1-8b-instruct"
  api_key_env: null
```

## Security Best Practices

1. **Never commit `secrets.yaml`** - It's in .gitignore
2. **Use environment variables** - Alternative to secrets.yaml:
   ```bash
   export OPENAI_API_KEY="sk-..."
   python your_script.py
   ```
3. **Rotate API keys regularly**
4. **Use SSH keys for spark-ts** - Avoid password authentication
5. **Limit API key permissions** - Use read-only or restricted keys when possible

## Testing

Run the example script:
```bash
python example_usage.py
```

Or test specific examples:
```bash
python example_usage.py 1  # Basic usage
python example_usage.py 2  # Endpoint switching
python example_usage.py 3  # Parameter override
python example_usage.py 4  # Workshop report style
```

## Troubleshooting

### "API key not found"
- Check `secrets.yaml` exists and contains the required key
- Or set environment variable: `export OPENAI_API_KEY="sk-..."`

### "Endpoint not found"
- Check `active_endpoint` matches an endpoint name in `endpoints:` section
- Check spelling and indentation in YAML

### "SSH command failed" (NIM)
- Verify SSH access: `ssh spark-ts echo test`
- Check NIM is running: `ssh spark-ts "curl http://localhost:8000/v1/models"`

### "Module not found"
- Install dependencies: `pip install openai pyyaml`

## Dependencies

```bash
pip install openai pyyaml
```

## Integration with TPC-Session-Reporter

To use this configuration system in your TPC-Session-Reporter:

```python
# In generate_report.py
from llm_client import create_llm_client

# Replace OpenAI client initialization with:
llm_client = create_llm_client()

# Replace API call with:
response = llm_client.chat_completion(
    messages=[
        {"role": "system", "content": "You are a technical report writer."},
        {"role": "user", "content": master_prompt}
    ],
    temperature=0.3,
    max_tokens=4000
)

# response is already a string, use directly
print(response)
```

## See Also

- `SPARK_NIM_SETUP.md` - Details on NVIDIA NIM configuration
- `example_usage.py` - Working examples
- `configuration.yaml` - Main config file
- `secrets.yaml.template` - Secrets template
