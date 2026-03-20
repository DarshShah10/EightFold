"""
Interview Tab - Adaptive Virtual Interview Engine
================================================
Streamlined flow: JD → Extract Skills → Interview → Results
"""

import os
import json
import re
import streamlit as st

from virtual_interview.config import API_CONFIG


# ─── LLM Helpers ────────────────────────────────────────────────────────────────

def get_vi_llm_client():
    """Get configured LLM client."""
    from openai import OpenAI
    return OpenAI(
        api_key=API_CONFIG["api_key"],
        base_url=API_CONFIG["base_url"]
    )


def call_vi_llm(messages: list, max_tokens: int = 500, system: str = "") -> str:
    """Call LLM and return response text."""
    client = get_vi_llm_client()

    # Add system prompt if provided
    if system:
        messages = [{"role": "system", "content": system}] + messages

    response = client.chat.completions.create(
        model=API_CONFIG["model"],
        max_tokens=max_tokens,
        temperature=0.7,
        messages=messages
    )

    if hasattr(response, 'choices') and response.choices:
        return response.choices[0].message.content or str(response)
    return str(response)


def extract_vi_skills(jd_text: str):
    """Extract skills from job description with proper categorization."""
    try:
        from src import extract_skills_from_jd, extract_skills_fallback

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if api_key and "your-api-key" not in api_key:
            skills_result = extract_skills_from_jd(jd_text)
        else:
            skills_result = extract_skills_fallback(jd_text)

        # Programming languages
        coding_languages = {
            "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
            "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "sql", "html", "css"
        }

        # Tools and frameworks
        tools_frameworks = {
            "docker", "kubernetes", "aws", "azure", "gcp", "react", "angular", "vue",
            "node.js", "django", "flask", "spring", "tensorflow", "pytorch", "keras",
            "jenkins", "git", "github", "gitlab", "terraform", "ansible", "kafka",
            "redis", "mongodb", "postgresql", "mysql", "elasticsearch", "grafana", "prometheus"
        }

        skills = []
        seen = set()

        def add_skill(name):
            name_lower = name.lower()
            if name_lower in seen:
                return
            seen.add(name_lower)

            if name_lower in coding_languages:
                skills.append({"name": name, "type": "coding"})
            elif name_lower in tools_frameworks:
                skills.append({"name": name, "type": "tool"})
            else:
                skills.append({"name": name, "type": "conceptual"})

        # Process must_have (higher priority)
        for skill_name in skills_result.get("must_have", []):
            add_skill(skill_name)

        # Process nice_to_have
        for skill_name in skills_result.get("nice_to_have", []):
            add_skill(skill_name)

        # Process soft_skills
        for skill_name in skills_result.get("soft_skills", []):
            add_skill(skill_name)

        return skills if skills else [{"name": "Programming", "type": "coding"}]

    except Exception as e:
        # Fallback with basic categorization
        skills = []
        tech_keywords = {
            "python": "coding", "java": "coding", "javascript": "coding", "typescript": "coding",
            "c++": "coding", "c#": "coding", "go": "coding", "rust": "coding",
            "docker": "tool", "kubernetes": "tool", "aws": "tool", "azure": "tool",
            "react": "tool", "node": "tool", "sql": "coding", "git": "tool",
            "machine learning": "conceptual", "ml": "conceptual", "ai": "conceptual",
            "deep learning": "conceptual", "ci/cd": "tool", "devops": "conceptual",
            "agile": "conceptual", "scrum": "conceptual", "cloud": "conceptual"
        }
        for kw, kw_type in tech_keywords.items():
            if kw.lower() in jd_text.lower():
                skills.append({"name": kw.title(), "type": kw_type})
        return skills[:10] or [{"name": "Programming", "type": "coding"}]


# ─── Question Generation ─────────────────────────────────────────────────────────

