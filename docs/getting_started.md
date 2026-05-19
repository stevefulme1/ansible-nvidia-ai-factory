# Getting Started with stevefulme1.gpu_ai_factory

>-

## Installation

```bash
ansible-galaxy collection install stevefulme1.gpu_ai_factory
```

## Requirements

- Ansible >= 2.16
- Python >= 3.12

## Authentication

Most modules require authentication credentials. Set these as variables
in your playbook, inventory, or Ansible Vault:

```yaml
vars:
  api_url: "https://your-service.example.com"
  api_token: "{{ vault_api_token }}"
  validate_certs: true
```

Store sensitive credentials in Ansible Vault:

```bash
ansible-vault encrypt_string 'your-token-here' --name 'vault_api_token'
```

## Quick Example

```yaml
---
- name: Example playbook
  hosts: localhost
  connection: local
  gather_facts: false
  collections:
    - stevefulme1.gpu_ai_factory
  tasks:
    - name: Get info
      stevefulme1.gpu_ai_factory.ai_factory_inventory_report:
        api_url: "{{ api_url }}"
        api_token: "{{ api_token }}"
      register: result

    - name: Show result
      ansible.builtin.debug:
        var: result
```

## Collection Contents

- **Modules**: 39
- **Roles**: 11
- **EDA plugins**: 3

## Next Steps

- Browse the module documentation: `ansible-doc stevefulme1.gpu_ai_factory.<module_name>`
- Check the [README](../README.md) for the full module and role list
- Review [CONTRIBUTING.md](../CONTRIBUTING.md) to contribute
