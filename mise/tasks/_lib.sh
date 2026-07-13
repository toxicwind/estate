set -euo pipefail
export SOV="${SOVEREIGN_ROOT:-$PWD}"
cd "$SOV"
pc_args(){
 local a=("$SOV/stack/base.yaml")
 for m in "$@";do a+=("$SOV/stack/modules/${m}.yaml");done
 printf "%s\n" "${a[@]}"
}
pc_up(){
 local cfgs=()
 while IFS= read -r l;do cfgs+=(--config "$l");done < <(pc_args "$@")
 # process-compose inherits env from mise automatically
 exec process-compose --address 127.0.0.1 up "${cfgs[@]}" -D
}