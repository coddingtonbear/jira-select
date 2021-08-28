ifeq ($(OS),Windows_NT)
	activate_script := ./env/Scripts/activate.bat
else
	activate_script := . env/bin/activate
endif

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
	@/usr/bin/env python -m pip install virtualenv
	@/usr/bin/env python -m virtualenv ./env
	@$(activate_script) && python -m pip install -e ../
	@$(activate_script) && python -m pip uninstall -y simpleeval
	@$(activate_script) && python -m pip install -r ./requirements.txt

exe: clean new
	@$(activate_script) && pyinstaller ./jira_select.exe.spec

dir: clean new
	@$(activate_script) && pyinstaller ./jira_select.spec
