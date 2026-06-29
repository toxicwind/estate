_bpaf_dynamic_completion()
{
    local -a _args=("$1" "--bpaf-complete-rev=8" "${COMP_WORDS[@]:1}")
    source <( "${_args[@]}" )
}
complete -o nosort -F _bpaf_dynamic_completion flox
