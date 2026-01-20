import logging
from typing import Dict, List, Any, Optional
from kiota_abstractions.base_request_configuration import RequestConfiguration
from utils.graph_client import GraphClient

logger = logging.getLogger(__name__)

# Microsoft Graph application ID - this is the constant ID for the Microsoft Graph service principal
MS_GRAPH_APP_ID = "00000003-0000-0000-c000-000000000000"

# Common permission mappings - mapping of common tasks to their required permissions
# Format: {
#   "task_category": {
#     "task_name": {
#       "delegated": ["Permission1", "Permission2"],
#       "application": ["Permission1", "Permission2"],
#       "description": "Description of the task"
#     }
#   }
# }
COMMON_PERMISSION_MAPPINGS = {
    "users": {
        "read_user_profile": {
            "delegated": ["User.Read", "User.ReadBasic.All"],
            "application": ["User.Read.All"],
            "description": "Read user profile information"
        },
        "update_user_profile": {
            "delegated": ["User.ReadWrite", "User.ReadWrite.All"],
            "application": ["User.ReadWrite.All"],
            "description": "Update user profile information"
        },
        "read_all_users": {
            "delegated": ["User.ReadBasic.All", "User.Read.All"],
            "application": ["User.Read.All"],
            "description": "Read all users' profiles in the organization"
        },
        "reset_user_password": {
            "delegated": ["User.ReadWrite.All"],
            "application": ["User.ReadWrite.All", "Directory.ReadWrite.All"],
            "description": "Reset a user's password"
        }
    },
    "groups": {
        "read_user_groups": {
            "delegated": ["GroupMember.Read.All"],
            "application": ["GroupMember.Read.All", "Directory.Read.All"],
            "description": "Read groups a user is a member of"
        },
        "read_all_groups": {
            "delegated": ["Group.Read.All"],
            "application": ["Group.Read.All"],
            "description": "Read all groups in the organization"
        },
        "manage_groups": {
            "delegated": ["Group.ReadWrite.All"],
            "application": ["Group.ReadWrite.All"],
            "description": "Create, update, and delete groups, and add/remove members"
        }
    },
    "mail": {
        "read_user_mail": {
            "delegated": ["Mail.Read"],
            "application": ["Mail.Read"],
            "description": "Read user's mail"
        },
        "send_mail": {
            "delegated": ["Mail.Send"],
            "application": ["Mail.Send"],
            "description": "Send mail as the user"
        }
    },
    "calendar": {
        "read_user_calendar": {
            "delegated": ["Calendars.Read"],
            "application": ["Calendars.Read"],
            "description": "Read user's calendar"
        },
        "edit_user_calendar": {
            "delegated": ["Calendars.ReadWrite"],
            "application": ["Calendars.ReadWrite"],
            "description": "Read and write to user's calendar"
        }
    },
    "files": {
        "read_user_files": {
            "delegated": ["Files.Read", "Files.Read.All"],
            "application": ["Files.Read.All"],
            "description": "Read user's files"
        },
        "edit_user_files": {
            "delegated": ["Files.ReadWrite", "Files.ReadWrite.All"],
            "application": ["Files.ReadWrite.All"],
            "description": "Read and write to user's files"
        }
    },
    "devices": {
        "read_devices": {
            "delegated": ["Device.Read"],
            "application": ["Device.Read.All"],
            "description": "Read device information"
        },
        "manage_devices": {
            "delegated": ["Device.ReadWrite.All"],
            "application": ["Device.ReadWrite.All"],
            "description": "Manage device configuration"
        }
    },
    "audit_logs": {
        "read_audit_logs": {
            "delegated": ["AuditLog.Read.All"],
            "application": ["AuditLog.Read.All"],
            "description": "Read audit logs"
        },
        "read_sign_in_logs": {
            "delegated": ["AuditLog.Read.All"],
            "application": ["AuditLog.Read.All"],
            "description": "Read sign-in activity logs"
        }
    },
    "directory": {
        "read_directory": {
            "delegated": ["Directory.Read.All"],
            "application": ["Directory.Read.All"],
            "description": "Read directory data (users, groups, apps, etc.)"
        },
        "write_directory": {
            "delegated": ["Directory.ReadWrite.All"],
            "application": ["Directory.ReadWrite.All"],
            "description": "Read and write directory data (users, groups, apps, etc.)"
        }
    }
}

async def suggest_permissions_for_task(task_category: str, task_name: str) -> Dict[str, Any]:
    """Suggest permissions for a specific task based on common mappings.
    
    Args:
        task_category: The category of the task (users, groups, mail, etc.)
        task_name: The specific task name
        
    Returns:
        A dictionary with suggested delegated and application permissions
    """
    try:
        if task_category not in COMMON_PERMISSION_MAPPINGS:
            return {
                "status": "error",
                "message": f"Unknown task category: {task_category}",
                "available_categories": list(COMMON_PERMISSION_MAPPINGS.keys())
            }
            
        if task_name not in COMMON_PERMISSION_MAPPINGS[task_category]:
            return {
                "status": "error",
                "message": f"Unknown task name: {task_name}",
                "available_tasks": list(COMMON_PERMISSION_MAPPINGS[task_category].keys())
            }
            
        task_info = COMMON_PERMISSION_MAPPINGS[task_category][task_name]
        
        return {
            "status": "success",
            "task_category": task_category,
            "task_name": task_name,
            "description": task_info["description"],
            "delegated_permissions": task_info["delegated"],
            "application_permissions": task_info["application"],
            "notes": "These are suggested permissions based on common usage patterns. Always follow the principle of least privilege."
        }
    except Exception as e:
        logger.error(f"Error suggesting permissions for task {task_category}/{task_name}: {str(e)}")
        raise

