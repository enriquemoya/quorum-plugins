# Claude Development Guidance

> **Looking for setup instructions?** This doc covers general best practices. For installing the plugins, skills, and orchestrator, see [`docs/claude-skills-overview.md`](claude-skills-overview.md) and [`INSTALL.md`](../INSTALL.md). New to the building blocks? Start with [`docs/claude-code-concepts.md`](claude-code-concepts.md).

## Overview

Claude should be used as a **pair programming partner** and **junior developer** - a helpful assistant that can write focused code, provide suggestions, and help brainstorm solutions. This document provides guidelines for safe and effective use of Claude in software development.

## Core Principles

### 🤝 Pair Programming Partner
- **Work together**: Use Claude to collaborate on specific coding tasks
- **Stay engaged**: Never leave Claude unattended while it's working
- **Review everything**: Always review and understand code before accepting it
- **Iterative approach**: Work in small, focused increments

### 👨‍💻 Junior Developer Mindset (for Implementation)
- **Focused tasks**: Give Claude specific, well-defined coding tasks
- **Limited scope**: Avoid asking for large, sweeping architectural changes
- **Guidance needed**: Provide context and direction for complex decisions
- **Review required**: Treat Claude's output like code from a junior developer

### 🧠 Senior Developer Mindset (for Design & Brainstorming)
- **Design discussions**: Claude can participate as a senior developer in architectural conversations
- **Pattern expertise**: Leverage Claude's knowledge of design patterns and best practices
- **Trade-off analysis**: Claude can provide experienced insights on technical decisions
- **Problem decomposition**: Use Claude's expertise to break down complex design challenges

## Best Practices

### ✅ Recommended Uses

#### **Focused Code Writing**
```
✅ "Write a function to validate email addresses"
✅ "Create a method to parse this JSON response"
✅ "Add error handling to this database call"
✅ "Write unit tests for this function"
```

#### **Code Review and Improvement**
```
✅ "Review this function for potential bugs"
✅ "Suggest performance improvements for this loop"
✅ "Help me refactor this method to be more readable"
✅ "Check this code for security vulnerabilities"
```

#### **Problem Solving and Brainstorming** (Senior Developer Capability)
```
✅ "What are different approaches to implement caching here?"
✅ "How should I structure this data for optimal queries?"
✅ "What design patterns would work for this scenario?"
✅ "Help me think through edge cases for this feature"
✅ "What are the architectural implications of this design choice?"
✅ "How would you design a scalable solution for this problem?"
✅ "What are the pros and cons of microservices vs monolith for this use case?"
✅ "Help me evaluate different database design approaches"
```

#### **Learning and Explanation**
```
✅ "Explain how this algorithm works"
✅ "What are the trade-offs of this approach?"
✅ "Help me understand this error message"
✅ "Show me examples of how to use this API"
```

### ❌ Avoid These Uses

#### **Large Architectural Changes**
```
❌ "Rewrite our entire authentication system"
❌ "Migrate the whole application to a new framework"
❌ "Redesign the database schema for the entire project"
❌ "Implement a complete microservices architecture"
```

#### **Unattended Operation**
```
❌ Asking Claude to work on multiple files while you're away
❌ Running Claude scripts without monitoring the output
❌ Letting Claude make changes to production code unsupervised
❌ Starting a large refactoring and walking away
```

#### **Critical Decision Making**
```
❌ "Choose our technology stack for the next project"
❌ "Decide on our security implementation strategy"
❌ "Make breaking changes to our public API"
❌ "Determine our deployment architecture"
```

## Safe Usage Guidelines

### 🔍 Always Review Code

**Language is ambiguous** - Even clear instructions can be interpreted multiple ways. Always:

1. **Read every line** of generated code
2. **Understand the logic** before accepting changes
3. **Test the code** to ensure it works as expected
4. **Check for edge cases** that might not be handled
5. **Verify security implications** of any changes

### 📝 Be Specific in Requests

**Clear communication prevents mistakes:**

```
❌ Vague: "Make this better"
✅ Specific: "Optimize this function to reduce database calls"

❌ Unclear: "Fix the user thing"
✅ Clear: "Add validation to prevent duplicate usernames in the registration form"

❌ Broad: "Update the API"
✅ Focused: "Add rate limiting to the /api/search endpoint"
```

### 🔄 Work Incrementally

**Small steps reduce risk:**

1. **Start small**: Begin with simple, isolated changes
2. **Test frequently**: Verify each change before moving to the next
3. **Commit often**: Save working states before making new changes
4. **Review together**: Discuss the approach before implementation

### 🛡️ Security Awareness