# Skill-specific question templates - these are real interview questions
SKILL_QUESTIONS = {
    # Coding Languages
    "python": {
        "beginner": {
            "question": "Write a Python function called `calculate_average` that takes a list of numbers and returns their arithmetic mean. Handle the case of an empty list by returning None.",
            "input": "[10, 20, 30, 40, 50]",
            "output": "30.0",
            "constraints": "Use only built-in Python features. No external libraries.",
            "why_this": "Tests understanding of basic Python data structures and functions."
        },
        "intermediate": {
            "question": "Write a Python decorator called `log_execution_time` that measures and prints the execution time of any function it decorates. It should work with functions of any signature.",
            "input": "@log_execution_time\ndef slow_function():\n    import time\n    time.sleep(0.1)\n    return 'Done'",
            "output": "slow_function() -> 'Done' (executed in 0.101s)",
            "constraints": "Use functools.wraps to preserve function metadata.",
            "why_this": "Tests understanding of decorators and closures in Python."
        },
        "advanced": {
            "question": "Implement a thread-safe LRU (Least Recently Used) cache class in Python with O(1) get and put operations. It should have a max_size parameter.",
            "input": "cache = LRUCache(3)\ncache.put(1, 'a')\ncache.put(2, 'b')\ncache.get(1)  # returns 'a'\ncache.put(3, 'c')",
            "output": "get(1) -> 'a', cache should contain {1:'a', 2:'b', 3:'c'}",
            "constraints": "Use collections.OrderedDict or manual doubly-linked list.",
            "why_this": "Tests data structure knowledge and thread safety."
        },
        "expert": {
            "question": "Implement an async context manager in Python that handles database connections with automatic retry logic. It should retry on transient errors up to 3 times with exponential backoff.",
            "input": "async with DatabaseConnection('postgresql://...') as conn:\n    result = await conn.execute('SELECT * FROM users')",
            "output": "Connection established, query executed, connection closed properly",
            "constraints": "Use asyncio, handle connection errors gracefully.",
            "why_this": "Tests advanced async patterns and error handling in production systems."
        }
    },
    "javascript": {
        "beginner": {
            "question": "Write a JavaScript function `filterByAge` that takes an array of user objects and a minimum age, returning only users who meet the age requirement. Each user object has `name` and `age` properties.",
            "input": "[{name: 'Alice', age: 25}, {name: 'Bob', age: 17}, {name: 'Charlie', age: 30}]",
            "output": "[{name: 'Alice', age: 25}, {name: 'Charlie', age: 30}]",
            "constraints": "Use array methods like filter().",
            "why_this": "Tests array manipulation and destructuring."
        },
        "intermediate": {
            "question": "Implement a debounce function in JavaScript that delays invoking a function until after a specified wait time has elapsed since the last invocation. It should handle leading and trailing edge calls.",
            "input": "const debouncedSearch = debounce(searchAPI, 300, {leading: true, trailing: true})",
            "output": "searchAPI called appropriately based on user input timing",
            "constraints": "Return a new function that can be called multiple times but only executes once after the wait period.",
            "why_this": "Tests closure understanding and performance optimization."
        },
        "advanced": {
            "question": "Write a JavaScript function that deep clones an object, handling circular references, Date objects, and nested arrays/objects.",
            "input": "const obj = {a: 1, b: {c: [1, 2, 3]}, d: new Date(), e: {f: {}}}; obj.e.f.g = obj;",
            "output": "A complete deep clone without circular reference issues",
            "constraints": "Do not use JSON.parse(JSON.stringify()) or structuredClone() for educational purposes.",
            "why_this": "Tests understanding of JavaScript types and memory references."
        },
        "expert": {
            "question": "Implement a custom React hook called `useAsync` that manages async operations with loading, error, and data states. It should support automatic refetching when dependencies change.",
            "input": "const { data, loading, error, refetch } = useAsync(() => fetchUsers(), [dep1, dep2])",
            "output": "Proper state management with React hooks",
            "constraints": "Use useState, useEffect, and handle cleanup properly.",
            "why_this": "Tests React best practices and custom hook patterns."
        }
    },
    "java": {
        "beginner": {
            "question": "Write a Java method `findMax` that takes an int array and returns the maximum value. Handle the case of null or empty arrays by throwing IllegalArgumentException.",
            "input": "int[] arr = {5, 3, 9, 1, 7};",
            "output": "9",
            "constraints": "Do not use Collections or Arrays utility methods.",
            "why_this": "Tests Java basics and exception handling."
        },
        "intermediate": {
            "question": "Implement a generic Stack class in Java with push, pop, peek, and isEmpty methods. The stack should support any object type.",
            "input": "Stack<String> stack = new Stack<>();\nstack.push('hello');\nstack.push('world');",
            "output": "pop() returns 'world', peek() returns 'world'",
            "constraints": "Use generics properly. Implement using a linked list or array.",
            "why_this": "Tests generics and data structure implementation."
        },
        "advanced": {
            "question": "Implement a thread-safe Producer-Consumer pattern in Java using BlockingQueue. Multiple producers should add items, and multiple consumers should process them.",
            "input": "SharedQueue queue = new SharedQueue(10);\n// Producers add items\n// Consumers process items",
            "output": "Items processed in order without race conditions",
            "constraints": "Use ExecutorService for thread management.",
            "why_this": "Tests concurrent programming and thread coordination."
        },
        "expert": {
            "question": "Design and implement a simple in-memory cache with TTL (time-to-live) support in Java. Items should expire after a configurable duration.",
            "input": "Cache<String, String> cache = new TTLCache<>(60_000); // 60 seconds TTL\ncache.put('key1', 'value1');",
            "output": "After 61 seconds, get('key1') returns null",
            "constraints": "Use ScheduledExecutorService for cleanup.",
            "why_this": "Tests production-grade caching patterns."
        }
    },
    "sql": {
        "beginner": {
            "question": "Write a SQL query to find all employees who earn more than the average salary in their department. Return employee name, department, and salary.",
            "input": "employees(id, name, department_id, salary)",
            "output": "List of employees earning above their department average",
            "constraints": "Use a subquery or window function.",
            "why_this": "Tests aggregation and subquery skills."
        },
        "intermediate": {
            "question": "Write SQL to find the second-highest salary in each department. If there are ties, handle them appropriately.",
            "input": "employees(id, name, department_id, salary)",
            "output": "Employee name, department, and second-highest salary per department",
            "constraints": "Use window functions like DENSE_RANK() or RANK().",
            "why_this": "Tests window functions and ranking."
        },
        "advanced": {
            "question": "Write a SQL query to calculate the running total of sales for each day, partitioned by region. Also include the percentage change from the previous day.",
            "input": "sales(id, date, region, amount)",
            "output": "Date, region, daily_sales, running_total, percent_change",
            "constraints": "Use window functions ROW_NUMBER, SUM, LAG.",
            "why_this": "Tests complex analytics with window functions."
        },
        "expert": {
            "question": "Design a database schema for a multi-tenant SaaS application where each tenant's data must be completely isolated. Include indexes for performance and consider soft delete patterns.",
            "input": "Design tables for: Organizations, Users, Subscriptions, Billing",
            "output": "Complete CREATE TABLE statements with proper constraints",
            "constraints": "Consider row-level security or schema-per-tenant approaches.",
            "why_this": "Tests database design for scalability and security."
        }
    },
    # Tools
    "docker": {
        "beginner": {
            "question": "Write a Dockerfile for a Node.js application. The app listens on port 3000 and has dependencies defined in package.json. Optimize for production use.",
            "input": "Node.js app with: npm install, npm start",
            "output": "Complete Dockerfile with multi-stage build",
            "constraints": "Use .dockerignore. Don't run as root.",
            "why_this": "Tests Docker fundamentals and best practices."
        },
        "intermediate": {
            "question": "Explain how you would debug a container that's crashing immediately after starting. List the commands and steps you would use.",
            "input": "Container ID: abc123 is crashing",
            "output": "Step-by-step debugging process",
            "constraints": "Assume Docker is running on Linux.",
            "why_this": "Tests practical Docker troubleshooting skills."
        },
        "advanced": {
            "question": "Design a Docker Compose setup for a web application with: Node.js frontend, Python Flask API, PostgreSQL database, Redis cache, and Nginx as reverse proxy.",
            "input": "5 services needed: frontend, api, db, cache, nginx",
            "output": "docker-compose.yml with proper networking and volumes",
            "constraints": "API should wait for database. Use health checks.",
            "why_this": "Tests multi-container orchestration."
        },
        "expert": {
            "question": "How would you implement zero-downtime deployments using Docker? Explain your blue-green deployment strategy and how you handle database migrations.",
            "input": "Production environment with PostgreSQL database",
            "output": "Complete deployment strategy with rollback plan",
            "constraints": "No downtime allowed. Preserve data integrity.",
            "why_this": "Tests production deployment patterns."
        }
    },
    "kubernetes": {
        "beginner": {
            "question": "Write Kubernetes manifests for a simple web application deployment with 3 replicas, a ClusterIP service, and a ConfigMap for environment variables.",
            "input": "App needs: REACT_APP_API_URL, NODE_ENV=production",
            "output": "YAML manifests for Deployment, Service, ConfigMap",
            "constraints": "Use proper labels and selectors.",
            "why_this": "Tests basic K8s resources."
        },
        "intermediate": {
            "question": "Explain how you would handle pod resource limits and autoscaling in Kubernetes. Design an HPA (Horizontal Pod Autoscaler) configuration for a CPU-intensive application.",
            "input": "Deployment with 2-10 replicas, target CPU at 70%",
            "output": "HPA configuration with resource requests and limits",
            "constraints": "Consider memory limits as well.",
            "why_this": "Tests scaling and resource management."
        },
        "advanced": {
            "question": "Design a Kubernetes ingress configuration with TLS termination, path-based routing to multiple services, and rate limiting.",
            "input": "Services: api.example.com (API), app.example.com (Frontend)",
            "output": "Ingress manifest with annotations for rate limiting",
            "constraints": "Use cert-manager for certificate management.",
            "why_this": "Tests ingress and security configuration."
        },
        "expert": {
            "question": "How would you implement a canary deployment strategy in Kubernetes? Include traffic splitting, metrics monitoring, and automated rollback.",
            "input": "Deploy new version of API service to 5% of traffic",
            "output": "Deployment strategy with Istio or Argo Rollouts",
            "constraints": "Monitor error rates and latency during rollout.",
            "why_this": "Tests advanced deployment patterns."
        }
    },
    "aws": {
        "beginner": {
            "question": "Design an S3 bucket policy that allows read-only access to a specific prefix for authenticated users, but full access only for users in the 'admin' group.",
            "input": "Bucket: company-data, Prefix: /reports, Users in 'admin' group",
            "output": "IAM policy JSON with proper resource and condition blocks",
            "constraints": "Use least privilege principle.",
            "why_this": "Tests AWS IAM and S3 security."
        },
        "intermediate": {
            "question": "Explain how you would set up a serverless API using AWS API Gateway and Lambda. Include error handling and basic authentication.",
            "input": "REST API with endpoints: GET /users, POST /users, GET /users/{id}",
            "output": "API Gateway setup with Lambda integrations",
            "constraints": "Use Cognito for authentication.",
            "why_this": "Tests serverless architecture fundamentals."
        },
        "advanced": {
            "question": "Design a highly available architecture on AWS for a web application handling 10,000 requests/second. Include load balancing, auto-scaling, multi-AZ deployment, and database failover.",
            "input": "Web application with session data, persistent data in RDS",
            "output": "Architecture diagram description with services used",
            "constraints": "99.9% uptime SLA. Handle 10x traffic spikes.",
            "why_this": "Tests cloud architecture design."
        },
        "expert": {
            "question": "How would you implement a multi-region active-active deployment on AWS? Address data replication, failover handling, and DNS management.",
            "input": "Primary: us-east-1, Secondary: eu-west-1",
            "output": "Complete multi-region strategy with replication",
            "constraints": "Minimize latency. Handle split-brain scenarios.",
            "why_this": "Tests advanced disaster recovery."
        }
    },
    # Conceptual
    "machine learning": {
        "beginner": {
            "question": "Explain the difference between supervised and unsupervised learning. Provide one example of each and explain when you would use each approach.",
            "input": "No code - conceptual question",
            "output": "Clear explanation with examples",
            "constraints": "Mention at least 3 techniques for each type.",
            "why_this": "Tests fundamental ML concepts."
        },
        "intermediate": {
            "question": "Explain the bias-variance tradeoff. How does it affect model selection? What techniques can you use to balance both?",
            "input": "No code - conceptual question",
            "output": "Explanation with mathematical intuition",
            "constraints": "Include examples of high-bias and high-variance models.",
            "why_this": "Tests ML theory understanding."
        },
        "advanced": {
            "question": "Compare and contrast gradient boosting (XGBoost, LightGBM) versus deep learning approaches for tabular data. When would you choose one over the other?",
            "input": "No code - conceptual question",
            "output": "Detailed comparison with use cases",
            "constraints": "Consider interpretability, training time, and data requirements.",
            "why_this": "Tests practical ML knowledge."
        },
        "expert": {
            "question": "Design an end-to-end ML pipeline for a fraud detection system. Address data collection, feature engineering, model training, deployment, and monitoring.",
            "input": "Real-time transaction processing, 99.9% uptime required",
            "output": "Complete pipeline architecture",
            "constraints": "Handle class imbalance. Minimize false positives.",
            "why_this": "Tests production ML systems design."
        }
    },
    "git": {
        "beginner": {
            "question": "Explain the difference between git merge and git rebase. When would you use each? Show the git commands you would use.",
            "input": "Feature branch needs to be integrated into main",
            "output": "Commands and explanation of outcomes",
            "constraints": "Mention the tradeoffs for each approach.",
            "why_this": "Tests version control fundamentals."
        },
        "intermediate": {
            "question": "How would you recover from a situation where you accidentally pushed sensitive data (like API keys) to a public repository?",
            "input": "Sensitive file was committed and pushed to main",
            "output": "Step-by-step recovery process",
            "constraints": "Assume repository has been forked by others.",
            "why_this": "Tests git emergency response."
        },
        "advanced": {
            "question": "Design a git branching strategy for a team of 10 developers working on a microservices application. Include feature flags, hotfixes, and release management.",
            "input": "10 developers, weekly releases, multiple services",
            "output": "Complete branching workflow with naming conventions",
            "constraints": "Enable parallel development without conflicts.",
            "why_this": "Tests team collaboration patterns."
        },
        "expert": {
            "question": "How would you implement a monorepo strategy using git for multiple teams? Address sparse checkout, partial cloning, and access control at the file level.",
            "input": "Monorepo with 50+ services, 100+ developers",
            "output": "Implementation strategy with git features",
            "constraints": "Minimize clone times. Support team-specific access.",
            "why_this": "Tests advanced git and repository management."
        }
    },
    "ci/cd": {
        "beginner": {
            "question": "Explain what CI/CD is and why it's important. Describe the typical stages in a CI pipeline.",
            "input": "No code - conceptual question",
            "output": "Clear explanation with pipeline stages",
            "constraints": "Mention at least 4 stages in a typical pipeline.",
            "why_this": "Tests DevOps fundamentals."
        },
        "intermediate": {
            "question": "Design a CI pipeline for a Node.js application that includes: linting, unit tests, integration tests, security scanning, and Docker image building.",
            "input": "GitHub Actions workflow for Node.js app",
            "output": "Complete workflow YAML with all stages",
            "constraints": "Fail fast on linting errors.",
            "why_this": "Tests CI pipeline design."
        },
        "advanced": {
            "question": "How would you implement progressive delivery (canary deployments, feature flags) in your CI/CD pipeline?",
            "input": "Kubernetes cluster with ArgoCD",
            "output": "Implementation with traffic splitting",
            "constraints": "Enable instant rollback capability.",
            "why_this": "Tests advanced deployment strategies."
        },
        "expert": {
            "question": "Design a CI/CD system that supports multiple environments (dev, staging, prod) with automatic promotion based on quality gates.",
            "input": "3 environments with different configurations",
            "output": "Complete pipeline with quality gates",
            "constraints": "Prod requires manual approval. Staging auto-promotes.",
            "why_this": "Tests enterprise DevOps architecture."
        }
    }
}


