# Lean Playground - QuantConnect Lean algorithmic trading research environment
FROM quantconnect/research:latest

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

# Install oh-my-zsh with headline theme
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
RUN wget https://raw.githubusercontent.com/moarram/headline/main/headline.zsh-theme && \
    sed -i "s/'echo \$USER'/'whoami'/g" headline.zsh-theme && \
    sed -i "s/'basename \"\$VIRTUAL_ENV\"'/'basename \"\$CONDA_DEFAULT_ENV\"'/g" headline.zsh-theme && \
    mv headline.zsh-theme /root/.oh-my-zsh/themes/headline.zsh-theme && \
    echo 'source /root/.oh-my-zsh/themes/headline.zsh-theme' >> /root/.zshrc

# UV package manager
RUN pip install uv
ENV UV_SYSTEM_PYTHON=1 \
    UV_PROJECT_ENVIRONMENT="/usr/local"

# Install Lean CLI (optional — for users with QuantConnect subscription)
RUN uv pip install lean

# Copy requirements and install project-specific dependencies
COPY requirements.txt ./
RUN uv pip install --system -r requirements.txt

# Download Python algorithm examples from Lean repo (~500 examples)
RUN git clone --depth 1 --filter=blob:none --sparse \
      https://github.com/QuantConnect/Lean.git /tmp/lean-source && \
    cd /tmp/lean-source && \
    git sparse-checkout set Algorithm.Python && \
    cp -r Algorithm.Python /Lean/Algorithm.Python && \
    rm -rf /tmp/lean-source

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

# Use base image's start.sh (creates Lean config.json + starts JupyterLab)
CMD ["/bin/sh", "-c", "/Lean/Launcher/bin/Debug/start.sh"]
EXPOSE 8888
