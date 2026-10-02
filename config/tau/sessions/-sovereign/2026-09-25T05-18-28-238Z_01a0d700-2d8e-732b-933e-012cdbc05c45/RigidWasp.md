**Plan**

The task is to create a simple, executable script that prints "hello" and verify it works correctly. We have already confirmed that `echo hello` works via a direct bash command, but we will now create a reusable script in the repository's `bin/` directory to ensure the behavior is encapsulated and testable.

**Steps**
1. **Create the script file** – Write `bin/hello.sh` with a proper shebang and the `echo hello` command.
2. **Make the script executable** – Set the executable permission on `bin/hello.sh`.
3. **Run the script directly** – Execute `bin/hello.sh` and capture its output.
4. **Verify output via explicit shell** – Run `sh bin/hello.sh` to ensure it works without relying on the shebang.
5. **Confirm no side effects** – Ensure the script does not produce errors or extra output.

**Already done**
- Verified that `echo hello` produces the expected output via a one-off bash command.

**Risks & Edge Cases**
- The `bin/` directory might not be writable; we will verify write ability before creating the file.
- The shebang path (`/bin/bash`) must exist; we assume a standard Linux environment.
- The script must not depend on any external state beyond the shell.

**Verification**
- Each step will be checked by running the command and comparing the output to the expected result.
- No modifications to existing test suites or verification assets are needed; we will only validate the new script's behavior.

---

Now, initialize the todo list to track these steps:
