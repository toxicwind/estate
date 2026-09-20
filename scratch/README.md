# scratch/ — non-production staging (renamed from shingle-workspace)
One-off scripts, staging dirs, audits, patch harnesses. NOT a service home:
do not add pitchfork daemon `run` paths here. Production files that lived here
were extracted: the exec bridge -> ../bridge/, bin tools -> ../bin/,
bridge docs -> ../hatch/docs/bridge-docs/.
Compat: ../shingle-workspace -> scratch (symlink).
