FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    iptables \
    ipset \
    iproute2 \
    dnsutils \
    aggregate \
    jq \
    libpq-dev \
    postgresql-client \
    build-essential \
    libffi-dev \
    fd-find \
    ripgrep \
    trash-cli \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s $(which fdfind) /usr/local/bin/fd

RUN git config --system --add safe.directory /workspace

COPY init-firewall.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/init-firewall.sh && \
  echo "vscode ALL=(root) NOPASSWD: /usr/local/bin/init-firewall.sh" > /etc/sudoers.d/vscode-firewall && \
  chmod 0440 /etc/sudoers.d/vscode-firewall

USER vscode

RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && /home/vscode/.local/bin/uv python install 3.13.7

RUN curl -fsSL https://claude.ai/install.sh | bash

RUN curl -fsSL https://gh.io/copilot-install | bash
