from fastapi import APIRouter, HTTPException, Depends, status, Header, Request
from typing import Optional
import os

from .schemas.linear import (
    CreateIssueRequest, CreateIssueResponse,
    ListIssuesRequest, ListIssuesResponse,
    ListProjectsResponse, ListUsersResponse,
    PostCommentRequest, PostCommentResponse,
    AssignIssueRequest, AssignIssueResponse,
    DeleteIssueRequest, DeleteIssueResponse,
    LinearIssue, LinearProject, LinearUser, LinearComment, LinearState, LinearTeam
)
from .client.linear_client import LinearClient

linear_router = APIRouter(prefix="/linear", tags=["Linear Integration"])


def get_linear_client(api_key: str) -> LinearClient:
    """
    Create and return a Linear client instance.
    
    Args:
        api_key (str): Linear API key
        
    Returns:
        LinearClient: Configured Linear client instance
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Linear API key is required in header"
        )
    
    try:
        return LinearClient(api_key)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize Linear client: {str(e)}"
        )


@linear_router.post("/issues", response_model=CreateIssueResponse)
async def create_issue(
    issue_request: CreateIssueRequest,
    request: Request
):
    """
    Create a new issue in Linear.
    
    Args:
        issue_request (CreateIssueRequest): Issue details including title, description, project_id, and team_id
        
    Returns:
        CreateIssueResponse: Created issue details or error information
        
    Raises:
        HTTPException: If issue creation fails
    """
    try:
        api_key = request.headers.get("api-key")
        client = get_linear_client(api_key)
        response = client.create_issue(
            title=issue_request.title,
            description=issue_request.description,
            project_id=issue_request.project_id,
            team_id=issue_request.team_id
        )
        
        if response.get("errors"):
            return CreateIssueResponse(
                success=False,
                error=str(response.get("errors"))
            )
        
        issue_data = response.get("data", {}).get("issueCreate", {})
        if issue_data.get("success"):
            issue = issue_data.get("issue", {})
            return CreateIssueResponse(
                success=True,
                issue=LinearIssue(
                    id=issue.get("id"),
                    title=issue.get("title"),
                    description=issue.get("description"),
                    state=LinearState(**issue.get("state", {})) if issue.get("state") else None,
                    project=LinearProject(**issue.get("project", {})) if issue.get("project") else None,
                    team=LinearTeam(**issue.get("team", {})) if issue.get("team") else None
                )
            )
        else:
            return CreateIssueResponse(
                success=False,
                error="Failed to create issue"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        return CreateIssueResponse(
            success=False,
            error=str(e)
        )


@linear_router.get("/issues", response_model=ListIssuesResponse)
async def list_issues(
    team_id: Optional[str] = None,
    project_id: Optional[str] = None,
    request: Request = None
):
    """
    List issues from Linear, optionally filtered by team or project.
    
    Args:
        team_id (str, optional): Filter issues by team ID
        project_id (str, optional): Filter issues by project ID
        
    Returns:
        ListIssuesResponse: List of issues or error information
        
    Raises:
        HTTPException: If listing issues fails
    """
    try:
        api_key = request.headers.get("api-key")
        client = get_linear_client(api_key)
        response = client.list_issues(
            team_id=team_id,
            project_id=project_id
        )
        
        if response.get("errors"):
            return ListIssuesResponse(
                success=False,
                error=str(response.get("errors"))
            )
        
        issues_data = response.get("data", {}).get("issues", {}).get("nodes", [])
        issues = []
        
        for issue_data in issues_data:
            issue = LinearIssue(
                id=issue_data.get("id"),
                title=issue_data.get("title"),
                description=issue_data.get("description"),
                state=LinearState(**issue_data.get("state", {})) if issue_data.get("state") else None,
                project=LinearProject(**issue_data.get("project", {})) if issue_data.get("project") else None,
                team=LinearTeam(**issue_data.get("team", {})) if issue_data.get("team") else None,
                assignee=LinearUser(**issue_data.get("assignee", {})) if issue_data.get("assignee") else None
            )
            issues.append(issue)
        
        return ListIssuesResponse(success=True, issues=issues)
        
    except HTTPException:
        raise
    except Exception as e:
        return ListIssuesResponse(
            success=False,
            error=str(e)
        )


@linear_router.get("/projects", response_model=ListProjectsResponse)
async def list_projects(
    request: Request
):
    """
    List all projects from Linear.
    
    Returns:
        ListProjectsResponse: List of projects or error information
        
    Raises:
        HTTPException: If listing projects fails
    """
    try:
        api_key = request.headers.get("api-key")
        client = get_linear_client(api_key)
        response = client.list_projects()
        
        if response.get("errors"):
            return ListProjectsResponse(
                success=False,
                error=str(response.get("errors"))
            )
        
        projects_data = response.get("data", {}).get("projects", {}).get("nodes", [])
        projects = []
        
        for project_data in projects_data:
            # Handle teams data - it's now a list of teams
            teams_data = project_data.get("teams", {}).get("nodes", [])
            teams = [LinearTeam(**team_data) for team_data in teams_data] if teams_data else None
            
            project = LinearProject(
                id=project_data.get("id"),
                name=project_data.get("name"),
                description=project_data.get("description"),
                state=project_data.get("state"),
                teams=teams
            )
            projects.append(project)
        
        return ListProjectsResponse(success=True, projects=projects)
        
    except HTTPException:
        raise
    except Exception as e:
        return ListProjectsResponse(
            success=False,
            error=str(e)
        )


@linear_router.get("/users", response_model=ListUsersResponse)
async def list_users(
    request: Request
):
    """
    List all users in the Linear workspace.
    
    Returns:
        ListUsersResponse: List of users or error information
        
    Raises:
        HTTPException: If listing users fails
    """
    try:
        api_key = request.headers.get("api-key")
        client = get_linear_client(api_key)
        response = client.list_users()
        
        if response.get("errors"):
            return ListUsersResponse(
                success=False,
                error=str(response.get("errors"))
            )
        
        users_data = response.get("data", {}).get("users", {}).get("nodes", [])
        users = []
        
        for user_data in users_data:
            user = LinearUser(
                id=user_data.get("id"),
                name=user_data.get("name"),
                email=user_data.get("email"),
                active=user_data.get("active")
            )
            users.append(user)
        
        return ListUsersResponse(success=True, users=users)
        
    except HTTPException:
        raise
    except Exception as e:
        return ListUsersResponse(
            success=False,
            error=str(e)
        )


@linear_router.post("/comments", response_model=PostCommentResponse)
async def post_comment(
    comment_request: PostCommentRequest,
    request: Request
):
    """
    Post a comment on a Linear issue.
    
    Args:
        comment_request (PostCommentRequest): Comment details including issue_id and body
        
    Returns:
        PostCommentResponse: Created comment details or error information
        
    Raises:
        HTTPException: If posting comment fails
    """
    try:
        api_key = request.headers.get("api-key")
        client = get_linear_client(api_key)
        response = client.post_comment(
            issue_id=comment_request.issue_id,
            body=comment_request.body
        )
        
        if response.get("errors"):
            return PostCommentResponse(
                success=False,
                error=str(response.get("errors"))
            )
        
        comment_data = response.get("data", {}).get("commentCreate", {})
        if comment_data.get("success"):
            comment = comment_data.get("comment", {})
            return PostCommentResponse(
                success=True,
                comment=LinearComment(
                    id=comment.get("id"),
                    body=comment.get("body"),
                    created_at=comment.get("createdAt")
                )
            )
        else:
            return PostCommentResponse(
                success=False,
                error="Failed to post comment"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        return PostCommentResponse(
            success=False,
            error=str(e)
        )


@linear_router.put("/issues/assign", response_model=AssignIssueResponse)
async def assign_issue(
    assign_request: AssignIssueRequest,
    request: Request
):
    """
    Assign an issue to a user in Linear.
    
    Args:
        assign_request (AssignIssueRequest): Assignment details including issue_id and assignee_id
        
    Returns:
        AssignIssueResponse: Assignment status and updated issue details or error information
        
    Raises:
        HTTPException: If assignment fails
    """
    try:
        api_key = request.headers.get("api-key")
        client = get_linear_client(api_key)
        response = client.assign_issue(
            issue_id=assign_request.issue_id,
            assignee_id=assign_request.assignee_id
        )
        
        if response.get("errors"):
            return AssignIssueResponse(
                success=False,
                error=str(response.get("errors"))
            )
        
        issue_data = response.get("data", {}).get("issueUpdate", {})
        if issue_data.get("success"):
            issue = issue_data.get("issue", {})
            return AssignIssueResponse(
                success=True,
                issue=LinearIssue(
                    id=issue.get("id"),
                    title=issue.get("title"),
                    assignee=LinearUser(**issue.get("assignee", {})) if issue.get("assignee") else None
                )
            )
        else:
            return AssignIssueResponse(
                success=False,
                error="Failed to assign issue"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        return AssignIssueResponse(
            success=False,
            error=str(e)
        )


@linear_router.delete("/issues/{issue_id}", response_model=DeleteIssueResponse)
async def delete_issue(
    issue_id: str,
    request: Request
):
    """
    Delete an issue from Linear.
    
    Args:
        issue_id (str): The ID of the issue to delete
        
    Returns:
        DeleteIssueResponse: Deletion status or error information
        
    Raises:
        HTTPException: If deletion fails
    """
    try:
        api_key = request.headers.get("api-key")
        client = get_linear_client(api_key)
        response = client.delete_issue(issue_id)
        
        if response.get("errors"):
            return DeleteIssueResponse(
                success=False,
                error=str(response.get("errors"))
            )
        
        delete_data = response.get("data", {}).get("issueDelete", {})
        if delete_data.get("success"):
            return DeleteIssueResponse(success=True)
        else:
            return DeleteIssueResponse(
                success=False,
                error="Failed to delete issue"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        return DeleteIssueResponse(
            success=False,
            error=str(e)
        )
