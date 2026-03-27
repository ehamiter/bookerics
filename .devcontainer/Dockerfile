FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

USER root

# System dependencies:
#   - libpq-dev / postgresql-client: required by psycopg (PostgreSQL adapter)
#   - pango/cairo/harfbuzz/fontconfig/gdk-pixbuf: required by WeasyPrint (PDF generation)
#   - build-essential / libffi-dev: compiling native Python extensions
#   - aspell / aspell-en: required by pyspelling (dev dependency)
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


# Copy and set up firewall script
COPY init-firewall.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/init-firewall.sh && \
  echo "vscode ALL=(root) NOPASSWD: /usr/local/bin/init-firewall.sh" > /etc/sudoers.d/vscode-firewall && \
  chmod 0440 /etc/sudoers.d/vscode-firewall

USER vscode

# Install uv (Python package manager) and Python 3.13.7
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && /home/vscode/.local/bin/uv python install 3.13.7

# Install Claude Code
RUN curl -fsSL https://claude.ai/install.sh | bash

# Install GitHub Copilot
RUN curl -fsSL https://gh.io/copilot-install | bash