async def list_available_categories_and_tasks() -> Dict[str, Any]:
    """List all available categories and tasks for permission suggestions.
    
    Returns:
        A dictionary with all available categories and their tasks
    """
    try:
        result = {
            "status": "success",
            "categories": {}
        }
        
        for category, tasks in COMMON_PERMISSION_MAPPINGS.items():
            result["categories"][category] = {
                "tasks": []
            }
            
            for task_name, task_info in tasks.items():
                result["categories"][category]["tasks"].append({
                    "name": task_name,
                    "description": task_info["description"]
                })
                
        return result
    except Exception as e:
        logger.error(f"Error listing available categories and tasks: {str(e)}")
        raise

async def get_all_graph_permissions(graph_client: GraphClient) -> Dict[str, Any]:
    """Get all Microsoft Graph permissions directly from the Microsoft Graph API.
    
    Args:
        graph_client: GraphClient instance
        
    Returns:
        A dictionary with all delegated and application permissions
    """
    try:
        client = graph_client.get_client()
        
        # Get the Microsoft Graph service principal
        query_params = {
            "$select": "id,appId,displayName,appRoles,oauth2PermissionScopes"
        }
        
        ms_graph_sp = await client.service_principals.by_service_principal_id(MS_GRAPH_APP_ID).get()
        
        if not ms_graph_sp:
            logger.error("Microsoft Graph service principal not found")
            return {"status": "error", "message": "Microsoft Graph service principal not found"}
        
        # Extract delegated permissions (oauth2PermissionScopes)
        delegated_permissions = []
        if hasattr(ms_graph_sp, "oauth2_permission_scopes") and ms_graph_sp.oauth2_permission_scopes:
            for permission in ms_graph_sp.oauth2_permission_scopes:
                delegated_permissions.append({
                    "id": str(getattr(permission, "id", '')) if getattr(permission, "id", None) else '',
                    "value": getattr(permission, "value", '') or '',
                    "type": "delegated",
                    "adminConsentDisplayName": getattr(permission, "admin_consent_display_name", '') or '',
                    "adminConsentDescription": getattr(permission, "admin_consent_description", '') or '',
                    "userConsentDisplayName": getattr(permission, "user_consent_display_name", '') or '',
                    "userConsentDescription": getattr(permission, "user_consent_description", '') or '',
                    "isEnabled": getattr(permission, "is_enabled", None) if getattr(permission, "is_enabled", None) is not None else False
                })
        
        # Extract application permissions (appRoles)
        application_permissions = []
        if hasattr(ms_graph_sp, "app_roles") and ms_graph_sp.app_roles:
            for permission in ms_graph_sp.app_roles:
                application_permissions.append({
                    "id": str(getattr(permission, "id", '')) if getattr(permission, "id", None) else '',
                    "value": getattr(permission, "value", '') or '',
                    "type": "application",
                    "displayName": getattr(permission, "display_name", '') or '',
                    "description": getattr(permission, "description", '') or '',
                    "isEnabled": getattr(permission, "is_enabled", None) if getattr(permission, "is_enabled", None) is not None else False
                })
        
        return {
            "status": "success",
            "delegated_permissions": delegated_permissions,
            "application_permissions": application_permissions
        }
    except Exception as e:
        logger.error(f"Error getting Graph permissions: {str(e)}")
        raise

async def search_permissions(graph_client: GraphClient, search_term: str, permission_type: Optional[str] = None) -> Dict[str, Any]:
    """Search for Microsoft Graph permissions by keyword.
    
    Args:
        graph_client: GraphClient instance
        search_term: The keyword to search for
        permission_type: Optional filter by permission type ("delegated" or "application")
        
    Returns:
        A dictionary with matching permissions
    """
    try:
        all_permissions = await get_all_graph_permissions(graph_client)
        
        if all_permissions.get("status") != "success":
            return all_permissions
        
        delegated_permissions = all_permissions.get("delegated_permissions", [])
        application_permissions = all_permissions.get("application_permissions", [])
        
        # Convert search term to lowercase for case-insensitive matching
        search_term = search_term.lower()
        
        # Filter permissions based on search term
        matching_delegated = []
        if permission_type is None or permission_type.lower() == "delegated":
            for permission in delegated_permissions:
                # Search in value, display name, and description
                if (search_term in permission.get("value", "").lower() or
                    search_term in permission.get("adminConsentDisplayName", "").lower() or
                    search_term in permission.get("adminConsentDescription", "").lower()):
                    matching_delegated.append(permission)
        
        matching_application = []
        if permission_type is None or permission_type.lower() == "application":
            for permission in application_permissions:
                # Search in value, display name, and description
                if (search_term in permission.get("value", "").lower() or
                    search_term in permission.get("displayName", "").lower() or
                    search_term in permission.get("description", "").lower()):
                    matching_application.append(permission)
        
        return {
            "status": "success",
            "search_term": search_term,
            "matching_delegated_permissions": matching_delegated,
            "matching_application_permissions": matching_application,
            "total_matches": len(matching_delegated) + len(matching_application)
        }
    except Exception as e:
        logger.error(f"Error searching for permissions with term '{search_term}': {str(e)}")
        raise 