# Docker Auto-Start Feature

## Overview

The `start-all.sh` script now automatically starts Docker Desktop if it's not running, providing a seamless startup experience.

## How It Works

When you run `./scripts/start-all.sh`:

1. **Check Docker**: Script checks if Docker daemon is running
2. **Auto-Start**: If not running, automatically launches Docker Desktop (macOS) or Docker service (Linux)
3. **Wait**: Waits up to 60 seconds for Docker daemon to be ready
4. **Progress**: Shows progress dots while waiting
5. **Continue**: Once ready, proceeds with starting services

## Example Output

```bash
./scripts/start-all.sh

╔═══════════════════════════════════════════════════════════╗
║  DocuSearch - Starting All Services                   ║
╚═══════════════════════════════════════════════════════════╝

Mode: Native worker with Metal GPU acceleration

Pre-flight checks...
Docker not running. Starting Docker Desktop...
  Waiting for Docker daemon..........
✓ Docker started successfully (20s)
```

## Configuration

### Enable Auto-Start (Default)

Auto-start is **enabled by default**. No configuration needed.

### Disable Auto-Start

To disable auto-start behavior:

**Option 1: Environment Variable**
```bash
export AUTO_START_DOCKER=false
./scripts/start-all.sh
```

**Option 2: .env File**
```bash
# In .env file
AUTO_START_DOCKER=false
```

## Platform Support

### macOS
- Uses `open -a Docker` command
- Works with Docker Desktop
- Typical startup: 10-30 seconds

### Linux
- Uses `systemctl start docker` command
- Requires systemd
- May require sudo permissions
- Typical startup: 2-10 seconds

### Windows (WSL2)
- Auto-start not currently supported
- Must start Docker Desktop manually
- Script will exit with helpful error message

## Troubleshooting

### Docker Fails to Start

**Error:**
```
Error: Docker failed to start after 60s
```

**Solutions:**
1. Check if Docker Desktop is installed
2. Try starting Docker Desktop manually
3. Check system resources (CPU, memory)
4. Restart your computer
5. Disable auto-start: `AUTO_START_DOCKER=false`

### Permission Denied (Linux)

**Error:**
```
Permission denied while trying to connect to Docker daemon
```

**Solution:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, then:
./scripts/start-all.sh
```

### Slow Startup

**Issue:** Docker takes a long time to start (> 30 seconds)

**Solutions:**
1. Check system resources (close other applications)
2. Increase Docker Desktop resources (Settings → Resources)
3. Check for Docker Desktop updates
4. Consider SSD upgrade if using HDD

## Use Cases

### Development Workflow
Perfect for daily development - just run `./scripts/start-all.sh` and everything starts automatically.

### After System Restart
After rebooting your Mac/Linux system, Docker Desktop isn't running. Auto-start handles this seamlessly.

### CI/CD Environments
Disable auto-start in automated environments:
```bash
AUTO_START_DOCKER=false ./scripts/start-all.sh
```

### Team Onboarding
New team members don't need to remember to start Docker manually - reduces friction in getting started.

## Technical Details

### Timeout
- **Maximum wait**: 60 seconds
- **Check interval**: 2 seconds
- **Stabilization delay**: 3 seconds after daemon ready

### Detection
The script uses `docker info` to check daemon status:
- **Success**: Exit code 0
- **Not running**: Exit code 1
- **Not installed**: Command not found

### OS Detection
Uses `$OSTYPE` environment variable:
- `darwin*` → macOS
- `linux-gnu*` → Linux
- Other → Error (unsupported)

## Related Configuration

Other Docker-related environment variables:
```bash
# Docker Compose directory
COMPOSE_DIR=./docker

# Service ports
CHROMADB_PORT=8001
COPYPARTY_PORT=8000
LEGACY_OFFICE_PORT=8003
```

## Feedback

If you encounter issues with Docker auto-start, please report:
1. Operating system and version
2. Docker Desktop version
3. Error messages
4. System resource availability (RAM, CPU)