def generate_vi_question(skill_name: str, skill_type: str, diff: int, job_role: str, jd_context: str = ""):
    """Generate interview question with skill-specific templates."""

    difficulty_map = {
        1: "beginner",
        2: "intermediate",
        3: "advanced",
        4: "expert",
        5: "expert"
    }
    difficulty = difficulty_map.get(diff, "intermediate")

    # Try skill-specific question first
    skill_lower = skill_name.lower()
    if skill_lower in SKILL_QUESTIONS and difficulty in SKILL_QUESTIONS[skill_lower]:
        return {
            "question": SKILL_QUESTIONS[skill_lower][difficulty]["question"],
            "type": skill_type,
            "input": SKILL_QUESTIONS[skill_lower][difficulty].get("input", ""),
            "output": SKILL_QUESTIONS[skill_lower][difficulty].get("output", ""),
            "constraints": SKILL_QUESTIONS[skill_lower][difficulty].get("constraints", ""),
            "hints": ["Review the key concepts of " + skill_name, "Think about practical applications in " + job_role],
            "why_this": SKILL_QUESTIONS[skill_lower][difficulty].get("why_this", "")
        }

    # Use LLM for custom questions
    system_prompt = """You are an expert technical interviewer. Generate SPECIFIC, JOB-RELEVANT interview questions.
CRITICAL RULES:
1. Questions must be CONCRETE with specific scenarios, not vague descriptions
2. For coding: give actual problems with test cases (input/output)
3. For tools: ask about real scenarios you'll face on the job
4. For concepts: ask about understanding, trade-offs, or comparisons
5. ALWAYS tailor to the job role and JD context
6. NO generic questions like 'explain X' - make them situational
7. Return ONLY valid JSON, no markdown or additional text"""

    try:
        if skill_type == "coding":
            prompt = f"""Generate a {difficulty} coding interview question for a {job_role}.

JOB DESCRIPTION CONTEXT:
{jd_context[:2000] if jd_context else 'General software engineering role'}

SKILL: {skill_name}

Create ONE specific coding problem that:
1. Is a REALISTIC scenario from {job_role} work (NOT generic LeetCode)
2. Has concrete input/output examples
3. Tests practical problem-solving, not just syntax

Example GOOD questions:
- "Implement a rate limiter for an API endpoint that allows X requests per minute"
- "Write a function to parse and validate user input from a registration form"
- "Create a cache implementation for frequently accessed database queries"

Example BAD questions (avoid these):
- "Write a function to reverse a string"
- "Implement a binary search"

Return JSON:
{{
    "question": "Specific coding problem with clear requirements",
    "type": "coding",
    "input": "Example input data or scenario",
    "output": "Expected output or behavior",
    "constraints": "Specific constraints or requirements",
    "hints": ["hint1", "hint2"],
    "why_this": "Why this is relevant to {job_role} work"
}}"""

        elif skill_type == "tool":
            prompt = f"""Generate a {difficulty} interview question about {skill_name} for a {job_role}.

JOB DESCRIPTION CONTEXT:
{jd_context[:2000] if jd_context else 'General software engineering role'}

SKILL: {skill_name}

Create ONE scenario-based question that:
1. Describes a REAL situation you'd face using {skill_name} on the job
2. Asks about troubleshooting, best practices, or implementation
3. Is directly relevant to {job_role}

Example GOOD questions:
- "A container keeps crashing in production. Walk me through how you'd diagnose this."
- "How would you configure {skill_name} to handle 10x traffic increase?"
- "What happens when you run these specific commands? Explain the output."

Example BAD questions (avoid):
- "What is {skill_name}?"
- "Explain the basic features of {skill_name}"

Return JSON:
{{
    "question": "Specific scenario-based question",
    "type": "tool",
    "scenario": "The specific situation or context",
    "what_looking_for": "What a good answer should demonstrate",
    "hints": ["hint1", "hint2"],
    "why_this": "Why this matters for {job_role}"
}}"""

        else:  # conceptual
            prompt = f"""Generate a {difficulty} conceptual interview question about {skill_name} for a {job_role}.

JOB DESCRIPTION CONTEXT:
{jd_context[:2000] if jd_context else 'General software engineering role'}

SKILL: {skill_name}

Create ONE question that:
1. Tests DEEP understanding, not just definitions
2. Asks about comparisons, trade-offs, or when to use
3. Is relevant to {job_role} responsibilities

Example GOOD questions:
- "When would you choose {skill_name} over alternatives? What are the trade-offs?"
- "Compare {skill_name} approaches A vs B. When would you use each?"
- "Design a system using {skill_name}. What challenges might you face?"

Example BAD questions (avoid):
- "What is {skill_name}?"
- "List the features of {skill_name}"

Return JSON:
{{
    "question": "Deep conceptual question",
    "type": "conceptual",
    "follow_up": "Potential follow-up question",
    "what_looking_for": "What strong answer demonstrates",
    "hints": ["hint1", "hint2"],
    "why_this": "Why this matters for {job_role}"
}}"""

        text = call_vi_llm([{"role": "user", "content": prompt}], max_tokens=700, system=system_prompt)
        text = text.strip().replace("```json", "").replace("```", "").strip()

        if '{' in text:
            start = text.find('{')
            end = text.rfind('}') + 1
            if end > start:
                result = json.loads(text[start:end])
                result.setdefault("hints", ["Review practical applications of " + skill_name])
                result.setdefault("why_this", f"Tests {skill_name} for {job_role}")
                return result

    except Exception as e:
        pass

    # Fallback to generic but still specific question
    return generate_fallback_question(skill_name, skill_type, difficulty, job_role, jd_context)


