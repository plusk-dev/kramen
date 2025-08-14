# Integration Manuals

This directory contains platform-specific manuals for each integration. These manuals provide guidance on how to handle queries for specific platforms and are used by the `/deep` endpoint to improve query processing.

## Structure

Each manual is named using the integration's UUID and contains markdown-formatted guidance specific to that platform.

## Current Manuals

- `e2ce7f23-804e-45de-bd21-6b94ab238025.md` - Stripe Integration Manual
- `fdd76ee5-1f50-4337-8c2e-d686fa07dc99.md` - Linear Integration Manual

## Manual Content

Each manual includes:

1. **Platform Overview** - General description of the platform
2. **Key Concepts** - Important terms and concepts specific to the platform
3. **Query Processing Guidelines** - Platform-specific rules for handling different types of queries
4. **Common Workflows** - Step-by-step processes for typical operations
5. **Error Handling** - Platform-specific error handling guidelines
6. **Best Practices** - Recommended approaches for the platform

## Usage

The manuals are automatically loaded by the `/deep` endpoint when processing queries. The manual content is included in the context provided to the data extraction agents, helping them understand platform-specific requirements and workflows.

## Adding New Manuals

To add a manual for a new integration:

1. Create a new markdown file named with the integration's UUID (e.g., `integration-uuid.md`)
2. Follow the structure outlined above
3. Include platform-specific guidance that will help the AI understand how to process queries for that platform
4. Focus on workflows, best practices, and common patterns for the platform

## Example

For a payment platform, the manual might include guidance like:
- "If the query mentions a user, your first step should be getting the user ID"
- "For payment operations, always verify the payment method first"
- "Handle currency conversions using the platform's built-in features"

This helps the AI understand the proper sequence of operations and platform-specific requirements. 