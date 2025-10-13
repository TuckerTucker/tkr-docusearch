# Library Frontend - Orchestration Plan

**Status**: Ready for Implementation
**Created**: 2025-10-13
**Feature Goal**: Production-ready document library UI with WebSocket real-time updates

---

## Overview

This orchestration plan coordinates **11 AI agents** across **3 waves** to build a complete frontend application at `/src/frontend` with zero conflicts and guaranteed integration.

**Target URL**: `http://localhost:8002/frontend/`

---

## Quick Start

### **For Coordination Lead**

1. **Review Core Documents**:
   - `orchestration-plan.md` - Complete execution plan
   - `agent-assignments.md` - Agent responsibilities
   - `coordination-protocol.md` - Communication and gates

2. **Execute Wave 0** (Foundation):
   ```bash
   # Run infrastructure agent
   # Creates directory structure
   # Configures worker
   # Validates setup
   ```

3. **Launch Wave 1** (6 Agents in Parallel):
   ```bash
   # Launch all 6 agents simultaneously:
   # - html-agent → index.html
   # - library-agent → library-manager.js, websocket-client.js, api-client.js
   # - card-agent → document-card.js
   # - filter-agent → filter-bar.js
   # - upload-agent → upload-modal.js
   # - style-agent → styles.css
   ```

4. **Validate Wave 1 Gate**:
   ```bash
   # Run validation script
   ./src/frontend/validate.sh
   ```

5. **Continue to Wave 2 & 3**

---

### **For Individual Agents**

1. **Find Your Assignment**:
   - Open `agent-assignments.md`
   - Locate your agent ID (e.g., `library-agent`)
   - Review your territory (files you own)

2. **Review Your Contracts**:
   - Navigate to `integration-contracts/`
   - Read contracts relevant to your work
   - Understand integration points

3. **Implement**:
   - Code only to your assigned files
   - Follow contract specifications exactly
   - Perform self-validation

4. **Report Status**:
   - Use format from `coordination-protocol.md`
   - Update every 30 minutes or at milestones
   - Escalate blockers immediately

---

## Directory Structure

```
.context-kit/orchestration/library-frontend/
├── README.md                        # This file
├── orchestration-plan.md            # Complete wave-based plan
├── agent-assignments.md             # Agent responsibilities
├── validation-strategy.md           # Testing and quality gates
├── coordination-protocol.md         # Communication and status
└── integration-contracts/           # Interface specifications
    ├── websocket.contract.md        # WebSocket message format
    ├── documents-api.contract.md    # Documents API spec
    ├── document-card.contract.md    # DocumentCard component API
    ├── filter-events.contract.md    # FilterBar event format
    └── upload-modal.contract.md     # UploadModal event format
```

---

## Key Features

### **Zero-Conflict Execution**
- Each agent owns distinct files (no overlaps)
- Integration via contracts, not coupling
- DOM events for runtime communication
- Guaranteed parallel safety

### **Progressive Validation**
- Validate after each wave, not at end
- Catch issues early
- Automated quality gates
- Clear pass/fail criteria

