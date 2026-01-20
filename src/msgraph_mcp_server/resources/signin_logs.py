"""Sign-in logs resource module for Microsoft Graph.

This module provides access to Microsoft Graph sign-in logs.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone

from msgraph.generated.audit_logs.sign_ins.sign_ins_request_builder import SignInsRequestBuilder
from kiota_abstractions.base_request_configuration import RequestConfiguration

from utils.graph_client import GraphClient

logger = logging.getLogger(__name__)

async def get_user_sign_in_logs(graph_client: GraphClient, user_id: str, days: int = 7) -> List[Dict[str, Any]]:
    """Get sign-in logs for a specific user within the last N days.
    
    Args:
        graph_client: GraphClient instance
        user_id: The unique identifier of the user.
        days: The number of past days to retrieve logs for (default: 7).
        
    Returns:
        A list of dictionaries, each representing a sign-in log event.
    """
    try:
        client = graph_client.get_client()
        
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        # Format dates for query using the exact format from documentation
        start_date_str = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_date_str = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Define the OData filter query with proper formatting
        filter_query = f"createdDateTime ge {start_date_str} and createdDateTime le {end_date_str} and userId eq '{user_id}'"
        
        logger.info(f"Fetching sign-in logs for user ID: {user_id}")
        logger.info(f"Date range: {start_date_str} to {end_date_str}")
        logger.info(f"Filter query: {filter_query}")
        
        # Set up query parameters using SignInsRequestBuilder
        query_params = SignInsRequestBuilder.SignInsRequestBuilderGetQueryParameters(
            filter=filter_query,
            orderby=['createdDateTime desc'],
            top=1000  # Increased from default to get more logs
        )
        
        # Create request configuration
        request_configuration = RequestConfiguration(
            query_parameters=query_params
        )
        request_configuration.headers.add("ConsistencyLevel", "eventual")
        
        # Execute the request
        sign_ins = await client.audit_logs.sign_ins.get(request_configuration=request_configuration)

        formatted_logs = []
        if sign_ins and sign_ins.value:
            logger.info(f"Found {len(sign_ins.value)} sign-in records")
            
            for log in sign_ins.value:
                # Format each log entry with comprehensive fields
                log_data = {
                    "id": log.id or '',
                    "createdDateTime": log.created_date_time.isoformat() if log.created_date_time else '',
                    "userId": log.user_id or '',
                    "userDisplayName": log.user_display_name or '',
                    "userPrincipalName": log.user_principal_name or '',
                    "appDisplayName": log.app_display_name or '',
                    "appId": log.app_id or '',
                    "ipAddress": log.ip_address or '',
                    "clientAppUsed": log.client_app_used or '',
                    "correlationId": log.correlation_id or '',
                    "isInteractive": log.is_interactive if log.is_interactive is not None else False,
                    "resourceDisplayName": log.resource_display_name or '',
                    "status": {
                        "errorCode": log.status.error_code if log.status and log.status.error_code is not None else 0,
                        "failureReason": log.status.failure_reason if log.status else '',
                        "additionalDetails": log.status.additional_details if log.status else ''
                    },
                    "riskInformation": {
                        "riskDetail": str(log.risk_detail) if log.risk_detail else '',
                        "riskLevelAggregated": str(log.risk_level_aggregated) if log.risk_level_aggregated else '',
                        "riskLevelDuringSignIn": str(log.risk_level_during_sign_in) if log.risk_level_during_sign_in else '',
                        "riskState": str(log.risk_state) if log.risk_state else '',
                        "riskEventTypes": log.risk_event_types_v2 if hasattr(log, 'risk_event_types_v2') and log.risk_event_types_v2 else []
                    }
                }
                
                # Add device details if available
                if hasattr(log, 'device_detail') and log.device_detail:
                    device = log.device_detail
                    log_data["deviceDetail"] = {
                        "deviceId": device.device_id or '',
                        "displayName": device.display_name or '',
                        "operatingSystem": device.operating_system or '',
                        "browser": device.browser or '',
                        "isCompliant": device.is_compliant if device.is_compliant is not None else False,
                        "isManaged": device.is_managed if device.is_managed is not None else False,
                        "trustType": device.trust_type or ''
                    }
                
                # Add location if available
                if hasattr(log, 'location') and log.location:
                    location = log.location
                    log_data["location"] = {
                        "city": location.city or '',
                        "state": location.state or '',
                        "countryOrRegion": location.country_or_region or '',
                        "coordinates": {}
                    }

                    # Add coordinates if available
                    if hasattr(location, 'geo_coordinates') and location.geo_coordinates:
                        log_data["location"]["coordinates"] = {
                            "latitude": location.geo_coordinates.latitude if location.geo_coordinates.latitude is not None else 0.0,
                            "longitude": location.geo_coordinates.longitude if location.geo_coordinates.longitude is not None else 0.0
                        }
                
                formatted_logs.append(log_data)
        else:
            logger.info(f"No sign-in logs found for user {user_id} in the last {days} days.")
            
        return formatted_logs
        
    except Exception as e:
        logger.error(f"Error fetching sign-in logs for user {user_id}: {str(e)}")
        # Check for permission errors specifically
        if "Authorization_RequestDenied" in str(e):
             logger.error("Permission denied. Ensure the application has AuditLog.Read.All permission.")
        raise 