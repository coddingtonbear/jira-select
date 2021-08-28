help:
	@echo 'Usage:'
	@echo '	make clean: Clean up the local environment'
	@echo '	make new: Set-up a new environment'
	@echo '	make exe: Package app as single executable'
	@echo '	make dir: Package app as directory'

.PHONY: clean new exe dir

clean:
	@/bin/rm -rf env build dist

new:
	@/usr/bin/env virtualenv ./env
	@./env/bin/python -m pip install -e ../
	@./env/bin/python -m pip uninstall -y simpleeval
	@./env/bin/python -m pip install -r ./requirements.txt

exe: clean new
	@./env/bin/pyinstaller ./jira_select.exe.spec

dir: clean new
	@./env/bin/pyinstaller ./jira_select.spec
