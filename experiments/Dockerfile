FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.7.13 /uv /usr/local/bin/uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash ca-certificates curl git ripgrep jq patch procps findutils less \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home agent && mkdir /workspace && chown agent:agent /workspace
COPY sandbox.py /opt/loopguard/sandbox.py
USER agent
WORKDIR /workspace
ENTRYPOINT ["python", "/opt/loopguard/sandbox.py", "start"]
CMD ["--", "bash"]
