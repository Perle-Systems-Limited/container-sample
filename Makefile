#
# Perle docker sample Makefile
#
# On a Linux or Cygwin box, type "make".
#

NAME=pslsample
IMG=$(NAME).img
ARCH=aarch64

# UPDATE WITH YOUR ROUTER IP/PORT/USER/PASS values and do "make test"
IP ?= 192.168.0.123
PORT ?= 8080
USER ?= admin
PASS ?= perle1

$(IMG): Dockerfile pslrestful.py mon.py
	# Install build emulation if needed (for arm64 routers)
	test `arch` = $(ARCH) || { docker history -q aptman/qus > /dev/null || docker run --rm --privileged aptman/qus -s -- -p $(ARCH); }
	# Build the image
	docker image build -t $(NAME) .
	# Save as file
	docker image save $(NAME) > $@
	gzip < $@ > $@.gz

test: $(IMG)
	# Run directly in local docker
	docker run --rm -t -e IP=$(IP) -e PORT=$(PORT) -e USER=$(USER) -e PASS=$(PASS) $(NAME)

clean:
	rm -rf __pycache__ $(IMG) $(IMG).gz
	-docker image rm $(NAME)
