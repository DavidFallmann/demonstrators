FROM rust:latest AS builder
WORKDIR /usr/src/eprofiler
COPY . .
RUN cargo install --path .

FROM debian

RUN apt-get update && apt-get install -y openssl && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /usr/local/cargo/bin/eprofiler /usr/local/bin/eprofiler
COPY config.json /
COPY ./www /www

CMD ["eprofiler"]