def generate_fallback_question(skill_name: str, skill_type: str, difficulty: str, job_role: str, jd_context: str = ""):
    """Generate a specific fallback question when LLM fails."""

    skill_lower = skill_name.lower()

    # Coding language fallbacks
    coding_fallbacks = {
        "python": {
            "beginner": {
                "question": f"Write a Python function called `validate_email` that checks if an email address is valid using regex. Return True or False.",
                "input": "validate_email('user@example.com')",
                "output": "True",
                "constraints": "Use the re module. Handle edge cases like missing @ or domain.",
                "why_this": "Tests Python regex and string manipulation."
            },
            "intermediate": {
                "question": f"Implement a Python class `RateLimiter` that limits API calls to a specified number per minute. Use a sliding window approach.",
                "input": "limiter = RateLimiter(5, 60)\nlimiter.is_allowed()  # call multiple times",
                "output": "True for first 5 calls, False after",
                "constraints": "Use threading.Lock for thread safety.",
                "why_this": "Tests class design and concurrency in Python."
            },
            "advanced": {
                "question": f"Write a Python decorator that implements retry logic with exponential backoff for a function that may fail due to network issues.",
                "input": "@retry(max_attempts=3, backoff_factor=2)\ndef fetch_data(url):\n    # may raise NetworkError",
                "output": "Function retried with delays: 1s, 2s, 4s before raising",
                "constraints": "Handle different exception types separately.",
                "why_this": "Tests decorators, error handling, and async patterns."
            },
            "expert": {
                "question": f"Implement a generator-based solution to process a large CSV file (10GB+) without loading it entirely into memory. Calculate the average of a specific column.",
                "input": "process_large_csv('huge_file.csv', 'price_column')",
                "output": "Average value of 'price_column' without memory overflow",
                "constraints": "Use yield and streaming. Handle CSV parsing incrementally.",
                "why_this": "Tests memory efficiency and generator patterns."
            }
        },
        "javascript": {
            "beginner": {
                "question": f"Write a JavaScript function `groupByProperty` that groups an array of objects by a specified property. Return an object where keys are property values.",
                "input": "groupByProperty([{type: 'a', val: 1}, {type: 'b', val: 2}, {type: 'a', val: 3}], 'type')",
                "output": "{a: [{type:'a', val:1}, {type:'a', val:3}], b: [{type:'b', val:2}]}",
                "constraints": "Use reduce or forEach. Handle missing properties.",
                "why_this": "Tests array manipulation and object creation."
            },
            "intermediate": {
                "question": f"Implement a JavaScript promise-based function that simulates making 3 API calls concurrently, but only resolves when ALL succeed or rejects if ANY fails.",
                "input": "async function fetchAll(urls) { /* implement */ }",
                "output": "Promise.all behavior with proper error handling",
                "constraints": "Use Promise.all or Promise.allSettled appropriately.",
                "why_this": "Tests async/await and promise patterns."
            },
            "advanced": {
                "question": f"Implement a memoization function in JavaScript that caches function results based on ALL arguments passed. Handle objects and arrays as arguments.",
                "input": "const memoize = createMemoFn();\nmemoize(expensiveFn, arg1, {key: 'value'}, [1,2,3])",
                "output": "Cache hit on subsequent calls with same arguments",
                "constraints": "Serialize arguments for cache key. Limit cache size.",
                "why_this": "Tests closure, serialization, and optimization."
            },
            "expert": {
                "question": f"Design a JavaScript event emitter system with: on(), off(), once(), and emit(). Include wildcard event handling (*.click) and event namespaces.",
                "input": "emitter.on('user.*', handler)\nemitter.emit('user.login', data)",
                "output": "Wildcard handler triggered on matching events",
                "constraints": "Support multiple listeners per event. Handle memory leaks.",
                "why_this": "Tests advanced patterns and system design."
            }
        },
        "java": {
            "beginner": {
                "question": f"Write a Java method `countWords` that counts word frequencies in a String. Return a Map with each word and its count.",
                "input": "countWords(\"hello world hello\")",
                "output": "{hello=2, world=1}",
                "constraints": "Use HashMap. Handle punctuation and case insensitivity.",
                "why_this": "Tests HashMap usage and string processing."
            },
            "intermediate": {
                "question": f"Implement a Java method that reads a JSON file and deserializes it into a List of custom objects using Gson or Jackson.",
                "input": "readJsonFile(\"users.json\")",
                "output": "List<User> with all deserialized users",
                "constraints": "Handle parsing errors. Validate required fields.",
                "why_this": "Tests JSON parsing and error handling."
            },
            "advanced": {
                "question": f"Implement a Java method that uses ExecutorService to process a batch of tasks concurrently, with proper shutdown and timeout handling.",
                "input": "processBatch(tasks, 4, 30, TimeUnit.SECONDS)",
                "output": "Processed results or timeout exception",
                "constraints": "Use fixed thread pool. Handle partial completion.",
                "why_this": "Tests concurrency and resource management."
            },
            "expert": {
                "question": f"Design and implement a simple transaction management system in Java with support for rollback on failure.",
                "input": "Transaction tx = new Transaction();\ntx.execute(() -> { /* operations */ });",
                "output": "Auto-rollback on exception, commit on success",
                "constraints": "Support nested transactions. Implement undo stack.",
                "why_this": "Tests design patterns and transactional thinking."
            }
        },
        "sql": {
            "beginner": {
                "question": f"Write a SQL query to find the top 3 highest-paid employees in each department.",
                "input": "employees(id, name, department_id, salary)",
                "output": "Top 3 earners per department with salary",
                "constraints": "Use window functions or subquery.",
                "why_this": "Tests aggregation and ranking."
            },
            "intermediate": {
                "question": f"Write SQL to find all customers who have placed orders in the last 30 days but NOT in the last 7 days (dormant customers).",
                "input": "customers(id, name), orders(id, customer_id, order_date)",
                "output": "List of dormant customer names",
                "constraints": "Use LEFT JOIN or NOT IN with subquery.",
                "why_this": "Tests complex filtering logic."
            },
            "advanced": {
                "question": f"Write a SQL query to calculate month-over-month revenue growth percentage for each product category.",
                "input": "sales(id, category, amount, sale_date)",
                "output": "Category, month, revenue, growth_percentage",
                "constraints": "Use LAG() window function. Handle division by zero.",
                "why_this": "Tests analytical queries and window functions."
            },
            "expert": {
                "question": f"Design SQL schema for a multi-tenant application with row-level security. Each tenant should only see their own data.",
                "input": "Tenants: acme_corp, startup_inc. Shared tables: users, orders, products",
                "output": "CREATE TABLE statements with RLS policies",
                "constraints": "Use tenant_id column with proper indexing.",
                "why_this": "Tests security patterns and schema design."
            }
        }
    }

    # Tool-specific fallbacks
    tool_fallbacks = {
        "docker": {
            "beginner": {
                "question": f"Write a Dockerfile for a simple Python Flask application. The app listens on port 5000 and uses requirements.txt for dependencies.",
                "input": "Flask app with pip install -r requirements.txt",
                "output": "Complete Dockerfile with proper layer caching",
                "constraints": "Use multi-stage build if possible.",
                "why_this": "Tests Dockerfile fundamentals."
            },
            "intermediate": {
                "question": f"Debug this scenario: Your Docker container runs fine locally but fails in production with 'No such file or directory'. Walk me through diagnosing it.",
                "input": "Error occurs when running: docker run myapp",
                "output": "Step-by-step diagnosis process",
                "constraints": "Consider file permissions, line endings, path issues.",
                "why_this": "Tests Docker troubleshooting skills."
            },
            "advanced": {
                "question": f"Write a docker-compose.yml for a Python FastAPI application with PostgreSQL database, Redis cache, and automatic health checks.",
                "input": "3 services: api, db, cache. API needs to wait for db.",
                "output": "Complete docker-compose with health checks",
                "constraints": "Use depends_on with condition: service_healthy.",
                "why_this": "Tests multi-container orchestration."
            },
            "expert": {
                "question": f"Explain how you would implement zero-downtime deployments using Docker. Include blue-green deployment and database migration strategies.",
                "input": "Production app with PostgreSQL database",
                "output": "Deployment strategy with rollback plan",
                "constraints": "No downtime. Preserve data integrity.",
                "why_this": "Tests production deployment patterns."
            }
        },
        "kubernetes": {
            "beginner": {
                "question": f"Write Kubernetes manifests for a web application: Deployment with 3 replicas, a ClusterIP Service, and a ConfigMap with environment variables.",
                "input": "App needs: API_URL, DEBUG=false, LOG_LEVEL=info",
                "output": "YAML for Deployment, Service, ConfigMap",
                "constraints": "Use proper labels and selectors.",
                "why_this": "Tests basic Kubernetes resources."
            },
            "intermediate": {
                "question": f"Your Kubernetes pod is in CrashLoopBackOff state. What steps would you take to diagnose the issue?",
                "input": "kubectl get pods shows: myapp-xxx CrashLoopBackOff",
                "output": "Diagnosis steps and kubectl commands",
                "constraints": "Check logs, events, and resource limits.",
                "why_this": "Tests troubleshooting skills."
            },
            "advanced": {
                "question": f"Configure Horizontal Pod Autoscaler (HPA) for a CPU-intensive API service. Target 70% CPU utilization with 2-8 replicas.",
                "input": "Deployment with resource requests and limits defined",
                "output": "HPA manifest with proper scaling parameters",
                "constraints": "Set appropriate resource requests.",
                "why_this": "Tests autoscaling configuration."
            },
            "expert": {
                "question": f"Design a canary deployment strategy for a critical API service using Kubernetes. Include traffic splitting and automated rollback based on error rates.",
                "input": "New version v2 needs to be rolled out to 10% of traffic",
                "output": "Implementation with Argo Rollouts or Istio",
                "constraints": "Monitor error rates. Enable instant rollback.",
                "why_this": "Tests advanced deployment patterns."
            }
        },
        "aws": {
            "beginner": {
                "question": f"Create an S3 bucket policy that allows read access to authenticated users but denies access to specific IP addresses (172.16.0.0/12).",
                "input": "Bucket: company-data, Block IP range: 172.16.0.0/12",
                "output": "S3 bucket policy JSON",
                "constraints": "Use aws:SourceIp condition.",
                "why_this": "Tests IAM and S3 security."
            },
            "intermediate": {
                "question": f"Design a Lambda function that processes uploaded images: resize them, create thumbnails, and store metadata in DynamoDB.",
                "input": "Image uploaded to S3 bucket 'uploads/'",
                "output": "Thumbnail in 'thumbnails/' and metadata in DynamoDB",
                "constraints": "Use AWS SDK. Handle different image formats.",
                "why_this": "Tests serverless architecture."
            },
            "advanced": {
                "question": f"Set up an AWS Auto Scaling Group for EC2 instances behind an Application Load Balancer. Include scaling policies based on CPU and memory.",
                "input": "Need: min 2, max 10 instances, scale on CPU > 70%",
                "output": "ASG configuration with scaling policies",
                "constraints": "Use launch template. Configure health checks.",
                "why_this": "Tests AWS infrastructure design."
            },
            "expert": {
                "question": f"Design a multi-region active-active architecture on AWS with Route 53 failover. Address data replication and latency optimization.",
                "input": "Primary: us-east-1, Secondary: eu-west-1, RPO: 1 minute",
                "output": "Architecture with replication and failover",
                "constraints": "Minimize latency. Handle split-brain scenarios.",
                "why_this": "Tests disaster recovery design."
            }
        },
        "git": {
            "beginner": {
                "question": f"Explain the difference between git merge and git rebase. When would you use each? Show the git commands for a feature branch integration.",
                "input": "Feature branch needs to be merged into main",
                "output": "Commands and outcomes for both approaches",
                "constraints": "Mention tradeoffs and potential issues.",
                "why_this": "Tests version control fundamentals."
            },
            "intermediate": {
                "question": f"You accidentally committed sensitive data (API keys) to git and pushed to the remote. How do you fix this?",
                "input": "Sensitive file was committed and pushed",
                "output": "Step-by-step recovery process",
                "constraints": "Assume others may have pulled.",
                "why_this": "Tests emergency response skills."
            },
            "advanced": {
                "question": f"Design a git workflow for a team of 8 developers working on a microservices architecture. Each service has its own repository but shared libraries.",
                "input": "8 developers, 12 microservices, shared libs team",
                "output": "Complete workflow with branching strategy",
                "constraints": "Enable parallel work. Manage dependencies.",
                "why_this": "Tests team collaboration patterns."
            },
            "expert": {
                "question": f"How would you implement a monorepo strategy for 50+ repositories using git? Address sparse checkout and CI optimization.",
                "input": "Monorepo with 50+ services, 100+ developers",
                "output": "Implementation with git features and tooling",
                "constraints": "Minimize clone times. Optimize CI pipelines.",
                "why_this": "Tests advanced git management."
            }
        }
    }

    # Conceptual fallbacks
    conceptual_fallbacks = {
        "machine learning": {
            "beginner": {
                "question": f"Explain the difference between supervised and unsupervised learning. Give one concrete example of each from real-world applications.",
                "input": "No code - conceptual",
                "output": "Clear explanation with examples",
                "constraints": "Mention specific algorithms.",
                "why_this": "Tests ML fundamentals."
            },
            "intermediate": {
                "question": f"Explain overfitting and underfitting. How would you detect and fix each? Use {job_role} context.",
                "input": "No code - conceptual",
                "output": "Explanation with detection and solutions",
                "constraints": "Mention cross-validation and regularization.",
                "why_this": "Tests ML model evaluation."
            },
            "advanced": {
                "question": f"Compare XGBoost vs neural networks for tabular data prediction. When would you choose one over the other?",
                "input": "No code - conceptual",
                "output": "Detailed comparison with trade-offs",
                "constraints": "Consider interpretability and training time.",
                "why_this": "Tests practical ML knowledge."
            },
            "expert": {
                "question": f"Design an end-to-end ML pipeline for churn prediction. Address data collection, feature engineering, model training, deployment, and monitoring.",
                "input": "SaaS application with user behavior data",
                "output": "Complete pipeline architecture",
                "constraints": "Handle class imbalance. Enable retraining.",
                "why_this": "Tests production ML systems."
            }
        },
        "agile": {
            "beginner": {
                "question": f"Explain the difference between Scrum and Kanban. When would you choose one over the other for a {job_role} team?",
                "input": "No code - conceptual",
                "output": "Comparison with use cases",
                "constraints": "Mention ceremonies and artifacts.",
                "why_this": "Tests agile methodology knowledge."
            },
            "intermediate": {
                "question": f"In a sprint planning meeting, how would you estimate and prioritize backlog items for a {job_role} project?",
                "input": "10 user stories with varying complexity",
                "output": "Prioritization and estimation approach",
                "constraints": "Use story points or t-shirt sizes.",
                "why_this": "Tests practical agile skills."
            },
            "advanced": {
                "question": f"How would you handle a situation where a critical bug is discovered 2 days before sprint end in a {job_role} context?",
                "input": "Critical bug needs immediate attention",
                "output": "Process for handling emergency",
                "constraints": "Balance sprint commitment and bug severity.",
                "why_this": "Tests agile problem-solving."
            },
            "expert": {
                "question": f"Design an agile transformation plan for a team of 20 developers moving from waterfall to Scrum for a {job_role} project.",
                "input": "20 developers, current process: waterfall",
                "output": "Transformation roadmap",
                "constraints": "Minimize disruption. Address resistance.",
                "why_this": "Tests leadership and change management."
            }
        }
    }

    # Default conceptual question for skills not in our database
    default_conceptual = {
        "beginner": {
            "question": f"Explain {skill_name} and describe a practical scenario where you would use it in a {job_role} role.",
            "input": "No code - conceptual",
            "output": "Clear explanation with examples",
            "constraints": "Connect to {job_role} responsibilities.",
            "why_this": f"Tests understanding of {skill_name}."
        },
        "intermediate": {
            "question": f"Compare different approaches or tools for {skill_name}. When would you choose each one for a {job_role} project?",
            "input": "No code - conceptual",
            "output": "Comparison with trade-offs",
            "constraints": "Mention pros and cons of each approach.",
            "why_this": f"Tests practical knowledge of {skill_name}."
        },
        "advanced": {
            "question": f"Design a system or solution using {skill_name} for a production {job_role} application. What challenges might you face?",
            "input": "Production system design",
            "output": "Architecture with {skill_name}",
            "constraints": "Address scalability and reliability.",
            "why_this": f"Tests system design with {skill_name}."
        },
        "expert": {
            "question": f"How would you implement and maintain {skill_name} at scale for a {job_role} organization? Address team training and process integration.",
            "input": "Enterprise implementation",
            "output": "Implementation strategy",
            "constraints": "Consider organizational factors.",
            "why_this": f"Tests leadership with {skill_name}."
        }
    }

    # Get the appropriate fallback
    if skill_type == "coding":
        fallbacks = coding_fallbacks
    elif skill_type == "tool":
        fallbacks = tool_fallbacks
    else:
        # Check if we have a specific conceptual fallback
        if skill_lower in conceptual_fallbacks:
            fallbacks = conceptual_fallbacks[skill_lower]
        else:
            fallbacks = default_conceptual

    # Get the question for this difficulty
    if skill_lower in fallbacks and difficulty in fallbacks[skill_lower]:
        return fallbacks[skill_lower][difficulty]
    elif isinstance(fallbacks, dict) and difficulty in fallbacks:
        result = fallbacks[difficulty].copy()
        result["question"] = result["question"].format(job_role=job_role)
        return result

    # Last resort - use intermediate as default
    if isinstance(fallbacks, dict) and "intermediate" in fallbacks:
        return fallbacks["intermediate"]

    return {
        "question": f"Explain {skill_name} and describe how you would apply it in a {job_role} role with practical examples.",
        "type": skill_type,
        "input": "No code - conceptual",
        "output": "Clear explanation",
        "constraints": "Connect to real-world scenarios.",
        "hints": ["Review fundamentals of " + skill_name, "Think about practical applications"],
        "why_this": f"Tests understanding of {skill_name} for {job_role}"
    }


