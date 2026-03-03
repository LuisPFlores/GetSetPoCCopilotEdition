# GetSetPOx MCP Server

A Python **Model Context Protocol (MCP)** server that wraps the
[GetSetPOx](https://github.com/jeevanbisht/GetSetPOx) services and exposes
them as **31 typed MCP tools** for:

| Consumer | Transport |
|---|---|
| **Cline / Claude Code** | stdio |
| **GitHub Copilot CLI / VS Code** | stdio |
| **Microsoft Copilot Studio** | HTTP/SSE |
| **Azure Container Apps** | HTTP/SSE |

All tools authenticate against **Microsoft Graph** using the
**client credentials flow** (app registration + client secret).

---

## Prerequisites

### Azure AD App Registration

Create an app registration with the following **Application** (not delegated)
API permissions and **admin consent** granted:

| Permission | Used by |
|---|---|
| `Application.Read.All` | Diagnostics |
| `Device.Read.All` | Diagnostics, EID |
| `DeviceManagementApps.ReadWrite.All` | Intune |
| `DeviceManagementConfiguration.ReadWrite.All` | Intune |
| `DeviceManagementManagedDevices.ReadWrite.All` | Intune |
| `Directory.Read.All` | Diagnostics, EID |
| `EntitlementManagement.ReadWrite.All` | IGA, POC |
| `Group.ReadWrite.All` | EID, IGA, POC |
| `GroupMember.ReadWrite.All` | EID |
| `NetworkAccess.ReadWrite.All` | Internet Access / GSA |
| `Policy.ReadWrite.ConditionalAccess` | Internet Access / GSA |
| `User.Read.All` | EID |

After creating the app:

1. Note the **Application (client) ID**.
2. Create a **client secret** and note its value immediately.
3. Note your **Tenant ID** (Azure AD → Overview).

---

## Quick Start — Local Development

```bash
# 1. Clone this repository
git clone https://github.com/jeevanbisht/GetSetPOx.git
cd GetSetPOx

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install the upstream services package
pip install -e ./GetSetPOx_repo

# 4. Install the MCP server package
pip install -e ".[dev]"

# 5. Configure environment variables
cp .env.example .env
# Edit .env and fill in MS_GRAPH_CLIENT_ID, MS_GRAPH_CLIENT_SECRET,
# MS_GRAPH_TENANT_ID

# 6. Run the server (stdio — for Cline / Copilot CLI)
python -m getset_pox_mcp_server.server

# Or run the HTTP server (for Copilot Studio)
python -m getset_pox_mcp_server.main_http
```

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `MS_GRAPH_CLIENT_ID` | ✅ | Azure AD app registration client ID |
| `MS_GRAPH_CLIENT_SECRET` | ✅ | Client secret value |
| `MS_GRAPH_TENANT_ID` | ✅ | Azure AD / Entra tenant ID |
| `MCP_LOG_LEVEL` | ➖ | `DEBUG` / `INFO` / `WARNING` (default: `INFO`) |
| `MCP_HTTP_HOST` | ➖ | HTTP bind host (default: `0.0.0.0`) |
| `MCP_HTTP_PORT` | ➖ | HTTP bind port (default: `8080`) |

---

## Using with Cline / Claude Code (stdio)

### Option A — `.env` file

Set the three `MS_GRAPH_*` variables in `.env` at the project root, then
run:

```bash
python -m getset_pox_mcp_server.server
```

### Option B — Cline `mcp.json`

Add the following to your Cline MCP configuration
(`~/.cline/mcp.json` or `.vscode/mcp.json`):

```json
{
  "servers": {
    "getset-pox": {
      "command": "python",
      "args": ["-m", "getset_pox_mcp_server.server"],
      "cwd": "C:/Py/GetSetPOCV1",
      "env": {
        "MS_GRAPH_CLIENT_ID":     "${env:MS_GRAPH_CLIENT_ID}",
        "MS_GRAPH_CLIENT_SECRET": "${env:MS_GRAPH_CLIENT_SECRET}",
        "MS_GRAPH_TENANT_ID":     "${env:MS_GRAPH_TENANT_ID}"
      }
    }
  }
}
```

---

## Using with GitHub Copilot CLI / VS Code

### VS Code `settings.json`

```json
{
  "mcp.servers": {
    "getset-pox": {
      "command": "python",
      "args": ["-m", "getset_pox_mcp_server.server"],
      "env": {
        "MS_GRAPH_CLIENT_ID":     "${env:MS_GRAPH_CLIENT_ID}",
        "MS_GRAPH_CLIENT_SECRET": "${env:MS_GRAPH_CLIENT_SECRET}",
        "MS_GRAPH_TENANT_ID":     "${env:MS_GRAPH_TENANT_ID}"
      }
    }
  }
}
```

### GitHub Copilot CLI (`~/.copilot/mcp.json`)

```json
{
  "servers": {
    "getset-pox": {
      "command": "python",
      "args": ["-m", "getset_pox_mcp_server.server"]
    }
  }
}
```

Set `MS_GRAPH_*` in your shell profile or export them before running
`gh copilot`.

---

## Using with Microsoft Copilot Studio (HTTP/SSE)

### Step 1 — Deploy the HTTP server

#### Docker (local test)

```bash
docker build -t getset-pox-mcp-server .

docker run -p 8080:8080 \
  -e MS_GRAPH_CLIENT_ID=<client-id> \
  -e MS_GRAPH_CLIENT_SECRET=<client-secret> \
  -e MS_GRAPH_TENANT_ID=<tenant-id> \
  getset-pox-mcp-server
```

Verify: `curl http://localhost:8080/health`

#### Azure Container Apps

```bash
# Login and set subscription
az login
az account set --subscription <subscription-id>

# Create resource group and ACR
az group create -n rg-getset-pox -l eastus
az acr create -n getsetpoxacr -g rg-getset-pox --sku Basic --admin-enabled true

# Build and push image
az acr build -t getset-pox-mcp-server:latest -r getsetpoxacr .

# Create Container Apps environment
az containerapp env create -n cae-getset-pox -g rg-getset-pox -l eastus

# Deploy
az containerapp create \
  -n getset-pox-mcp \
  -g rg-getset-pox \
  --environment cae-getset-pox \
  --image getsetpoxacr.azurecr.io/getset-pox-mcp-server:latest \
  --registry-server getsetpoxacr.azurecr.io \
  --target-port 8080 \
  --ingress external \
  --secrets \
    clientid=<client-id> \
    clientsecret=<client-secret> \
    tenantid=<tenant-id> \
  --env-vars \
    MS_GRAPH_CLIENT_ID=secretref:clientid \
    MS_GRAPH_CLIENT_SECRET=secretref:clientsecret \
    MS_GRAPH_TENANT_ID=secretref:tenantid
```

Note the assigned HTTPS URL, e.g.:

```
https://getset-pox-mcp.<random>.eastus.azurecontainerapps.io
```

Your MCP endpoint is:

```
https://getset-pox-mcp.<random>.eastus.azurecontainerapps.io/mcp
```

### Step 2 — Connect to Copilot Studio

1. Open [Copilot Studio](https://copilotstudio.microsoft.com).
2. Select your agent (or create a new one).
3. Go to **Settings → Actions & connectors → MCP servers**.
4. Click **Add MCP server**.
5. Enter the MCP endpoint URL:
   `https://<yourapp>.azurecontainerapps.io/mcp`
6. Click **Connect** — Copilot Studio will enumerate all 31 tools
   automatically.
7. Tools appear as **Actions** in the agent dialog with their names,
   descriptions, inputs, and outputs inherited directly from the MCP server.

> **Authentication**: For production, configure Entra ID authentication
> on the Container App and use the Copilot Studio OAuth connector instead
> of open CORS.  The current setup (CORS `*`) is suitable for POC/dev only.

---

## Tool Catalog

### Diagnostics

| Tool | Description | Inputs | Output |
|---|---|---|---|
| `pox_check_token_permissions` | Test all 19 Graph API permissions live | — | `{summary: {working, missing, total}, tests: [...]}` |

### Entra ID (EID)

| Tool | Description | Inputs | Output |
|---|---|---|---|
| `eid_list_users` | List all Entra ID users | — | `{users: [...], count}` |
| `eid_get_user` | Get user by object ID or UPN | `user_principal_name` | `{user: {...}}` |
| `eid_search_users` | Search users by displayName/UPN prefix | `query`, `top?` | `{users: [...], count, query}` |
| `eid_list_devices` | List all Entra ID devices | — | `{devices: [...], count}` |
| `eid_get_device` | Get device by object ID | `device_id` | `{device: {...}}` |
| `eid_get_groups` | List all groups | `top?` | `{groups: [...], count}` |
| `eid_get_group` | Get group by object ID | `group_id` | `{group: {...}}` |
| `eid_get_group_members` | List group members | `group_id`, `top?` | `{members: [...], count, group_id}` |
| `eid_search_groups` | Search groups by displayName prefix | `query`, `top?` | `{groups: [...], count, query}` |
| `eid_create_security_group` | Create a static security group | `group_name`, `description?`, `user_ids?`, `group_ids?`, `mail_enabled?`, `add_prefix?` | `{group: {...}, members: {...}}` |

### Identity Governance & Administration (IGA)

| Tool | Description | Inputs | Output |
|---|---|---|---|
| `iga_list_access_packages` | List all Entitlement Management access packages | `select?`, `filter?`, `expand?` | `{accessPackages: [...], count}` |
| `iga_create_access_catalog` | Create an access package catalog | `display_name`, `description`, `state`, `is_externally_visible` | `{catalog: {...}, catalogId}` |
| `iga_create_access_package` | Create an access package | `catalog_id`, `display_name`, `description?` | `{accessPackage: {...}, accessPackageId, catalogId}` |
| `iga_add_group_to_access_package` | Add a group resource to an access package | `catalog_id`, `access_package_id`, `group_object_id` | `{resourceId, roleId, role: "Member"}` |

### Internet Access / Global Secure Access (GSA)

| Tool | Description | Inputs | Output |
|---|---|---|---|
| `ia_check_forwarding_profile` | Check Internet Access forwarding profile state | — | `{name, state, id}` |
| `ia_enable_forwarding_profile` | Enable/disable forwarding profile | `forwarding_profile_id`, `state?` | `{name, id, message}` |
| `ia_create_filtering_policy` | Create a web content filtering policy | `name?`, `description?`, `web_categories?` | `{policy_name, policy_id}` |
| `ia_create_filtering_profile` | Create a filtering profile | `name?`, `description?`, `state?`, `priority?` | `{profile_name, profile_id}` |
| `ia_link_policy_to_profile` | Link a filtering policy to a profile | `filtering_profile_id`, `filtering_policy_id`, `priority?` | `{profile_id, policy_id, link_id}` |
| `ia_create_conditional_access_policy` | Create a CA policy for GSA filtering | `filtering_profile_id`, `display_name?`, `include_users?`, `include_groups?`, `include_applications?` | `{policy_name, policy_id}` |
| `ia_tls_onboarding` | Automate TLS inspection onboarding (CSR→sign→upload) | `name?`, `common_name?`, `organization_name?`, `cert_output_dir?`, `max_retries?` | `{csr_generation, signing_upload, root_ca_download, retry_metrics}` |
| `ia_internet_access_poc` | End-to-end Internet Access POC (5 steps) | `forwarding_profile_id`, many optional params | `{steps: [...], summary}` |

### Intune

| Tool | Description | Inputs | Output |
|---|---|---|---|
| `intune_list_managed_devices` | List Intune-managed devices | `top?` | `{devices: [...], count}` |
| `intune_get_device_details` | Get a specific managed device | `device_id` | `{device: {...}}` |
| `intune_list_compliance_policies` | List device compliance policies | — | `{policies: [...], count}` |
| `intune_list_config_profiles` | List device configuration profiles | — | `{profiles: [...], count}` |
| `intune_sync_device` | Send sync command to a device | `device_id` | `{deviceId, message}` |
| `intune_deploy_gsa_client` | Upload GSA Win32 client to Intune | `display_name?`, `description?`, `publisher?`, `sas_url?` | `{app_id, content_version_id, display_name}` |
| `intune_assign_app_to_groups` | Assign an Intune app to groups | `app_id`, `group_ids`, `intent?`, `notification_settings?`, `restart_grace_period?`, `delivery_optimization_priority?` | `{app, assignment, assignments: [...]}` |

### POC Orchestration

| Tool | Description | Inputs | Output |
|---|---|---|---|
| `poc_govern_internet_access` | Full Govern Internet Access POC (4 steps) | — | `{group_id, catalog_id, access_package_id, resource_assignment_id}` |

---

## Response Shape

Every tool returns one of two envelope shapes:

**Success**

```json
{
  "success": true,
  "data": { "...": "..." }
}
```

**Error**

```json
{
  "success": false,
  "error": {
    "code":    "SERVICE_ERROR",
    "message": "Human-readable description",
    "details": { "...": "..." }
  }
}
```

This consistent envelope means both Claude and Copilot Studio can interpret
results without special per-tool parsing.

---

## Project Layout

```
getset_pox_mcp_server/
├── __init__.py
├── server.py            # FastMCP stdio entry point (Cline / Copilot CLI)
├── main_http.py         # FastMCP HTTP/SSE entry point (Copilot Studio)
├── auth.py              # MSAL client-credentials token acquisition
├── services_adapter.py  # Auth bridge + response normalisation
└── tools/
    ├── __init__.py              # register_all_tools(mcp)
    ├── diagnostics_tools.py     # 1 tool
    ├── eid_tools.py             # 10 tools
    ├── iga_tools.py             # 4 tools
    ├── internet_access_tools.py # 8 tools
    ├── intune_tools.py          # 7 tools
    └── poc_tools.py             # 1 tool

GetSetPOx_repo/          # Upstream service code (read-only)
pyproject.toml
Dockerfile
.env.example
README.md
```

---

## Authentication Architecture

```
MCP Client (Cline / Copilot Studio)
         │
         ▼
  getset_pox_mcp_server
  ┌──────────────────────────────────────────────────────┐
  │  server.py / main_http.py                            │
  │         │                                            │
  │  tools/*.py  ──► services_adapter.safe_call()        │
  │                         │                            │
  │               getset_pox_mcp services                │
  │                         │                            │
  │               auth.get_auth_middleware()             │
  │                         │   (bridged from            │
  │               auth.py   │    MS_GRAPH_* → ENTRA_*)   │
  └──────────────────────────────────────────────────────┘
         │
         ▼
  MSAL ConfidentialClientApplication
  (client credentials flow)
         │
         ▼
  https://graph.microsoft.com/v1.0
```

---

## License

MIT