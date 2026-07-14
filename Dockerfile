# StrandMD — Streamlit web app + AmberTools + GROMACS bundled.
# Single-stage build on miniconda3 (Python 3.11 base).

# Pin to linux/amd64 — matches HuggingFace Spaces build target. On Apple
# Silicon (M-series) the build runs under qemu emulation (slower but correct).
FROM --platform=linux/amd64 continuumio/miniconda3:24.3.0-0

LABEL maintainer="Zibin Zhao <zhaozibin1999@gmail.com>"
LABEL description="StrandMD — trajectory-guided protein–nucleic-acid engineering"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ---- No apt step ----
# miniconda3 base already includes Python, ca-certificates, libstdc++,
# and conda itself. We skip apt entirely so the build works even when a
# local VPN/proxy intercepts deb.debian.org. The healthcheck uses Python
# (in base image) instead of curl.

# ---- Conda env: AmberTools + GROMACS + Python deps ----
# Done in one layer to keep image size manageable.
# Unpinned ambertools/gromacs so the solver picks compatible versions
# (specific pins fail when conda-forge's matrix doesn't have them together).
RUN conda install -n base -c conda-forge -c bioconda -y \
        python=3.11 \
        ambertools \
        gromacs \
        parmed \
        numpy \
        && conda clean -afy

# ---- StrandMD source + pip deps ----
WORKDIR /app

# Copy dependency manifest first for better layer caching
COPY pyproject.toml /app/pyproject.toml

# Install pip deps separately so source-only changes don't reinstall them
RUN pip install --no-cache-dir \
        'streamlit>=1.30' \
        'plotly>=5.18' \
        'MDAnalysis>=2.7' \
        'biopython>=1.83' \
        'python-docx>=1.1' \
        'python-pptx>=0.6' \
        'Jinja2>=3.1'

# Now copy source code + install StrandMD in dev mode
COPY src/ /app/src/
COPY app/ /app/app/
COPY .streamlit/ /app/.streamlit/
RUN pip install --no-cache-dir -e /app

# ---- Streamlit credentials (skip first-run email prompt) ----
RUN mkdir -p /root/.streamlit \
    && printf '[general]\nemail = ""\n' > /root/.streamlit/credentials.toml

# ---- Expose Streamlit's port ----
EXPOSE 8501

# ---- Healthcheck (HF Spaces uses this) ----
# Uses Python's stdlib instead of curl so we don't have to apt-install curl.
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; \
        r = urllib.request.urlopen('http://localhost:8501/_stcore/health', timeout=5); \
        sys.exit(0 if r.status == 200 else 1)" || exit 1

# ---- Default command: run the Streamlit UI ----
CMD ["python", "-m", "streamlit", "run", "/app/app/streamlit_app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
