"""Service Principals resource module for Microsoft Graph.

This module provides access to Microsoft Graph service principal resources.
"""

import logging
from typing import Dict, List, Any, Optional
from utils.graph_client import GraphClient
from msgraph.generated.models.service_principal import ServicePrincipal

logger = logging.getLogger(__name__)

async def list_service_principals(graph_client: GraphClient, limit: int = 100) -> List[Dict[str, Any]]:
    """List all service principals in the tenant, with paging."""
    try:
        client = graph_client.get_client()
        response = await client.service_principals.get()
        service_principals = []
        if response and response.value:
            service_principals.extend(response.value)
        # Paging: fetch more if odata_next_link is present
        while response is not None and getattr(response, 'odata_next_link', None) and len(service_principals) < limit:
            response = await client.service_principals.with_url(response.odata_next_link).get()
            if response and response.value:
                service_principals.extend(response.value)
        formatted_sps = []
        for sp in service_principals[:limit]:
            sp_data = {
                'id': getattr(sp, 'id', '') or '',
                'appId': getattr(sp, 'app_id', '') or '',
                'displayName': getattr(sp, 'display_name', '') or '',
                'createdDateTime': sp.created_date_time.isoformat() if getattr(sp, 'created_date_time', None) else '',
                'accountEnabled': getattr(sp, 'account_enabled', None) if getattr(sp, 'account_enabled', None) is not None else False,
                'appOwnerOrganizationId': str(getattr(sp, 'app_owner_organization_id', '')) if getattr(sp, 'app_owner_organization_id', None) else '',
                'tags': getattr(sp, 'tags', []) or [],
            }
            formatted_sps.append(sp_data)
        return formatted_sps
    except Exception as e:
        logger.error(f"Error listing service principals: {str(e)}")
        raise

async def get_service_principal_by_app_id(graph_client: GraphClient, app_id: str) -> Optional[Any]:
    """Get a service principal by its appId (application client ID)."""
    try:
        client = graph_client.get_client()
        # Filter by appId
        filter_query = f"appId eq '{app_id}'"
        response = await client.service_principals.get(query_parameters={"$filter": filter_query})
        if response and response.value:
            return response.value[0]  # Return the first match
        return None
    except Exception as e:
        logger.error(f"Error getting service principal by appId {app_id}: {str(e)}")
        raise