### **Specification-Driven**
- Contracts define all integration points
- Agents code to specs, not to each other
- Runtime decoupling via events
- Consumer-driven contract testing

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Browser Client                          │
├─────────────────────────────────────────────────────────────┤
│  index.html                                                  │
│  ├── LibraryManager                                         │
│  │   ├── WebSocketClient (ws://localhost:8002/ws)          │
│  │   ├── DocumentsAPIClient (GET /documents)               │
│  │   └── DocumentCard (component)                          │
│  ├── FilterBar (server-side filtering)                      │
│  ├── UploadModal (drag-drop to Copyparty)                   │
│  └── styles.css                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Wave Summary

### **Wave 0: Foundation** (1 Agent)
**Infrastructure Agent**: Setup directory, configure worker, validate access

### **Wave 1: Parallel Development** (6 Agents)
All work simultaneously:
- **html-agent**: HTML structure
- **library-agent**: Core logic + WebSocket + API client
- **card-agent**: DocumentCard component
- **filter-agent**: FilterBar with events
- **upload-agent**: UploadModal with drag-drop
- **style-agent**: Complete CSS

### **Wave 2: Integration & Testing** (3 Agents)
- **integration-agent**: Integration tests
- **e2e-agent**: End-to-end testing
- **docs-agent**: Documentation

### **Wave 3: Polish & Production** (2 Agents)
- **perf-agent**: Performance optimization
- **cleanup-agent**: Remove POC, final validation

---

## Integration Points

### **WebSocket** (Existing API)
- Endpoint: `ws://localhost:8002/ws`
- Messages: `status_update`, `log`, `stats`, `connection`
- Contract: `integration-contracts/websocket.contract.md`

### **Documents API** (Existing API)
- Endpoint: `GET /documents`
- Pagination, filtering, sorting
- Contract: `integration-contracts/documents-api.contract.md`

### **DocumentCard** (New Component)
- Function: `createDocumentCard(options)`
- Function: `updateCardState(card, status)`
- Contract: `integration-contracts/document-card.contract.md`

### **FilterBar** (New Component)
- Event: `filterChange` (CustomEvent)
- Event: `pageChange` (CustomEvent)
- Contract: `integration-contracts/filter-events.contract.md`

### **UploadModal** (New Component)
- Event: `uploadComplete` (CustomEvent)
- Event: `uploadError` (CustomEvent)
- Upload to: Copyparty API (`POST http://localhost:8000/uploads`)
- Contract: `integration-contracts/upload-modal.contract.md`

---

## Validation Gates

### **Wave 0 Gate**
- [ ] Directory structure created
- [ ] Worker configured and running
- [ ] Frontend accessible at `/frontend`

### **Wave 1 Gate**
- [ ] All 6 files created
- [ ] No syntax errors
- [ ] All exports available
- [ ] Browser console clean

### **Wave 2 Gate**
- [ ] Integration tests pass (>80% coverage)
- [ ] E2E tests pass (100%)
- [ ] Documentation complete

### **Wave 3 Gate**
- [ ] Performance targets met (<2s load, <1s FCP)
- [ ] POC removed
- [ ] Production ready

---

## Success Criteria

**Functional Requirements**:
- ✓ Library page accessible
- ✓ Documents load from API
- ✓ Real-time updates via WebSocket
- ✓ Drag-drop upload to Copyparty
- ✓ Server-side filtering/sorting
- ✓ Pagination working

**Quality Requirements**:
- ✓ Zero console errors
- ✓ WCAG AA accessibility
- ✓ <2s load time
- ✓ >80% test coverage
- ✓ Responsive design
- ✓ Complete documentation

---

## Timeline Estimate

- **Wave 0**: 1-2 hours (setup)
- **Wave 1**: 1 day (6 agents parallel)
- **Wave 2**: 4-6 hours (testing)
- **Wave 3**: 2-4 hours (polish)

**Total**: ~2 days end-to-end

---

## Risks & Mitigations

### **Risk: WebSocket Message Format Mismatch**
**Mitigation**: Contract specifies exact format, consumer validates

### **Risk: Agent File Conflicts**
**Mitigation**: Territorial ownership, zero overlaps

### **Risk: Integration Bugs**
**Mitigation**: Progressive validation, test after each wave

### **Risk: Performance Issues**
**Mitigation**: Dedicated performance agent, targets defined

---

## Getting Help

### **Contract Questions**
- Check `integration-contracts/` first
- Escalate ambiguities to coordination lead
- Use format from `coordination-protocol.md`

### **Blockers**
- Report immediately (format in `coordination-protocol.md`)
- Include severity, impact, attempted solutions
- Coordination lead responds <15 minutes

### **Status Updates**
- Every 30 minutes or at key milestones
- Use format from `coordination-protocol.md`
- Include progress, blockers, next steps

---

## Related Documentation

**Project Context**:
- `/_context-kit.yml` - Project architecture
- `/docs/QUICK_START.md` - System setup
- `/docs/GPU_ACCELERATION.md` - Worker configuration

**Existing APIs**:
- `/src/processing/worker_webhook.py` - Worker with WebSocket
- `/src/processing/websocket_broadcaster.py` - WebSocket implementation
- `/src/processing/documents_api.py` - Documents API

**POC Reference** (do not modify):
- `/data/copyparty/www/` - Proof of concept pages
- `/data/copyparty/www/modules/document-card.js` - Original component

---

## Next Steps

1. **Coordination Lead**: Review complete plan
2. **Infrastructure Agent**: Execute Wave 0
3. **All Agents**: Prepare for Wave 1 (review contracts)
4. **Wave 1 Kickoff**: Launch 6 agents in parallel
5. **Progressive Execution**: Complete all waves with validation gates

---

**Status**: ✅ Orchestration Plan Complete - Ready for Implementation

**Questions?** Review `coordination-protocol.md` for communication procedures