# ─── Answer Evaluation ──────────────────────────────────────────────────────────

def evaluate_vi_answer(skill: str, question: str, answer: str, q_type: str, job_role: str, jd_context: str = "") -> dict:
    """Evaluate interview answer with improved criteria."""

    system_prompt = """You are an expert technical interviewer evaluating candidate answers.
Be HONEST and SPECIFIC in your evaluation:
- Give HIGH scores (80%+) only for genuinely good, complete answers
- Give LOW scores (40%-) for wrong, incomplete, or superficial answers
- Be critical but constructive in feedback
- Consider the difficulty level and job relevance
Return ONLY valid JSON."""

    try:
        eval_prompt = f"""Evaluate this interview answer for a {job_role} position.

SKILL BEING TESTED: {skill}
QUESTION TYPE: {q_type}

JOB CONTEXT:
{jd_context if jd_context else 'General software engineering role'}

QUESTION ASKED:
{question}

CANDIDATE'S ANSWER:
{answer}

Evaluation Criteria:
1. Correctness - Is the answer technically correct?
2. Completeness - Does it fully address the question?
3. Depth - Does it show deep understanding vs surface-level?
4. Practicality - Can this be applied in real work?
5. Job Relevance - Is it relevant to {job_role} work?

Return this EXACT JSON format:
{{
    "score": 0-100,
    "correct": true/false,
    "correctness": 0.0-1.0,
    "clarity": 0.0-1.0,
    "depth": "high"/"medium"/"low",
    "feedback": "Specific feedback on what was right and wrong",
    "strengths": ["What the answer did well"],
    "gaps": ["Specific gaps or mistakes in the answer"],
    "improvement_tip": "One actionable tip to improve"
}}"""

        response = call_vi_llm([{"role": "user", "content": eval_prompt}], max_tokens=500, system=system_prompt)
        response_lower = response.lower()

        # Parse JSON from response
        if '{' in response:
            start = response.find('{')
            end = response.rfind('}') + 1
            if end > start:
                try:
                    result = json.loads(response[start:end])
                    return {
                        "correctness": result.get("correctness", 0.5),
                        "clarity": result.get("clarity", 0.5),
                        "correct": result.get("correct", False),
                        "depth": result.get("depth", "medium"),
                        "feedback": result.get("feedback", response),
                        "strengths": result.get("strengths", []),
                        "gaps": result.get("gaps", []),
                        "improvement_tip": result.get("improvement_tip", "")
                    }
                except json.JSONDecodeError:
                    pass

        # Fallback: extract score with regex
        score = 50
        for pattern in [r'"score"\s*:\s*(\d+)', r'score[:\s]+(\d+)', r'(\d+)\s*/\s*100', r'(\d+)\s*out\s*of\s*100']:
            match = re.search(pattern, response_lower)
            if match:
                score = int(match.group(1))
                break

        # Determine depth from keywords
        depth = "medium"
        if any(w in response_lower for w in ["excellent", "outstanding", "in-depth", "comprehensive"]):
            depth = "high"
        elif any(w in response_lower for w in ["superficial", "incomplete", "lacking", "missing"]):
            depth = "low"

        correctness = score / 100.0
        correct = correctness >= 0.6

        return {
            "correctness": correctness,
            "clarity": correctness,
            "correct": correct,
            "depth": depth,
            "feedback": response,
            "strengths": ["Good attempt"] if correctness >= 0.5 else [],
            "gaps": ["Could be more detailed"] if correctness < 0.7 else [],
            "improvement_tip": ""
        }

    except Exception as e:
        return {
            "correctness": 0.5,
            "clarity": 0.5,
            "correct": False,
            "depth": "medium",
            "feedback": f"Evaluation completed: {str(e)}",
            "strengths": [],
            "gaps": ["Could not fully evaluate"],
            "improvement_tip": ""
        }


