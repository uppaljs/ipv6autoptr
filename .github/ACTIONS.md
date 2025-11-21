# GitHub Actions Documentation

This repository uses GitHub Actions for automated testing, building, and releasing. This document explains how to set up and use the CI/CD workflows.

## 📋 Workflows Overview

### 1. Continuous Integration (ci.yml)
**Triggers**: Pull requests and pushes to main branch

**What it does**:
- ✅ Tests across Python 3.11, 3.12, and 3.13
- ✅ Validates Python syntax and YAML configuration
- ✅ Tests Docker image building (Python 3.13 only)
- ✅ Code quality checks (Black, isort, flake8)
- ✅ Security scans (Safety, Bandit, Hadolint)

### 2. Build and Release (release.yml)
**Triggers**:
- Pushes to main branch (builds `latest` tag)
- Git tags starting with `v` (e.g., `v1.0.0`) for releases

**What it does**:
- 🧪 Runs comprehensive tests
- 🐳 Builds multi-platform Docker images (amd64, arm64)
- 📦 Pushes to Docker Hub with proper tagging
- 🚀 Creates GitHub releases with changelogs
- 🔒 Runs security scans on Docker images

## 🔧 Setup Instructions

### 1. Docker Hub Configuration

To enable Docker Hub publishing, you need to set up repository secrets:

1. **Create Docker Hub Access Token**:
   - Go to [Docker Hub Settings](https://hub.docker.com/settings/security)
   - Click "New Access Token"
   - Give it a name like "GitHub Actions"
   - Copy the generated token

2. **Add GitHub Secrets**:
   - Go to your repository → Settings → Secrets and variables → Actions
   - Add these secrets:

   | Secret Name | Description | Example Value |
   |-------------|-------------|---------------|
   | `DOCKERHUB_USERNAME` | Your Docker Hub username | `uppaljs` |
   | `DOCKERHUB_TOKEN` | Docker Hub access token | `dckr_pat_abc123...` |

### 2. Verify Setup

1. **Test CI Workflow**:
   ```bash
   # Create a test branch and push
   git checkout -b test-ci
   echo "# Test" >> test.md
   git add test.md
   git commit -m "Test CI workflow"
   git push -u origin test-ci
   ```
   - Create a Pull Request
   - Check that CI workflow runs successfully

2. **Test Release Workflow**:
   ```bash
   # Create and push a tag
   git tag v1.0.0
   git push origin v1.0.0
   ```
   - Check Actions tab for release workflow
   - Verify Docker images are pushed to Docker Hub
   - Verify GitHub release is created

## 🏷️ Versioning and Releases

### Semantic Versioning

This project uses [Semantic Versioning](https://semver.org/):

- `v1.0.0` - Major release
- `v1.1.0` - Minor release (new features)
- `v1.1.1` - Patch release (bug fixes)
- `v1.0.0-beta.1` - Pre-release

### Creating a Release

1. **Update VERSION file**:
   ```bash
   echo "1.1.0" > VERSION
   git add VERSION
   git commit -m "Bump version to 1.1.0"
   ```

2. **Create and push tag**:
   ```bash
   git tag v1.1.0
   git push origin main
   git push origin v1.1.0
   ```

3. **Automatic Process**:
   - GitHub Actions builds Docker images
   - Pushes to Docker Hub with tags: `v1.1.0`, `1.1`, `1`, `latest`
   - Creates GitHub release with changelog
   - Runs security scans

## 🐳 Docker Image Tagging

The release workflow creates multiple tags for flexibility:

| Tag Type | Example | Use Case |
|----------|---------|----------|
| Full version | `v1.2.3` | Pin to exact version |
| Major.Minor | `1.2` | Get latest patch |
| Major only | `1` | Get latest minor/patch |
| Latest | `latest` | Always get newest |
| Branch | `main` | Development builds |

### Usage Examples

```bash
# Production - pin to specific version
docker pull uppal/ipv6autoptr:v1.2.3

# Development - latest stable
docker pull uppal/ipv6autoptr:latest

# Auto-updates with minor versions
docker pull uppal/ipv6autoptr:1.2
```

## 🔒 Security Features

### Container Security
- 🔍 **Trivy vulnerability scanning** of final images
- 🛡️ **Hadolint** Dockerfile security analysis
- 👤 **Non-root user** in containers
- 🔒 **Minimal attack surface** with Alpine Linux

### Code Security
- 🔎 **Bandit** Python security analysis
- 📦 **Safety** dependency vulnerability checks
- 🏗️ **Multi-platform builds** for architecture security

### Security Reporting
- Vulnerability reports uploaded to GitHub Security tab
- Failed scans block releases
- Automated dependency updates (via Dependabot - configure separately)

## 📊 Monitoring and Notifications

### Build Status
- ✅ All workflows show status in Pull Requests
- 🔔 Failed builds notify repository maintainers
- 📈 Build summaries available in Actions tab

### Release Notifications
- 📧 GitHub automatically notifies watchers of new releases
- 📱 Configure repository notifications in GitHub settings
- 🔗 Release notes include Docker pull commands

## 🛠️ Troubleshooting

### Common Issues

1. **Docker Hub Push Fails**:
   ```
   Error: denied: requested access to the resource is denied
   ```
   - Check `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets
   - Verify Docker Hub token has push permissions
   - Ensure repository exists on Docker Hub

2. **Release Creation Fails**:
   ```
   Error: Resource not accessible by integration
   ```
   - Check `GITHUB_TOKEN` permissions
   - Verify repository settings allow Actions to create releases

3. **Build Timeout**:
   - Check for infinite loops in application code
   - Review resource usage in Actions tab
   - Consider increasing timeout values in workflow

### Debug Mode

Enable debug logging in Actions:
1. Go to repository Settings → Secrets
2. Add secret: `ACTIONS_STEP_DEBUG` = `true`
3. Re-run failed workflow

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Push Action](https://github.com/docker/build-push-action)
- [Semantic Versioning](https://semver.org/)
- [Docker Hub Access Tokens](https://docs.docker.com/docker-hub/access-tokens/)

## 🔄 Workflow Customization

### Adding New Platforms

To build for additional architectures, modify `release.yml`:

```yaml
platforms: linux/amd64,linux/arm64,linux/arm/v7
```

### Custom Release Notes

Modify the changelog generation in `release.yml`:

```bash
# Add custom sections to changelog.md
echo "### 🆕 New Features" >> changelog.md
echo "### 🐛 Bug Fixes" >> changelog.md
echo "### ⚡ Improvements" >> changelog.md
```

### Environment-Specific Deployments

Add deployment jobs for different environments:

```yaml
deploy-staging:
  if: github.ref == 'refs/heads/main'
  # Deploy to staging environment

deploy-production:
  if: startsWith(github.ref, 'refs/tags/v')
  # Deploy to production environment
```

---

**Happy Building! 🚀**