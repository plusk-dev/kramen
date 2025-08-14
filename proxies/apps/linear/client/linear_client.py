import requests
import json
from typing import Optional, Dict, List, Any

class LinearClient:
    """
    A client for interacting with the Linear API.
    Provides methods for managing issues, projects, users, and comments.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the Linear client.
        
        Args:
            api_key (str): Your Linear API key
        """
        self.api_key = api_key
        self.base_url = "https://api.linear.app/graphql"
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }
    
    def _make_request(self, query: str) -> Dict[str, Any]:
        """
        Make a GraphQL request to Linear API.
        
        Args:
            query (str): The GraphQL query/mutation
            
        Returns:
            Dict[str, Any]: The JSON response from the API
        """
        response = requests.post(
            self.base_url,
            json={"query": query},
            headers=self.headers
        )
        return response.json()
    
    def create_issue(
        self,
        title: str,
        description: str = "",
        project_id: str = "",
        team_id: str = ""
    ) -> Dict[str, Any]:
        """
        Create a new issue in Linear.
        
        Args:
            title (str): The title of the issue
            description (str, optional): Description of the issue
            project_id (str, optional): ID of the project to create the issue in
            team_id (str, optional): ID of the team to create the issue in
            
        Returns:
            Dict[str, Any]: Response containing the created issue details
        """
        mutation = """
        mutation IssueCreate {
            issueCreate(
                input: {
                    title: "%s"
                    description: \"\"\"%s\"\"\"
                    projectId: "%s"
                    teamId: "%s"
                }
            ) {
                success
                issue {
                    id
                    title
                    description
                    state {
                        id
                        name
                    }
                    project {
                        id
                        name
                    }
                    team {
                        id
                        name
                    }
                }
            }
        }
        """ % (title, description, project_id, team_id)
        
        return self._make_request(mutation)
    
    def list_issues(
        self,
        team_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List issues from Linear, optionally filtered by team or project.
        
        Args:
            team_id (str, optional): Filter issues by team ID
            project_id (str, optional): Filter issues by project ID
            
        Returns:
            Dict[str, Any]: Response containing list of issues
        """
        filter_conditions = []
        if team_id:
            filter_conditions.append(f'team: {{ id: {{ eq: "{team_id}" }} }}')
        if project_id:
            filter_conditions.append(f'project: {{ id: {{ eq: "{project_id}" }} }}')
        
        filter_string = ", ".join(filter_conditions)
        filter_clause = f"filter: {{ {filter_string} }}" if filter_conditions else ""
        
        # Only include parentheses if there are filter conditions
        issues_args = f"({filter_clause})" if filter_conditions else ""
        
        query = f"""
        query {{
            issues{issues_args} {{
                nodes {{
                    id
                    title
                    description
                    state {{
                        id
                        name
                    }}
                    project {{
                        id
                        name
                    }}
                    team {{
                        id
                        name
                    }}
                    assignee {{
                        id
                        name
                        email
                    }}
                }}
            }}
        }}
        """
        
        return self._make_request(query)
    
    def list_projects(self) -> Dict[str, Any]:
        """
        List all projects from Linear.
        
        Returns:
            Dict[str, Any]: Response containing list of projects
        """
        query = """
        query {
            projects {
                nodes {
                    id
                    name
                    description
                    state
                    teams {
                        nodes {
                            id
                            name
                        }
                    }
                }
            }
        }
        """
        
        return self._make_request(query)
    
    def list_users(self) -> Dict[str, Any]:
        """
        List all users in the Linear workspace.
        
        Returns:
            Dict[str, Any]: Response containing list of users
        """
        query = """
        query {
            users {
                nodes {
                    id
                    name
                    email
                    active
                }
            }
        }
        """
        
        return self._make_request(query)
    
    def post_comment(self, issue_id: str, body: str) -> Dict[str, Any]:
        """
        Post a comment on a Linear issue.
        
        Args:
            issue_id (str): The ID of the issue to comment on
            body (str): The comment text
            
        Returns:
            Dict[str, Any]: Response containing the created comment details
        """
        mutation = """
        mutation CommentCreate {
            commentCreate(
                input: {
                    issueId: "%s"
                    body: "%s"
                }
            ) {
                success
                comment {
                    id
                    body
                    createdAt
                }
            }
        }
        """ % (issue_id, body.replace('"', '\\"'))
        
        return self._make_request(mutation)
    
    def assign_issue(self, issue_id: str, assignee_id: str) -> Dict[str, Any]:
        """
        Assign an issue to a user in Linear.
        
        Args:
            issue_id (str): The ID of the issue to assign
            assignee_id (str): The ID of the user to assign the issue to
            
        Returns:
            Dict[str, Any]: Response containing the assignment status
        """
        mutation = """
        mutation IssueUpdate {
            issueUpdate(
                id: "%s"
                input: {
                    assigneeId: "%s"
                }
            ) {
                success
                issue {
                    id
                    title
                    assignee {
                        id
                        name
                        email
                    }
                }
            }
        }
        """ % (issue_id, assignee_id)
        
        return self._make_request(mutation)
    
    def delete_issue(self, issue_id: str) -> Dict[str, Any]:
        """
        Delete an issue from Linear.
        
        Args:
            issue_id (str): The ID of the issue to delete
            
        Returns:
            Dict[str, Any]: Response containing the deletion status
        """
        mutation = """
        mutation IssueDelete {
            issueDelete(
                id: "%s"
            ) {
                success
            }
        }
        """ % issue_id
        
        return self._make_request(mutation)

# Example usage:
# if __name__ == "__main__":
#     # Initialize the client
#     client = LinearClient("lin_api_lGk8nPTgeMaK83g1VeOSsqrr6CBCZsHbpVVn1rLj")
    
#     # Create an issue
#     issue = client.create_issue(
#         title="Test Issue",
#         description="This is a test issue",
#         team_id="628ef95b-417b-4007-b128-3669a6e67df5",
#         project_id="2f42fa4f-ea31-4ab2-98b6-207da9cba727"
#     )
#     print("Created issue:", issue)