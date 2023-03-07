update:
	@transwarp -D specification -I templates/python/ -L templates/lib -O libflagship -u

diff:
	@transwarp -D specification -I templates/python/ -L templates/lib -O libflagship -d

install-tools:
	git submodule update --init
	pip install ./transwarp
