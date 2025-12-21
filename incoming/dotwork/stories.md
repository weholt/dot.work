# .work user stories

## Web frontend

- I want a frontend in react using tailwind css and shadcn components for a modern sleek design
- I want the frontend to support light and dark mode and theming using css and static images
- I want frontend to support different fonts, but use jetbrains nerd font mono as standard
- The frontend should have these tabs:
    - projects, crud for basic project operations
    - global personas
        - each persona can have a role, description, optional name and avatar, default documents and references selected from the global resources
    - resources where the user can add, delete, edit documents, add urls, binary files and images
    - global environment variables and settings for api keys, llm/models etc
    - when selected a project should have these tabs:
        - dashboard with overall information about the project, current status, current task etc
        - user stories where the user should be able to add user stories as different personas or create custom project-specific personas
            - when the project is created there is no personas, but the user can add from the global or create custom
            - the personas are listed in a left sidebar with an edit button and delete button (disabled if the persona has been used)
            - when clicked a dialog appear where you add a user story as the clicked persona with the ability to add a description, an optional title, tags, images, attachments, both global and project-specific documents, and set priority
            - the main content is a list of user stories that can be filtered by persona, tags, or keywords, and sorted by priority or status
            - when a user story is added an llm processes the content, adds a title if none is present, adds tags and assigns section, priority, defaults to medium 
        - resources where the user should be able to choose from the global resources or add project specific resources
        - project settings and environment variables
        - specification generated from user stories and resources by the llm
            - the generation is triggered manually by the project manager
        - tasks generated from the specification by the llm. 
            - the generation is triggered manually by the project manager
            - Each task should be editable, the list should be sortable by priority, task status and filter by type, priority, user, persona, tags etc
    - I Want to be able to export the project to markdown, including all documents, tasks, user stories etc. in a nice format
    - I want to be able to see the entire project in a web view including links to documents, specification, tasks, embedded images, user stories etc

## Identifiers

- When we talk about identifiers we want humanly usable identifiers, not guids, integers etc
- A identifier should have a random or incremental part and a text part which makes it recognizable
- Examples (where ?? is random alpha characters):
    - PR-??-002 : project
    - SP-??-001: specification
    - GR-??-023: group
    - MS-??-002: milestone 
    - TASK-??-002: task

## Project specification

- All projects should have these properties
    - title
    - description
    - optional version
    - optional github url
    - optional cookiecutter recipe
    - status: open | closed | pending | blocked | deferred | cancelled (all start pending and finish as closed or cancelled)
    - tags: comma-seperated list of words
    - section: part of the project/ui/cli/api
    - priority: critical | high | medium | low | nice-to-have
    - system-wide unique identifier
    
## Specification specification

- A specification should have these properties:
    - project properties
    - version
    - general overview, vision, goal, success criteria
    - technical overview
    - technical details, stacks, framework, ux design etc
    - link to reference material, other documents
    - all user stories processed and optimized by the llm, sorted by persona
    - prioritized milestones
        - title
        - project-wide identifier
        - description
        - links to user stories or technical details related to this milestone
    - appendix with links to references

## Task specification

- Tasks are divided into groups, each group has no more than 10-15 tasks
- Each group is connected to a milestone in the specification
- Each group has a project-wide unique identifier
- Each group should be completed before moving to the next
- Each group of tasks should end with validation using build scripts and testing, both using unittests but also validating that the implementation is according to the spec

- All tasks should have these properties:
    - title
    - type:  feature | bug | enhancement | refactoring
    - description
    - created by username
    - registration-timestamp
    - completion-timestamp
    - status: open | closed | pending | blocked | deferred | cancelled (all start pending and finish as closed or cancelled)
    - tags: comma-seperated list of words
    - section: part of the project/ui/cli/api
    - priority: critical | high | medium | low | nice-to-have
    - project-wide unique identifier
    - linked images, urls, documents
    - link to group
- The llm should define all missing properties when a task is defined

## LLM processing

- I want the documents to be searchable using semantic search (implemented later)
- I want **ALL** prompts to be customizable and not hardcoded into the source code
- I want MCP support for the agentic tools (implemented later)

## Backend API

- I want a fastapi backend 
- I want a sqlite database but support for postgres
- I want to use pydantic, pydantic ai, sqlmodel, typer, rich, python-dotenv
- I want to use uv for package management and running all python code
- I want a API key used for authentication to the API
- I want a nice cli
- I want support for multiple llm, models, providers etc using dependency injections

## Agent tools

- I want tools the agent can use while planning and implementing the project
- I want the agent to be able to fetch the current tasklist and required context to perform its tasks optimally
- I want the agent to be able to update tasks with status
- I Want the agent to be able to report bugs

## Deployment

- I want a docker-compose.yml file with all services
- I want multi-stage dockerfiles for efficient building time
- I want the frontend built for production as a static site inside docker
- I want the backend running in production mode inside docker
