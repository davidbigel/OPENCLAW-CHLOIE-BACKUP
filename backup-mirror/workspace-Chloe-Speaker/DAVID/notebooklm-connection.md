# NotebookLM Connection

Convenient command:

```bash
notebooklm-connect status
```

This command is installed as a global symlink to:

```text
/root/.openclaw/workspace-Chloe-Speaker/DAVID/notebooklm-connect
```

It wraps the existing NotebookLM workspace:

```text
/root/.openclaw/workspace-GOOG-V1-01-NotebookLM
```

## Commands

```bash
notebooklm-connect status
notebooklm-connect login
notebooklm-connect bootstrap
notebooklm-connect list
notebooklm-connect ask "question"
notebooklm-connect raw <notebooklm args...>
notebooklm-connect stop-login
```

## Current State

The local CLI and wrappers are installed and runnable. Authentication currently needs a fresh Google / NotebookLM login before notebook listing works.

Use this flow:

```bash
notebooklm-connect login
# complete Google login in the VNC browser
notebooklm-connect bootstrap
notebooklm-connect list
```

Security note: start the VNC login browser only when needed, then stop it:

```bash
notebooklm-connect stop-login
```
