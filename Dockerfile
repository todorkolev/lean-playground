# Lean Playground - QuantConnect Lean algorithmic trading research environment
FROM quantconnect/lean:foundation

# Container metadata
LABEL org.opencontainers.image.source=https://github.com/${GITHUB_REPOSITORY}
LABEL org.opencontainers.image.description="Lean Playground Docker Image"
LABEL org.opencontainers.image.licenses=MIT

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:$PATH"

# Working directory
WORKDIR /workspaces/lean-playground

USER root

# System dependencies
RUN apt-get update && \
    apt-get install -y \
    sudo zsh git nano less wget curl htop mc vim \
    build-essential \
    ninja-build gettext cmake unzip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# UV package manager
RUN pip install uv
ENV UV_SYSTEM_PYTHON=1 \
    UV_PROJECT_ENVIRONMENT="/usr/local"

# Python development tools
RUN uv pip install pytest black isort pylint debugpy

# JupyterLab
RUN uv pip install --system jupyterlab

# Lean CLI and additional ML packages not in foundation
RUN pip install lean river einops

# Copy pyproject.toml, README.md and install dependencies
COPY pyproject.toml README.md ./
RUN uv pip install --system -e ".[dev,jupyter]"

# Various packages install a `tests` directory which causes pytest to use it instead of our local one
RUN python -c "import site; import os; [os.system(f'rm -rf {path}/tests') for path in site.getsitepackages()]"

# Install oh-my-zsh with headline theme
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
RUN wget https://raw.githubusercontent.com/moarram/headline/main/headline.zsh-theme && \
    sed -i "s/'echo \$USER'/'whoami'/g" headline.zsh-theme && \
    sed -i "s/'basename \"\$VIRTUAL_ENV\"'/'basename \"\$CONDA_DEFAULT_ENV\"'/g" headline.zsh-theme && \
    mv headline.zsh-theme /root/.oh-my-zsh/themes/headline.zsh-theme && \
    echo 'source /root/.oh-my-zsh/themes/headline.zsh-theme' >> /root/.zshrc

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# AI development tools
RUN curl -fsSL https://claude.ai/install.sh | bash
RUN npm install -g @augmentcode/auggie
RUN uv tool install --force --python python3.12 aider-chat@latest

RUN npm install -g @buildforce/cli
RUN buildforce init .

# GitHub CLI
RUN (type -p wget >/dev/null || (sudo apt update && sudo apt-get install wget -y)) \
    && sudo mkdir -p -m 755 /etc/apt/keyrings \
    && out=$(mktemp) && wget -nv -O$out https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    && cat $out | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
    && sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && sudo apt update \
    && sudo apt install gh -y

# Act for local GitHub Actions testing
RUN curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | bash && \
    mv ./bin/act /usr/local/bin/ && \
    rm -rf bin && \
    echo "--container-architecture linux/arm64" > /root/.actrc && \
    echo "-P ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest" >> /root/.actrc

# Copy scripts
COPY scripts /workspaces/lean-playground/scripts/
RUN chmod +x /workspaces/lean-playground/scripts/*.sh 2>/dev/null || true

# Tini for proper signal handling
RUN if [ "$(uname -m)" = "aarch64" ]; then \
    tini_binary="tini-arm64"; \
    tini_sha256="07952557df20bfd2a95f9bef198b445e006171969499a1d361bd9e6f8e5e0e81"; \
    else \
    tini_binary="tini-amd64"; \
    tini_sha256="93dcc18adc78c65a028a84799ecf8ad40c936fdfc5f2a57b1acda5a8117fa82c"; \
    fi && \
    wget --quiet -O tini "https://github.com/krallin/tini/releases/download/v0.19.0/${tini_binary}" && \
    echo "${tini_sha256} *tini" | sha256sum -c - && \
    mv tini /usr/local/bin/tini && \
    chmod +x /usr/local/bin/tini

ENTRYPOINT ["/usr/local/bin/tini", "--"]

CMD ["/bin/bash", "-c", "/workspaces/lean-playground/scripts/start_jupyter.sh && tail -f /dev/null"]
EXPOSE 8888 5678
