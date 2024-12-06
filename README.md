# Perle sample container for routers

#### update on 2024-12-06

Add a build support to make a x86 image to run on scrx

To make a x86 container image, type "make -f Makefile_x86"
To make a x86 container image tarball, type "sudo make -f Makefile_x86 pslsample_x86.img.gz"


#### OVERVIEW

This directory contains two sample python3 scripts.  They can be run
directly from any computer on the network to interrogate a Perle router
for its status using the RESTful API.

This directory also contains a `Dockerfile` suitable for building
a basic Linux image with python3 and the above scripts.
This can be run in a container on the router itself.

#### THE SCRIPTS

- `pslrestful.py`

	A generic base class `PSL_RESTfulAPI` for accessing the router RESTful API.
	Derive a class from this to develop your own functionality, or just make
	an instance of the class and use it directly as in the `main()` example
	in the script itself.

- `mon.py`

	A sample that uses the above pslrestful to show the router status.
	Change this as necessary to do what you wish.

If you already have a router available on the network, you can run
`mon.py` directly from any computer that has python3 installed on it.
The script takes IP, PORT, USER and PASS either as arguments or
environment variables.  Type `python3 mon.py` for usage.

If you get an error about the module `requests` being missing when
you run the script, install it via `pip install requests`

Running the python code from a remote computer is generally easier
for debugging.  You should only need to run it in a router container
for eventual deployment in the field.

The .yaml file describing the available commands can be
found at `flash:managed-devices.yaml` of the router and at
<https://www.perle.com/downloads/lte-routers.shtml> .
This file can be loaded into an yaml editor such as the
online swagger editor at <https://editor.swagger.io/>

#### BUILDING AN IMAGE

A prebuilt pslsample.img.gz (compressed image) is included in this repository.
Use the following instructions to build it yourself.

If you are on a Linux/Cygwin box with docker installed,
type "make" to create the image.  This will use the supplied
Dockerfile to create a sample image using the python scripts.

Otherwise, type these commands on the PC containing this README.md file.

	docker run --rm --privileged aptman/qus -s -- -p aarch64
	docker image build -t pslsample .
	docker image save pslsample > pslsample.img

1. The first command installs arm64 emulation for Docker which is necessary
only if you are *not* using an arm64 computer such as a Raspberry PI
(e.g. you are using a standard Intel PC)

2. The second command builds the image (don't forget the "." at the end).

3. The third command saves the image from docker into a local file pslsample.img

If you have gzip you may want to compress pslsample.img to save space.
The router handles both compressed and uncompressed images.

Copy the resulting pslsample.img (or pslsample.img.gz if compressed)
to the `flash:` partition of the router.  Then, on the router install the
image using the CLI like this:

	container image add load-from flash:pslsample.img

or if compressed:

	container image add load-from flash:pslsample.img.gz

When complete it should show up in `show container images`

#### CONFIGURING THE ROUTER

You will need to:

1. Enable the RESTful API
2. Enable container management
3. Define a BVI and container network for the container to use
4. Define the container itself.

For the container network, the specific IP does not matter as long as
it is an available local network.  The container will use this to
communicate to the RESTful API on the router itself.

Make sure the IP of the environment matches the network and that USER/PASS
is a valid existing router user.  Also ensure that the IP value matches
the address of the corresponding BVI network.  In the example below,
the container is at 192.168.78.11 and the API is at 192.168.78.1 .

The script `mon.py` also supports optional environment variables DELAY for
the delay in seconds and LOOPS for how many times to loop before exiting.

The below CLI config mode commands assume the login admin/mypasswd
is already set up on the router.

    remote-management
	 restful-api http

	interface BVI78
	 ip address 192.168.78.1 255.255.255.0

    container-management enable

	container network net78
	 network-interface BVI 78

	container name pslsample_cont
	 image pslsample
	 network net78 ip address 192.168.78.11
	 environment IP 192.168.78.1
	 environment USER admin
	 environment PASS mypasswd
	 environment PORT 8080
	 no disable

If you need internet access from inside the container itself, you will
also need to enable NAT.  The below assumes that all Ethernet ports are
bridged into BVI 1:

	ip nat inside source any interface BVI 1 overload

Once the container is running, you can examine its progress via:

	show container log pslsample_cont

By default the image runs `/usr/local/bin/mon.py`.
If you want to look around in the container itself,
add this to the container definition to make it just
run an interactive shell instead of mon.py:

	arguments 1 /bin/bash
	arguments 2 -i

Then restart it and do `container connect pslsample_cont` for shell
access in the container.

The scripts are in /usr/local/bin/ and can be modified inside the
container if you use the "apt" command to install a simple editor
(e.g. `apt install nano` or `apt install vim-tiny`).  Be aware that
any changes you make will be in that container only and not the source
image pslsample.img, and so will be lost on a restart done via
"container force-remove restart".

You can run the script when connected by typing "mon.py".
