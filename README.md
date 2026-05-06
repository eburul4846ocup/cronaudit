# cronaudit

> Lightweight utility that parses and summarizes crontab entries across multiple servers into a readable report.

---

## Installation

```bash
pip install cronaudit
```

Or install from source:

```bash
git clone https://github.com/youruser/cronaudit.git && cd cronaudit && pip install .
```

---

## Usage

Point `cronaudit` at a list of servers or local crontab files and generate a summary report:

```bash
# Audit crontabs on remote servers via SSH
cronaudit --hosts servers.txt --user deploy --output report.html

# Parse a local crontab file
cronaudit --file /etc/crontab --output report.txt

# Print a quick summary to stdout
cronaudit --hosts servers.txt --format table
```

**Example output:**

```
Server          User     Schedule        Command
--------------  -------  --------------  ----------------------------
web-01          root     0 2 * * *       /usr/bin/backup.sh
web-01          deploy   */15 * * * *    /app/scripts/healthcheck.py
db-01           postgres 0 0 * * 0       /usr/bin/pg_dump mydb
```

---

## Configuration

Create a `cronaudit.yaml` file to set defaults:

```yaml
hosts_file: servers.txt
ssh_user: deploy
output_format: table  # table | html | json
output_file: report.txt
```

---

## Requirements

- Python 3.8+
- `paramiko` for SSH connections
- `croniter` for schedule parsing

---

## License

This project is licensed under the [MIT License](LICENSE).