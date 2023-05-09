update:
	@transwarp -D specification -I templates/python/ -L templates/lib -O libflagship -u

diff:
	@transwarp -D specification -I templates/python/ -L templates/lib -O libflagship -d

install-tools:
	git submodule update --init
	pip install ./transwarp

clean:
	@find -name '*~' -o -name '__pycache__' -print0 | xargs -0 rm -rfv
