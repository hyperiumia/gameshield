FROM rust:1-slim AS builder
WORKDIR /usr/src/app
COPY Cargo.toml .
COPY src ./src
RUN cargo build --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /usr/src/app/target/release/gameshield-ingest /usr/local/bin/
EXPOSE 8080
CMD ["gameshield-ingest"]
