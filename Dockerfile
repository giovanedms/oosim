# OOSim — reproducible container for the IAC 2026 paper artifacts
#
# Build:  docker build -t oosim .
# Run:    docker run --rm oosim                          # runs pytest
#         docker run --rm oosim python experiments/scripts/12_soyuz_ms17_full.py

FROM python:3.12-slim

WORKDIR /opt/oosim
COPY pyproject.toml README.md LICENSE-CODE ./
COPY oosim ./oosim
COPY tests ./tests
COPY experiments ./experiments

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -e .[dev] \
 && pip install --no-cache-dir sgp4

CMD ["pytest", "-v", "--tb=short"]
