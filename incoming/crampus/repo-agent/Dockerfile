# ---------------------------------------------------------------------
# BASE IMAGE — minimal tools shared across all variants
# ---------------------------------------------------------------------
FROM ubuntu:22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      wget \
      git \
      openssh-client \
      gnupg \
      sudo \
      software-properties-common \
      unzip && \
    rm -rf /var/lib/apt/lists/*

# Install GitHub CLI
RUN mkdir -p -m 755 /etc/apt/keyrings && \
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
      | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg >/dev/null && \
    chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
      | tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
    apt-get update && \
    apt-get install -y --no-install-recommends gh && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /workspace


# ---------------------------------------------------------------------
# NODE LAYER — Node.js + npm-based LLM tools
# Enabled with:   --build-arg INSTALL_NODE_TOOLS=1
# ---------------------------------------------------------------------
FROM base AS node-tools

ARG INSTALL_NODE_TOOLS=0

RUN if [ "$INSTALL_NODE_TOOLS" = "1" ]; then \
      echo "Installing Node.js 20.x..."; \
      curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
      apt-get update && \
      apt-get install -y nodejs && \
      npm install -g \
        @google/gemini-cli \
        @githubnext/github-copilot-cli \
        @anthropic-ai/claude-code \
        opencode-ai && \
      rm -rf /var/lib/apt/lists/*; \
    else \
      echo "Skipping Node.js & node tools layer"; \
    fi


# ---------------------------------------------------------------------
# OPENCODE LAYER — install official OpenCode CLI
# Enabled with:   --build-arg INSTALL_OPENCODE=1
# ---------------------------------------------------------------------
FROM base AS opencode

ARG INSTALL_OPENCODE=0

RUN if [ "$INSTALL_OPENCODE" = "1" ]; then \
      echo "Installing OpenCode..."; \
      curl -fsSL https://opencode.ai/install | bash && \
      cp /root/.opencode/bin/opencode /usr/local/bin/opencode && \
      chmod +x /usr/local/bin/opencode && \
      echo "OpenCode installed successfully"; \
    else \
      echo "Skipping OpenCode layer"; \
    fi


# ---------------------------------------------------------------------
# FINAL IMAGE BUILDER
# Compose layers depending on which tools are requested
# ---------------------------------------------------------------------
FROM base AS final

# Pass args to decide which artifacts to copy in
ARG INSTALL_NODE_TOOLS=0
ARG INSTALL_OPENCODE=0

# Conditionally install tools based on build args
# Copy from node-tools stage if enabled
RUN --mount=type=bind,from=node-tools,target=/node-tools \
    if [ "$INSTALL_NODE_TOOLS" = "1" ]; then \
      if [ -f /node-tools/usr/bin/node ]; then \
        cp /node-tools/usr/bin/node /usr/bin/node && \
        cp /node-tools/usr/bin/npm /usr/bin/npm && \
        cp -r /node-tools/usr/lib/node_modules /usr/lib/node_modules; \
      fi; \
    fi

ENV PATH="/usr/lib/node_modules/.bin:${PATH}"

# Copy from opencode stage if enabled
RUN --mount=type=bind,from=opencode,target=/opencode \
    if [ "$INSTALL_OPENCODE" = "1" ]; then \
      if [ -f /opencode/usr/local/bin/opencode ]; then \
        cp /opencode/usr/local/bin/opencode /usr/local/bin/opencode && \
        chmod +x /usr/local/bin/opencode; \
      fi; \
    fi

WORKDIR /workspace
