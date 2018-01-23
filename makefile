#! SHELL=/bin/sh

supervisorctl = /home/work/supervisor/bin/supervisorctl

api_restart:
	@for port in {9000..9011}; \
	do\
		${supervisorctl} restart api:api-$$port; \
	done

api_restart1:
	@for port in {9000..9000}; \
	do\
		${supervisorctl} restart api:api-$$port; \
	done
