# This file must be used with "source activate.sh" *from bash*
# You cannot run it directly
#
# Run "make venv" to create .venv and install all dependencies there
#
source .venv/bin/activate
eval "$(declare -f deactivate | sed 's/^deactivate/_rex_venv_deactivate/')"
rex() { ( cd "${VIRTUAL_ENV}/.." && .venv/bin/python3 -m RisExUtils "$@"; ); }
risen() { ( cd "${VIRTUAL_ENV}/.." && .venv/bin/ptipython -i RisEnQuery.py "$@"; ); }
deactivate() {
	unset -f rex
	unset -f risen
	_rex_venv_deactivate
	unset -f _rex_venv_deactivate
	unset -f deactivate
}
if [ -z "${VIRTUAL_ENV_DISABLE_PROMPT:-}" ] ; then
	export PS1="(RisEx) ${PS1#${VIRTUAL_ENV_PROMPT}}"
	export VIRTUAL_ENV_PROMPT='(RisEx) '
fi
