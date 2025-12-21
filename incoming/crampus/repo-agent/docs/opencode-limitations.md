# OpenCode Limitations with OpenRouter

## Problem

OpenCode does not support custom API endpoints like OpenRouter. It has its own provider system with built-in integrations for specific providers.

## Investigation Results

### OpenCode CLI
```bash
opencode run --help
```

Available options:
- `--model`: Format is `provider/model` but only works with built-in providers
- `--attach`: Attach to running OpenCode server
- No `--base-url` or `--api-base` option
- No environment variables for API configuration

### Test Results
```bash
# This fails with "ProviderModelNotFoundError"
opencode run --model "anthropic/claude-3.5-haiku" "say hello"

# OpenCode doesn't recognize "anthropic" as a provider in this format
# It expects its own provider configuration
```

## Solutions

### Option 1: Use Direct Provider API (Recommended for OpenCode)

If you want to use OpenCode, configure it with a direct provider API key:

```yaml
# For Anthropic Claude directly (not via OpenRouter)
model: "claude-3-5-haiku-20241022"
api_key_env: "ANTHROPIC_API_KEY"

tool:
  name: "opencode"
  entrypoint: "opencode run"
  args: {}
```

### Option 2: Use a Different Tool

Use a tool that supports custom API endpoints:

#### aider (Recommended)
`aider` supports OpenRouter via `--api-base`:

```yaml
model: "anthropic/claude-3.5-haiku"
api_key_env: "OPENROUTER_API_KEY"

tool:
  name: "aider"
  entrypoint: "aider"
  args:
    api-base: "https://openrouter.ai/api/v1"
    yes: true  # Auto-confirm changes
```

**Note**: `aider` is not currently installed in the Docker image. Need to add it to Dockerfile:

```dockerfile
RUN pip install aider-chat
```

#### Other Options
- **gpt-engineer**: Supports custom endpoints
- **mentat**: OpenAI-compatible APIs
- **Custom script**: Write a simple wrapper that calls OpenRouter API directly

### Option 3: Use Echo for Testing

For testing the workflow without LLM integration:

```yaml
tool:
  name: "echo"
  entrypoint: "echo"
  args: {}
```

This validates:
- GitHub authentication
- Repository operations (clone, branch, commit, push)
- File handling
- Docker environment

## Recommendation

1. **For Testing**: Use `echo` tool (current configuration)
2. **For Production with OpenRouter**: Add `aider` to Dockerfile
3. **For Production without OpenRouter**: Use OpenCode with direct Anthropic API key

## Implementation Steps (Adding aider)

1. Update `Dockerfile`:
```dockerfile
# After OpenCode installation
RUN pip install aider-chat
```

2. Rebuild Docker image:
```bash
docker build --build-arg INSTALL_OPENCODE=1 --build-arg INSTALL_NODE_TOOLS=1 -t repo-agent:latest .
```

3. Update instruction file:
```yaml
tool:
  name: "aider"
  entrypoint: "aider"
  args:
    api-base: "https://openrouter.ai/api/v1"
    yes: true
    model: "anthropic/claude-3.5-haiku"
```

4. Update `core.py` to handle aider's command format:
```python
elif [[ "${TOOL_NAME}" == "aider" ]]; then
  ${TOOL_ENTRYPOINT} --model "${MODEL}" --message "${FULL_PROMPT}" ${TOOL_EXTRA_ARGS}
```