**Claude should never:**
- Handle or generate actual secrets, passwords, or API keys
- Make decisions about authentication or authorization logic
- Implement security features without your review and approval
- Access production systems or sensitive data

**Always review for:**
- Input validation
- SQL injection vulnerabilities
- XSS prevention
- Proper authentication checks
- Data exposure risks

## Effective Collaboration Patterns

### 🎯 Task-Focused Sessions

**Structure your work:**

1. **Define the goal**: "I want to add pagination to this API endpoint"
2. **Break it down**: "First, let's modify the repository method"
3. **Implement step-by-step**: Work on one component at a time
4. **Review each step**: Ensure understanding before proceeding
5. **Test incrementally**: Verify functionality as you build

### 💬 Brainstorming Sessions (Senior Developer Mode)

**Use Claude for senior-level design discussions:**

1. **Present the problem**: Describe the challenge you're facing with full context
2. **Ask for approaches**: "What are different ways to solve this?" (expect expert-level responses)
3. **Discuss trade-offs**: Explore architectural pros and cons with depth
4. **Evaluate patterns**: Discuss design patterns and industry best practices
5. **Choose together**: Make the final decision yourself, but leverage Claude's expertise
6. **Plan implementation**: Break chosen approach into actionable steps

### 🔧 Code Review Sessions

**Collaborative improvement:**

1. **Present the code**: Show Claude the code you want to improve
2. **Ask specific questions**: "Are there any performance issues here?"
3. **Review suggestions**: Understand why changes are recommended
4. **Implement selectively**: Choose which suggestions to apply
5. **Test changes**: Verify improvements work as expected

## Common Pitfalls to Avoid

### 🚨 Over-Reliance
- Don't let Claude become a crutch for learning
- Maintain your own understanding of the codebase
- Make your own technical decisions
- Stay involved in the problem-solving process

### 🚨 Blind Acceptance
- Never copy-paste code without understanding it
- Question approaches that seem overly complex
- Verify that solutions fit your specific context
- Check for compatibility with existing code

### 🚨 Context Loss
- Provide sufficient context for each request
- Remember that Claude doesn't retain session state
- Re-explain important constraints or requirements
- Share relevant code when asking for modifications

### 🚨 Scope Creep
- Resist the temptation to ask for "just one more thing"
- Keep tasks focused and well-defined
- Finish one task completely before starting another
- Don't let sessions become too long or complex

## Integration with Development Workflow

### 📋 Planning Phase
- **Brainstorm approaches** with Claude
- **Identify potential challenges** early
- **Break down complex tasks** into smaller pieces
- **Research unfamiliar technologies** or patterns

### 💻 Implementation Phase
- **Write focused code sections** together
- **Handle specific technical challenges** as they arise
- **Generate boilerplate code** to save time
- **Add comprehensive error handling**

### 🧪 Testing Phase
- **Generate unit tests** for new functionality
- **Create test data** and mock objects
- **Identify edge cases** to test
- **Review test coverage** and quality

### 🔍 Review Phase
- **Analyze code for improvements**
- **Check for security vulnerabilities**
- **Verify performance considerations**
- **Ensure coding standards compliance**

## Success Metrics

### ✅ Good Outcomes
- Code is working and well-understood
- Development velocity increased without sacrificing quality
- New techniques or patterns learned
- Complex problems broken down effectively
- Security and performance maintained

### ⚠️ Warning Signs
- Code works but you don't understand how
- Making changes without testing
- Accepting solutions that feel "too magical"
- Sessions lasting hours without breaks
- Implementing changes you wouldn't normally make

## Emergency Stops

**Stop and reassess if:**
- You're no longer understanding the changes being made
- The scope has grown beyond the original task
- Claude suggests changes to critical security code
- You're implementing solutions you're not comfortable with
- The session has been running for more than an hour

## Conclusion

Claude is a powerful tool when used appropriately as a collaborative partner. The key to success is understanding when to treat Claude as a junior developer vs. a senior consultant:

**For Implementation (Junior Developer Mode):**
- **You set direction** and make final decisions
- **Review and approve** all code changes
- **Understand** the reasoning behind solutions
- **Take responsibility** for the final implementation

**For Design & Brainstorming (Senior Developer Mode):**
- **Collaborate as peers** on architectural discussions
- **Leverage Claude's expertise** in patterns and best practices
- **Explore trade-offs together** with depth and experience
- **Make informed decisions** based on expert-level analysis

Remember: **You are always the pilot, but Claude can be both co-pilot and senior consultant depending on the task.** Stay engaged, stay informed, and maintain control of your development process.

---

*This guidance should be reviewed regularly and updated based on team experience and evolving best practices.*