async def get_service_principal_by_id(graph_client: GraphClient, sp_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific service principal by its object ID, including appRoleAssignments and oauth2PermissionGrants."""
    try:
        client = graph_client.get_client()
        sp = await client.service_principals.by_service_principal_id(sp_id).get()
        if sp:
            sp_data = {
                'id': getattr(sp, 'id', '') or '',
                'appId': getattr(sp, 'app_id', '') or '',
                'displayName': getattr(sp, 'display_name', '') or '',
                'createdDateTime': sp.created_date_time.isoformat() if getattr(sp, 'created_date_time', None) else '',
                'accountEnabled': getattr(sp, 'account_enabled', None) if getattr(sp, 'account_enabled', None) is not None else False,
                'appOwnerOrganizationId': str(getattr(sp, 'app_owner_organization_id', '')) if getattr(sp, 'app_owner_organization_id', None) else '',
                'tags': getattr(sp, 'tags', []) or [],
            }
            # Fetch appRoleAssignments (application permissions)
            app_role_assignments = []
            try:
                response = await client.service_principals.by_service_principal_id(sp_id).app_role_assignments.get()
                while response:
                    if response.value:
                        for assignment in response.value:
                            created_dt = getattr(assignment, 'created_date_time', None)
                            app_role_assignments.append({
                                'id': getattr(assignment, 'id', '') or '',
                                'createdDateTime': created_dt.isoformat() if created_dt else '',
                                'appRoleId': str(getattr(assignment, 'app_role_id', '')) if getattr(assignment, 'app_role_id', None) else '',
                                'principalDisplayName': getattr(assignment, 'principal_display_name', '') or '',
                                'principalId': str(getattr(assignment, 'principal_id', '')) if getattr(assignment, 'principal_id', None) else '',
                                'principalType': getattr(assignment, 'principal_type', '') or '',
                                'resourceDisplayName': getattr(assignment, 'resource_display_name', '') or '',
                                'resourceId': str(getattr(assignment, 'resource_id', '')) if getattr(assignment, 'resource_id', None) else '',
                            })
                    if getattr(response, 'odata_next_link', None):
                        response = await client.service_principals.by_service_principal_id(sp_id).app_role_assignments.with_url(response.odata_next_link).get()
                    else:
                        break
            except Exception as e:
                logger.warning(f"Error fetching appRoleAssignments for service principal {sp_id}: {str(e)}")
            sp_data['appRoleAssignments'] = app_role_assignments

            # Fetch oauth2PermissionGrants (delegated permissions)
            oauth2_permission_grants = []
            try:
                response = await client.service_principals.by_service_principal_id(sp_id).oauth2_permission_grants.get()
                while response:
                    if response.value:
                        for grant in response.value:
                            oauth2_permission_grants.append({
                                'id': getattr(grant, 'id', '') or '',
                                'clientId': getattr(grant, 'client_id', '') or '',
                                'consentType': getattr(grant, 'consent_type', '') or '',
                                'principalId': getattr(grant, 'principal_id', '') or '',
                                'resourceId': getattr(grant, 'resource_id', '') or '',
                                'scope': getattr(grant, 'scope', '') or '',
                            })
                    if getattr(response, 'odata_next_link', None):
                        response = await client.service_principals.by_service_principal_id(sp_id).oauth2_permission_grants.with_url(response.odata_next_link).get()
                    else:
                        break
            except Exception as e:
                logger.warning(f"Error fetching oauth2PermissionGrants for service principal {sp_id}: {str(e)}")
            sp_data['oauth2PermissionGrants'] = oauth2_permission_grants

            return sp_data
        return None
    except Exception as e:
        logger.error(f"Error getting service principal {sp_id}: {str(e)}")
        raise

async def create_service_principal(graph_client: GraphClient, sp_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new service principal."""
    try:
        client = graph_client.get_client()
        sp = ServicePrincipal()
        # Set properties from sp_data
        if 'appId' in sp_data:
            sp.app_id = sp_data['appId']
        if 'accountEnabled' in sp_data:
            sp.account_enabled = sp_data['accountEnabled']
        if 'tags' in sp_data:
            sp.tags = sp_data['tags']
        if 'appRoleAssignmentRequired' in sp_data:
            sp.app_role_assignment_required = sp_data['appRoleAssignmentRequired']
        if 'displayName' in sp_data:
            sp.display_name = sp_data['displayName']
        new_sp = await client.service_principals.post(sp)
        if new_sp:
            return {
                'id': getattr(new_sp, 'id', '') or '',
                'appId': getattr(new_sp, 'app_id', '') or '',
                'displayName': getattr(new_sp, 'display_name', '') or '',
                'createdDateTime': new_sp.created_date_time.isoformat() if getattr(new_sp, 'created_date_time', None) else '',
                'accountEnabled': getattr(new_sp, 'account_enabled', None) if getattr(new_sp, 'account_enabled', None) is not None else False,
                'appOwnerOrganizationId': str(getattr(new_sp, 'app_owner_organization_id', '')) if getattr(new_sp, 'app_owner_organization_id', None) else '',
                'tags': getattr(new_sp, 'tags', []) or [],
            }
        raise Exception("Failed to create service principal")
    except Exception as e:
        logger.error(f"Error creating service principal: {str(e)}")
        raise

async def update_service_principal(graph_client: GraphClient, sp_id: str, sp_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing service principal."""
    try:
        client = graph_client.get_client()
        sp = ServicePrincipal()
        # Set updatable properties from sp_data
        if 'accountEnabled' in sp_data:
            sp.account_enabled = sp_data['accountEnabled']
        if 'tags' in sp_data:
            sp.tags = sp_data['tags']
        if 'appRoleAssignmentRequired' in sp_data:
            sp.app_role_assignment_required = sp_data['appRoleAssignmentRequired']
        if 'displayName' in sp_data:
            sp.display_name = sp_data['displayName']
        await client.service_principals.by_service_principal_id(sp_id).patch(sp)
        # Return the updated service principal
        return await get_service_principal_by_id(graph_client, sp_id)
    except Exception as e:
        logger.error(f"Error updating service principal {sp_id}: {str(e)}")
        raise

async def delete_service_principal(graph_client: GraphClient, sp_id: str) -> bool:
    """Delete a service principal by its object ID."""
    try:
        client = graph_client.get_client()
        await client.service_principals.by_service_principal_id(sp_id).delete()
        return True
    except Exception as e:
        logger.error(f"Error deleting service principal {sp_id}: {str(e)}")
        raise 