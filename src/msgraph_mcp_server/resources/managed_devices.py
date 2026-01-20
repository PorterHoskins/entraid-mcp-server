import logging
from typing import Dict, List, Any, Optional
from msgraph.generated.device_management.managed_devices.managed_devices_request_builder import ManagedDevicesRequestBuilder
from kiota_abstractions.base_request_configuration import RequestConfiguration
from utils.graph_client import GraphClient

logger = logging.getLogger(__name__)

async def get_all_managed_devices(graph_client: GraphClient, filter_os: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get all managed devices (optionally filter by OS), with paging support."""
    try:
        client = graph_client.get_client()
        query_params = ManagedDevicesRequestBuilder.ManagedDevicesRequestBuilderGetQueryParameters()
        if filter_os:
            query_params.filter = f"operatingSystem eq '{filter_os}'"
        request_configuration = RequestConfiguration(query_parameters=query_params)
        request_configuration.headers.add("ConsistencyLevel", "eventual")
        response = await client.device_management.managed_devices.get(request_configuration=request_configuration)
        devices = []
        if response and response.value:
            devices.extend(response.value)
        while response is not None and getattr(response, 'odata_next_link', None):
            response = await client.device_management.managed_devices.with_url(response.odata_next_link).get(request_configuration=request_configuration)
            if response and response.value:
                devices.extend(response.value)
        formatted_devices = []
        for device in devices:
            device_data = {
                'id': getattr(device, 'id', '') or '',
                'deviceName': getattr(device, 'device_name', '') or '',
                'userId': getattr(device, 'user_id', '') or '',
                'userPrincipalName': getattr(device, 'user_principal_name', '') or '',
                'operatingSystem': getattr(device, 'operating_system', '') or '',
                'osVersion': getattr(device, 'os_version', '') or '',
                'managementAgent': getattr(device, 'management_agent', None).value if getattr(device, 'management_agent', None) else '',
                'complianceState': getattr(device, 'compliance_state', None).value if getattr(device, 'compliance_state', None) else '',
                'jailBroken': getattr(device, 'jail_broken', '') or '',
                'enrollmentType': getattr(device, 'enrollment_type', None).value if getattr(device, 'enrollment_type', None) else '',
                'lastSyncDateTime': getattr(device, 'last_sync_date_time', None).isoformat() if getattr(device, 'last_sync_date_time', None) else ''
            }
            formatted_devices.append(device_data)
        return formatted_devices
    except Exception as e:
        logger.error(f"Error fetching all managed devices: {str(e)}")
        raise

async def get_managed_devices_by_user(graph_client: GraphClient, user_id: str) -> List[Dict[str, Any]]:
    """Get all managed devices for a specific userId, with paging support."""
    try:
        client = graph_client.get_client()
        query_params = ManagedDevicesRequestBuilder.ManagedDevicesRequestBuilderGetQueryParameters(
            filter=f"userId eq '{user_id}'"
        )
        request_configuration = RequestConfiguration(query_parameters=query_params)
        request_configuration.headers.add("ConsistencyLevel", "eventual")
        response = await client.device_management.managed_devices.get(request_configuration=request_configuration)
        devices = []
        if response and response.value:
            devices.extend(response.value)
        while response is not None and getattr(response, 'odata_next_link', None):
            response = await client.device_management.managed_devices.with_url(response.odata_next_link).get(request_configuration=request_configuration)
            if response and response.value:
                devices.extend(response.value)
        formatted_devices = []
        for device in devices:
            device_data = {
                'id': getattr(device, 'id', '') or '',
                'deviceName': getattr(device, 'device_name', '') or '',
                'userId': getattr(device, 'user_id', '') or '',
                'userPrincipalName': getattr(device, 'user_principal_name', '') or '',
                'operatingSystem': getattr(device, 'operating_system', '') or '',
                'osVersion': getattr(device, 'os_version', '') or '',
                'managementAgent': getattr(device, 'management_agent', None).value if getattr(device, 'management_agent', None) else '',
                'complianceState': getattr(device, 'compliance_state', None).value if getattr(device, 'compliance_state', None) else '',
                'jailBroken': getattr(device, 'jail_broken', '') or '',
                'enrollmentType': getattr(device, 'enrollment_type', None).value if getattr(device, 'enrollment_type', None) else '',
                'lastSyncDateTime': getattr(device, 'last_sync_date_time', None).isoformat() if getattr(device, 'last_sync_date_time', None) else ''
            }
            formatted_devices.append(device_data)
        return formatted_devices
    except Exception as e:
        logger.error(f"Error fetching managed devices for user {user_id}: {str(e)}")
        raise 