# Tool Documentation

AgentSkills MCP utilizes four tools to load Agent Skills, following the descriptions in [Anthropic's Agent Skills Engineering Blog](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) to implement *Progressive Disclosure* architecture.


## Tool 1: load_skill_metadata_op

<p align="left">
  <em>Load metadata from all available skills (always call at task start).</em>
</p>

### Description

This tool scans the skills directory recursively for SKILL.md files and extracts their metadata (name and description) from YAML frontmatter. The metadata is returned as a dictionary where keys are skill names and values contain the description and skill directory path.

### Key Operation Flow

- Gets the skills directory path from the context
- Recursively searches for all SKILL.md files
- Parses each file's frontmatter to extract metadata
- Builds a dictionary with skill names as keys
- Sets the output with the complete metadata dictionary

### Input Parameters

This tool requires no input parameters and will scan the skills directory to load all available skill metadata.
The skills directory path is obtained from `self.context.skill_dir`. Only SKILL.md files with valid YAML frontmatter containing both 'name' and 'description' fields will be included in the results.

### Returns

dict: A dictionary `skill_metadata_dict` mapping skill names to their metadata. Each entry has the format:

    {
        "skill_name": {
            "description": "Skill description text",
            "skill_dir": "/path/to/skill/directory"
        }
    }

### Test Demo

```bash
python tests/test_load_skill_metadata_op.py <path/to/skills>
```

---

## Tool 2: `load_skill_op`

<p align="left">
  <em>Load a specific skill's instructions (i.e., SKILL.md).</em>
</p>

### Description

This tool loads the content of a SKILL.md file for a given skill name. The skill directory is retrieved from the context's `skill_metadata_dict`, which should be initilized by load_skill_metadata_op beforehand.

### Key Operation Flow

- Takes a skill_name as input
- Looks up the skill directory from skill_metadata_dict
- Reads the SKILL.md file from that directory
- Returns the file content

### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skill_name` | string | Yes | - | Name of the skill |

### Returns

str: The skill instructions content. If the SKILL.md file exists, returns the file content. Otherwise, returns an error message string.

> [!TIP]
> You can ref to [official Anthropic documentation](https://code.claude.com/docs/en/skills) on the Skills format.

### Test Demo

```bash
python tests/test_load_skill_op.py <path/to/skills> <skill_name>
```

---

## Tool 3: read_reference_file_op

<p align="left">
  <em>Read reference files from a skill directory.</em>
</p>

### Description

This tool allows reading reference files like forms.md, reference.md, or  from a specific skill's directory. It retrieves the skill directory from the `skill_metadata_dict`, constructs the file path, and reads the file content if it exists.

### Key Operation Flow

- Takes a skill_name and file_name as input
- Looks up the skill directory from skill_metadata_dict
- Constructs the file path as {skill_dir}/{file_name}
- Reads the file content if it exists
- Returns the file content or an error message if not found

### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skill_name` | string | Yes | - | Name of the skill |
| `file_name` | string | Yes | - | The reference file name or file path relative to the skill directory |

### Returns

str: The content of the reference file read from the skill directory. If the file is not found, returns an error message string indicating that the file was not found in the specified skill.

### Test Demo

```bash
python tests/test_reference_file_op.py <path/to/skills> <skill_name> <file_name>
```

---

## Tool 4: run_shell_command_op

<p align="left">
  <em>Execute shell commands to run scripts within skill directories.</em>
</p>

### Description

This tool executes shell commands and can automatically detect and install dependencies for script files (Python, JavaScript, Shell). The command is executed in the skill's directory context, allowing scripts to access skill-specific files and resources.

### Key Operation Flow

- Extract skill_name and command from input
- Look up the skill directory from skill_metadata_dict
- Change to the skill directory before executing the command
- For Python commands, automatically detect and install dependencies using pipreqs (if available and auto_install_deps parameter is enabled)
- Execute the command in a subprocess and capture stdout/stderr
- Return the combined output (stdout + stderr)


### Input Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skill_name` | string | Yes | - | Name of the skill |
| `command` | string | Yes | - | The shell command to execute |


### Returns

str: The combined stdout and stderr output from the command execution. The output is decoded as UTF-8 and formatted as: "{stdout}\n{stderr}". 


> [!NOTE]
> Dependency auto-installation only occurs for commands containing "py" and when the auto_install_deps parameter is enabled
> The command runs in the skill's directory, allowing access to skill-specific files and resources


### Test Demo

```bash
python tests/run_shell_command_op.py <path/to/skills> <skill_name> <command>
```