# ─── UI Rendering ──────────────────────────────────────────────────────────────

def render_interview_tab():
    """Render the interview tab."""

    # ─── Session State ─────────────────────────────────────────────────────────
    st.session_state.setdefault('vi_phase', 'input')  # input, skills, interview, results
    st.session_state.setdefault('vi_jd_text', '')
    st.session_state.setdefault('vi_skills', [])
    st.session_state.setdefault('vi_selected', [])
    st.session_state.setdefault('vi_current_idx', 0)
    st.session_state.setdefault('vi_question', None)
    st.session_state.setdefault('vi_eval_done', False)
    st.session_state.setdefault('vi_evaluation', None)
    st.session_state.setdefault('vi_scores', {})
    st.session_state.setdefault('vi_difficulty', {})
    st.session_state.setdefault('vi_answers', [])
    st.session_state.setdefault('vi_job_role', 'Software Engineer')

    # ─── Phase 0: JD Input ─────────────────────────────────────────────────────
    if st.session_state.vi_phase == 'input':
        st.markdown("### 🎤 Virtual Interview Engine")

        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)

            jd_input = st.text_area(
                "Job Description",
                height=180,
                placeholder="Paste the complete job description here. The interview questions will be based on this JD...",
                key="vi_jd"
            )

            st.markdown('</div>', unsafe_allow_html=True)

            col1, col2 = st.columns([3, 1])
            with col1:
                manual_skills = st.text_input("Or enter skills manually (comma-separated)", placeholder="Python, Docker, AWS, Machine Learning")
            with col2:
                st.markdown("")  # Spacing
                if st.button("🎯 Start Interview", type="primary", use_container_width=True):
                    if jd_input.strip():
                        with st.spinner("Analyzing JD and extracting skills..."):
                            skills = extract_vi_skills(jd_input)
                            st.session_state.vi_skills = skills
                            st.session_state.vi_jd_text = jd_input
                            st.session_state.vi_phase = 'skills'
                            st.rerun()
                    elif manual_skills.strip():
                        skills = [{"name": s.strip(), "type": "conceptual"} for s in manual_skills.split(",") if s.strip()]
                        st.session_state.vi_skills = skills
                        st.session_state.vi_jd_text = ""
                        st.session_state.vi_phase = 'skills'
                        st.rerun()

    # ─── Phase 1: Skill Selection ──────────────────────────────────────────────
    elif st.session_state.vi_phase == 'skills':
        st.markdown("### ✅ Select Skills to Assess")

        # Count by type
        coding_count = sum(1 for s in st.session_state.vi_skills if s.get('type') == 'coding')
        tool_count = sum(1 for s in st.session_state.vi_skills if s.get('type') == 'tool')
        conceptual_count = sum(1 for s in st.session_state.vi_skills if s.get('type') == 'conceptual')

        col_types = st.columns(3)
        with col_types[0]:
            st.metric("💻 Coding", coding_count)
        with col_types[1]:
            st.metric("🔧 Tools", tool_count)
        with col_types[2]:
            st.metric("📚 Conceptual", conceptual_count)

        st.markdown("---")

        selected = []

        # Group by type
        coding_skills = [s for s in st.session_state.vi_skills if s.get('type') == 'coding']
        tool_skills = [s for s in st.session_state.vi_skills if s.get('type') == 'tool']
        conceptual_skills = [s for s in st.session_state.vi_skills if s.get('type') == 'conceptual']

        if coding_skills:
            st.markdown("**💻 Coding Languages**")
            cols = st.columns(4)
            for i, skill in enumerate(coding_skills):
                with cols[i % 4]:
                    if st.checkbox(f" `{skill['name']}`", value=True, key=f"skill_c_{i}"):
                        selected.append(skill)
                        if skill['name'] not in st.session_state.vi_scores:
                            st.session_state.vi_scores[skill['name']] = {'correct': 0, 'total': 0}
                        if skill['name'] not in st.session_state.vi_difficulty:
                            st.session_state.vi_difficulty[skill['name']] = 3

        if tool_skills:
            st.markdown("**🔧 Tools & Frameworks**")
            cols = st.columns(4)
            for i, skill in enumerate(tool_skills):
                with cols[i % 4]:
                    if st.checkbox(f" `{skill['name']}`", value=True, key=f"skill_t_{i}"):
                        selected.append(skill)
                        if skill['name'] not in st.session_state.vi_scores:
                            st.session_state.vi_scores[skill['name']] = {'correct': 0, 'total': 0}
                        if skill['name'] not in st.session_state.vi_difficulty:
                            st.session_state.vi_difficulty[skill['name']] = 3

        if conceptual_skills:
            st.markdown("**📚 Concepts & Knowledge**")
            cols = st.columns(4)
            for i, skill in enumerate(conceptual_skills):
                with cols[i % 4]:
                    if st.checkbox(f" `{skill['name']}`", value=True, key=f"skill_k_{i}"):
                        selected.append(skill)
                        if skill['name'] not in st.session_state.vi_scores:
                            st.session_state.vi_scores[skill['name']] = {'correct': 0, 'total': 0}
                        if skill['name'] not in st.session_state.vi_difficulty:
                            st.session_state.vi_difficulty[skill['name']] = 3

        st.markdown("---")

        if selected and st.button(f"🚀 Begin Interview ({len(selected)} skills)", type="primary"):
            st.session_state.vi_selected = selected
            st.session_state.vi_current_idx = 0
            st.session_state.vi_phase = 'interview'
            st.rerun()

        if st.button("← Back", key="back_input"):
            st.session_state.vi_phase = 'input'
            st.rerun()

    # ─── Phase 2: Interview ─────────────────────────────────────────────────────
    elif st.session_state.vi_phase == 'interview':
        skill = st.session_state.vi_selected[st.session_state.vi_current_idx]
        skill_name = skill['name']
        skill_type = skill.get('type', 'conceptual')
        diff = st.session_state.vi_difficulty.get(skill_name, 3)

        total = len(st.session_state.vi_selected)
        current = st.session_state.vi_current_idx + 1

        # Type badge
        type_icons = {"coding": "💻", "tool": "🔧", "conceptual": "📚"}
        type_icon = type_icons.get(skill_type, "📝")

        st.markdown(f"### {type_icon} {skill_name}")
        st.markdown(f"**Type:** {skill_type.title()} | **Difficulty:** {'⭐' * diff}")
        st.progress(current / total, text=f"Skill {current}/{total}")

        # Generate question
        if not st.session_state.vi_question:
            with st.spinner("Generating question based on JD..."):
                st.session_state.vi_question = generate_vi_question(
                    skill_name, skill_type, diff,
                    st.session_state.vi_job_role,
                    st.session_state.vi_jd_text  # Pass JD context
                )

        q_data = st.session_state.vi_question

        # Display question with nice formatting
        st.markdown(f'<div class="card"><p class="card-header">❓ Question</p>{q_data.get("question", "Loading...")}</div>', unsafe_allow_html=True)

        # Show type-specific context
        if q_data.get("type") == "coding":
            col_io1, col_io2 = st.columns(2)
            with col_io1:
                if q_data.get("input"):
                    st.code(q_data.get("input"), language="text")
            with col_io2:
                if q_data.get("output"):
                    st.code(q_data.get("output"), language="text")
            if q_data.get("constraints"):
                st.caption(f"📋 Constraints: {q_data.get('constraints')}")

        elif q_data.get("what_looking_for"):
            st.info(f"**What we're looking for:** {q_data.get('what_looking_for')}")

        # Why this question
        if q_data.get("why_this"):
            st.caption(f"💡 *{q_data.get('why_this')}*")

        # Answer input
        st.markdown("**Your Answer:**")
        answer = st.text_area("", height=120, key=f"vi_answer_{current}", placeholder="Type your answer here...")

        # Buttons
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            submit = st.button("📤 Submit Answer", type="primary", disabled=not answer)
        with col_b2:
            hint_btn = st.button("💡 Show Hint")
        with col_b3:
            skip = st.button("⏭️ Skip")

        # Show hint
        if hint_btn and q_data.get("hints"):
            hints = q_data['hints']
            if isinstance(hints, list):
                st.info(f"💡 **Hint:** {hints[0] if hints else 'Think about practical applications.'}")
            else:
                st.info(f"💡 **Hint:** {hints}")

        # Process answer
        if submit and answer:
            with st.spinner("Evaluating your answer..."):
                ev = evaluate_vi_answer(
                    skill_name, q_data.get("question", ""), answer,
                    q_data.get("type", skill_type),
                    st.session_state.vi_job_role,
                    st.session_state.vi_jd_text  # Pass JD context
                )
                st.session_state.vi_evaluation = ev
                st.session_state.vi_eval_done = True
                st.session_state.vi_answers.append({
                    'skill': skill_name,
                    'answer': answer,
                    'eval': ev,
                    'question': q_data.get("question", "")
                })

                st.session_state.vi_scores[skill_name]['total'] += 1
                if ev.get('correctness', 0) >= 0.6:
                    st.session_state.vi_scores[skill_name]['correct'] += 1

                # Adjust difficulty based on performance
                if ev.get('correctness', 0) >= 0.8:
                    st.session_state.vi_difficulty[skill_name] = min(5, diff + 1)
                elif ev.get('correctness', 0) < 0.4:
                    st.session_state.vi_difficulty[skill_name] = max(1, diff - 1)

                st.rerun()

        # Skip button
        if skip:
            st.session_state.vi_current_idx += 1
            st.session_state.vi_question = None
            st.rerun()

        # Show evaluation
        if st.session_state.vi_eval_done:
            ev = st.session_state.vi_evaluation
            depth = ev.get('depth', 'medium')

            st.markdown("---")
            st.markdown("### 📊 Evaluation")

            col_e1, col_e2, col_e3 = st.columns(3)
            with col_e1:
                score = ev.get('correctness', 0)
                color = "#3fb950" if score >= 0.6 else "#d29922" if score >= 0.4 else "#f85149"
                st.markdown(f'<p class="metric-label">Score</p><p class="metric-value" style="color:{color}">{score:.0%}</p>', unsafe_allow_html=True)
            with col_e2:
                clarity = ev.get('clarity', 0)
                st.markdown(f'<p class="metric-label">Clarity</p><p class="metric-value">{clarity:.0%}</p>', unsafe_allow_html=True)
            with col_e3:
                emoji = "🟢" if depth == 'high' else "🟡" if depth == 'medium' else "🔴"
                st.markdown(f'<p class="metric-label">Depth</p><p class="metric-value">{emoji} {depth.upper()}</p>', unsafe_allow_html=True)

            # Feedback
            feedback = ev.get('feedback', '')
            try:
                if '{' in feedback and '}' in feedback:
                    fb_json = json.loads(feedback)
                    feedback = fb_json.get('feedback', feedback)
            except:
                pass

            st.markdown("**Feedback:**")
            st.info(feedback)

            # Strengths
            if ev.get('strengths'):
                st.success("**✅ Strengths:** " + " ".join(ev['strengths'][:2]))

            # Gaps
            if ev.get('gaps'):
                st.error("**❌ Gaps:** " + " ".join(ev['gaps'][:2]))

            # Improvement tip
            if ev.get('improvement_tip'):
                st.markdown(f"**💡 Tip to improve:** {ev['improvement_tip']}")

            st.markdown("---")

            # Next button
            next_idx = st.session_state.vi_current_idx + 1
            if next_idx >= len(st.session_state.vi_selected):
                if st.button("📊 View Results", type="primary"):
                    st.session_state.vi_phase = 'results'
                    st.rerun()
            else:
                if st.button("➡️ Next Skill"):
                    st.session_state.vi_current_idx = next_idx
                    st.session_state.vi_question = None
                    st.session_state.vi_eval_done = False
                    st.rerun()

    # ─── Phase 3: Results ────────────────────────────────────────────────────────
    elif st.session_state.vi_phase == 'results':
        st.markdown("## 🎉 Interview Complete!")

        total_correct = sum(s['correct'] for s in st.session_state.vi_scores.values())
        total_q = sum(s['total'] for s in st.session_state.vi_scores.values())
        overall = (total_correct / total_q * 100) if total_q > 0 else 0

        # Summary cards
        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        with col_r1:
            color = "#3fb950" if overall >= 60 else "#d29922" if overall >= 40 else "#f85149"
            st.markdown(f'<p class="metric-label">Overall Score</p><p class="metric-value" style="color:{color}">{overall:.0f}%</p>', unsafe_allow_html=True)
        with col_r2:
            st.markdown(f'<p class="metric-label">Questions</p><p class="metric-value">{total_q}</p>', unsafe_allow_html=True)
        with col_r3:
            st.markdown(f'<p class="metric-label">Correct</p><p class="metric-value" style="color:#3fb950">{total_correct}</p>', unsafe_allow_html=True)
        with col_r4:
            st.markdown(f'<p class="metric-label">Incorrect</p><p class="metric-value" style="color:#f85149">{total_q - total_correct}</p>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 🔍 Per-Skill Breakdown")

        for skill in st.session_state.vi_selected:
            name = skill['name']
            s_type = skill.get('type', 'conceptual')
            type_icons = {"coding": "💻", "tool": "🔧", "conceptual": "📚"}
            scores = st.session_state.vi_scores.get(name, {'correct': 0, 'total': 1})
            acc = scores['correct'] / scores['total'] if scores['total'] > 0 else 0
            diff = st.session_state.vi_difficulty.get(name, 3)

            if acc >= 0.8 and diff >= 4:
                level, emoji = "Expert", "🟢"
            elif acc >= 0.6:
                level, emoji = "Proficient", "🟡"
            elif acc >= 0.4:
                level, emoji = "Developing", "🟠"
            else:
                level, emoji = "Needs Training", "🔴"

            with st.container():
                col_s1, col_s2, col_s3, col_s4 = st.columns([1, 3, 1, 1])
                with col_s1:
                    st.markdown(f"{type_icons.get(s_type, '📝')}")
                with col_s2:
                    st.markdown(f"**{name}**")
                with col_s3:
                    st.markdown(f"{acc:.0%}")
                with col_s4:
                    st.markdown(f"{emoji} {level}")

        st.markdown("---")

        # Final recommendation
        if overall >= 75:
            st.success("## ✅ STRONG CANDIDATE - Recommended for Hire")
        elif overall >= 55:
            st.warning("## ⚠️ CONDITIONALLY RECOMMENDED - Consider with Training")
        else:
            st.error("## ❌ NEEDS MORE TRAINING - Not Recommended")

        # Download & Reset
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            report = {
                "overall_score": round(overall, 1),
                "recommendation": "Highly Recommended" if overall >= 75 else "Conditionally Recommended" if overall >= 55 else "Not Recommended",
                "skills": st.session_state.vi_scores,
                "difficulties": st.session_state.vi_difficulty,
                "answers": [
                    {"skill": a['skill'], "question": a['question'], "answer": a['answer'], "score": a['eval'].get('correctness', 0)}
                    for a in st.session_state.vi_answers
                ]
            }
            st.download_button("📥 Download Report", json.dumps(report, indent=2), "interview_report.json", mime="application/json")

        with col_d2:
            if st.button("🔄 New Interview"):
                for key in list(st.session_state.keys()):
                    if key.startswith('vi_'):
                        del st.session_state[key]
                st.rerun()
