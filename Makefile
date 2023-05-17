update:
	@transwarp -D specification -I templates/python/ -L templates/lib -O libflagship -u
	@transwarp -D specification -I templates/js/     -L templates/lib -O static      -u

diff:
	@transwarp -D specification -I templates/python/ -L templates/lib -O libflagship -d
	@transwarp -D specification -I templates/js/     -L templates/lib -O static      -d

install-tools:
	git submodule update --init
	pip install ./transwarp

clean:
	@find -name '*~' -o -name '__pycache__' -print0 | xargs -0 rm -rfv
