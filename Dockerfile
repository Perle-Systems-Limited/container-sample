#
# Dockerfile for sample Perle router docker image
#
# pslrestful.py is a generic module for accessing the RESTful API via python3.
# mon.py is a simple module that uses it for monitoring the router.
#

# Base image
FROM --platform=linux/arm64 debian:stable-slim

# Add python3.  Might want to add net-tools and iputils-ping too.
RUN apt-get update && \
	apt-get install -y --no-install-recommends python3 python3-requests && \
	rm -rf /var/lib/apt/lists/* /usr/share/doc/*

# The scripts
COPY pslrestful.py mon.py /usr/local/bin/

# What to run
CMD ["/usr/local/bin/mon.py"]
