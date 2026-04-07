# OnexExplorer — CLI-only image
# Build: docker build -t onexexplorer:cli .
# Run:   docker run --rm -v "$PWD/data:/work" onexexplorer:cli --cli --unpack /work/in.nos --target /work/out

FROM debian:bookworm-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    ninja-build \
    qtbase5-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev \
    freeglut3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY . .

RUN cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release \
    && cmake --build build \
    && strip build/OnexExplorer

FROM debian:bookworm-slim

# QApplication picks a platform before CLI parsing; without this, Qt defaults to xcb and fails with no DISPLAY.
ENV QT_QPA_PLATFORM=offscreen

RUN apt-get update && apt-get install -y --no-install-recommends \
    libqt5core5a \
    libqt5gui5 \
    libqt5widgets5 \
    libgl1 \
    libglu1-mesa \
    libglut3.12 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /src/build/OnexExplorer /usr/local/bin/onexexplorer

ENTRYPOINT ["/usr/local/bin/onexexplorer"]
