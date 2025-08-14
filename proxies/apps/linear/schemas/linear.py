from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# Request Models
class CreateIssueRequest(BaseModel):
    title: str = Field(..., description="The title of the issue", min_length=1)
    description: Optional[str] = Field("", description="Description of the issue")
    project_id: Optional[str] = Field("", description="ID of the project to create the issue in")
    team_id: Optional[str] = Field("", description="ID of the team to create the issue in")


class ListIssuesRequest(BaseModel):
    team_id: Optional[str] = Field(None, description="Filter issues by team ID")
    project_id: Optional[str] = Field(None, description="Filter issues by project ID")


class PostCommentRequest(BaseModel):
    issue_id: str = Field(..., description="The ID of the issue to comment on")
    body: str = Field(..., description="The comment text", min_length=1)


class AssignIssueRequest(BaseModel):
    issue_id: str = Field(..., description="The ID of the issue to assign")
    assignee_id: str = Field(..., description="The ID of the user to assign the issue to")


class DeleteIssueRequest(BaseModel):
    issue_id: str = Field(..., description="The ID of the issue to delete")


# Data Models
class LinearState(BaseModel):
    id: str = Field(..., description="Unique identifier for the issue state")
    name: str = Field(..., description="Name of the issue state (e.g., 'Todo', 'In Progress', 'Done')")


class LinearProject(BaseModel):
    id: str = Field(..., description="Unique identifier for the project")
    name: str = Field(..., description="Name of the project")
    description: Optional[str] = Field(None, description="Description of the project")
    state: Optional[str] = Field(None, description="Current state of the project")
    teams: Optional[List['LinearTeam']] = Field(None, description="Teams associated with the project")


class LinearTeam(BaseModel):
    id: str = Field(..., description="Unique identifier for the team")
    name: str = Field(..., description="Name of the team")


class LinearUser(BaseModel):
    id: str = Field(..., description="Unique identifier for the user")
    name: str = Field(..., description="Full name of the user")
    email: str = Field(..., description="Email address of the user")
    active: Optional[bool] = Field(None, description="Whether the user is active in the workspace")


class LinearIssue(BaseModel):
    id: str = Field(..., description="Unique identifier for the issue")
    title: str = Field(..., description="Title of the issue")
    description: Optional[str] = Field(None, description="Description of the issue")
    state: Optional[LinearState] = Field(None, description="Current state of the issue")
    project: Optional[LinearProject] = Field(None, description="Project the issue belongs to")
    team: Optional[LinearTeam] = Field(None, description="Team the issue belongs to")
    assignee: Optional[LinearUser] = Field(None, description="User assigned to the issue")


class LinearComment(BaseModel):
    id: str = Field(..., description="Unique identifier for the comment")
    body: str = Field(..., description="Content of the comment")
    created_at: Optional[datetime] = Field(None, description="Timestamp when the comment was created")


# API Response Models
class CreateIssueResponse(BaseModel):
    success: bool = Field(..., description="Whether the issue creation was successful")
    issue: Optional[LinearIssue] = Field(None, description="Details of the created issue (if successful)")
    error: Optional[str] = Field(None, description="Error message if the operation failed")


class ListIssuesResponse(BaseModel):
    success: bool = Field(..., description="Whether the issue listing was successful")
    issues: List[LinearIssue] = Field(default_factory=list, description="List of issues retrieved from Linear")
    error: Optional[str] = Field(None, description="Error message if the operation failed")


class ListProjectsResponse(BaseModel):
    success: bool = Field(..., description="Whether the project listing was successful")
    projects: List[LinearProject] = Field(default_factory=list, description="List of projects retrieved from Linear")
    error: Optional[str] = Field(None, description="Error message if the operation failed")


class ListUsersResponse(BaseModel):
    success: bool = Field(..., description="Whether the user listing was successful")
    users: List[LinearUser] = Field(default_factory=list, description="List of users in the Linear workspace")
    error: Optional[str] = Field(None, description="Error message if the operation failed")


class PostCommentResponse(BaseModel):
    success: bool = Field(..., description="Whether the comment posting was successful")
    comment: Optional[LinearComment] = Field(None, description="Details of the created comment (if successful)")
    error: Optional[str] = Field(None, description="Error message if the operation failed")


class AssignIssueResponse(BaseModel):
    success: bool = Field(..., description="Whether the issue assignment was successful")
    issue: Optional[LinearIssue] = Field(None, description="Updated issue details with assignment (if successful)")
    error: Optional[str] = Field(None, description="Error message if the operation failed")


class DeleteIssueResponse(BaseModel):
    success: bool = Field(..., description="Whether the issue deletion was successful")
    error: Optional[str] = Field(None, description="Error message if the operation failed")


class LinearAuthResponse(BaseModel):
    success: bool = Field(..., description="Whether the authentication was successful")
    message: str = Field(..., description="Authentication result message")
    error: Optional[str] = Field(None, description="Error message if authentication failed")


# Update forward references
LinearProject.model_rebuild()
LinearTeam.model_rebuild() 