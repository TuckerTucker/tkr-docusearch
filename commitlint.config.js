/**
 * Commitlint Configuration
 *
 * Enforces conventional commit message format for consistent commit history
 * and automated release notes generation.
 *
 * Format: <type>(<scope>): <subject>
 *
 * Types:
 *   feat:      A new feature
 *   fix:       A bug fix
 *   docs:      Documentation only changes
 *   style:     Changes that do not affect code meaning (formatting, missing semicolons, etc)
 *   refactor:  Code change that neither fixes a bug nor adds a feature
 *   perf:      Code change that improves performance
 *   test:      Adding missing tests or correcting existing tests
 *   chore:     Changes to build process, dependencies, or devops
 *   ci:        Changes to CI/CD configuration
 *   revert:    Reverts a previous commit
 *
 * Scopes (optional):
 *   backend, frontend, search, research, ui, api, mcp, etc.
 *
 * Examples:
 *   feat(frontend): add dark mode toggle
 *   fix(search): resolve memory leak in useThemeStore
 *   docs(contributing): update commit message guidelines
 *   refactor(upload): simplify state management with useReducer
 */

module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      [
        'feat',      // A new feature
        'fix',       // A bug fix
        'docs',      // Documentation only changes
        'style',     // Changes that do not affect the meaning of code (formatting, etc)
        'refactor',  // A code change that neither fixes a bug nor adds a feature
        'perf',      // A code change that improves performance
        'test',      // Adding missing or updating existing tests
        'chore',     // Changes to build process, dependencies, or development utilities
        'ci',        // Changes to CI/CD configuration and scripts
        'revert',    // Revert a previous commit
      ],
    ],
    'type-case': [2, 'always', 'lowercase'],
    'type-empty': [2, 'never'],
    'scope-case': [2, 'always', 'lowercase'],
    'subject-empty': [2, 'never'],
    'subject-full-stop': [2, 'never', '.'],
    'subject-case': [2, 'never', ['start-case', 'pascal-case', 'upper-case']],
    'header-max-length': [2, 'always', 72],
    'body-max-line-length': [2, 'always', 100],
  },
};
