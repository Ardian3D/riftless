"""Server-side DataHub MCP boundary for F8.2.

This package is intentionally not imported by application startup or routes.
"""

from .config import DataHubMCPConfig, load_datahub_mcp_config
from .initialization import DataHubMCPSession, initialize_datahub_mcp
from .tool_discovery import DataHubReadToolCatalog, DataHubReadToolCapability, DataHubReadToolName, discover_datahub_read_tools
from .search_contract import (
    DataHubReadToolDiscoveryBundle,
    DataHubSearchArgumentPlan,
    DataHubSearchContractError,
    DataHubSearchSchemaContract,
    build_datahub_search_argument_plan,
    build_datahub_search_tools_call_request,
    discover_datahub_read_tool_bundle,
    serialize_datahub_search_tools_call_request,
)

__all__ = [
    "DataHubMCPConfig",
    "DataHubMCPSession",
    "initialize_datahub_mcp",
    "load_datahub_mcp_config",
    "DataHubReadToolCatalog",
    "DataHubReadToolCapability",
    "DataHubReadToolName",
    "discover_datahub_read_tools",
    "DataHubReadToolDiscoveryBundle",
    "DataHubSearchArgumentPlan",
    "DataHubSearchContractError",
    "DataHubSearchSchemaContract",
    "build_datahub_search_argument_plan",
    "build_datahub_search_tools_call_request",
    "discover_datahub_read_tool_bundle",
    "serialize_datahub_search_tools_call_request",
]
