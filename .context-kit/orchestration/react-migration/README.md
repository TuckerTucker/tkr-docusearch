# React Migration Orchestration Plan

**Feature Goal:** Migrate 3-page vanilla JS frontend to React + Vite SPA
**Strategy:** 6 parallel agents with territorial ownership
**Timeline:** 4 waves (10-12 days)
**Status:** Ready to Execute

---

## 📁 Directory Structure

```
.context-kit/orchestration/react-migration/
├── README.md                          # This file
├── orchestration-plan.md              # Complete execution plan with waves
├── agent-assignments.md               # Territorial ownership map
├── validation-strategy.md             # Testing and quality gates
├── coordination-protocol.md           # Communication and sync procedures
├── integration-contracts/             # Interface specifications
│   ├── api-service.contract.md
│   ├── stores.contract.md
│   ├── hooks.contract.md
│   ├── layout-components.contract.md
│   ├── document-components.contract.md
│   ├── media-components.contract.md
│   ├── research-components.contract.md
│   ├── library-view.contract.md
│   ├── details-view.contract.md
│   └── research-view.contract.md
└── status/                            # Agent status files (generated)
    ├── foundation-agent.json
    ├── infrastructure-agent.json
    ├── layout-agent.json
    ├── library-agent.json
    ├── details-agent.json
    └── research-agent.json
```

---

## 🎯 Quick Start

### For Orchestration Coordinator

```bash
# 1. Review the orchestration plan
cat .context-kit/orchestration/react-migration/orchestration-plan.md

# 2. Review agent assignments
cat .context-kit/orchestration/react-migration/agent-assignments.md

# 3. Start Wave 0 (foundation-agent solo)
# Assign: foundation-agent to execute Wave 0 tasks

# 4. Monitor progress
./scripts/monitor-agents.sh

# 5. Open Wave 1 gate when Wave 0 complete
# Assign: infrastructure-agent, layout-agent, foundation-agent to Wave 1

# 6. Continue through waves 2, 3, 4
```

### For Individual Agents

```bash
# 1. Read your assignment
cat .context-kit/orchestration/react-migration/agent-assignments.md
# Find your agent section

# 2. Read all integration contracts you depend on
cat .context-kit/orchestration/react-migration/integration-contracts/*.contract.md

# 3. Create your status file
cp .context-kit/orchestration/react-migration/templates/status-template.json \
   .context-kit/orchestration/react-migration/status/{your-agent-name}.json

# 4. Start working on your wave tasks
# Update status every 15 minutes

# 5. Run tests continuously
npm run test:watch

# 6. Mark deliverables complete in status.json

# 7. Wait for wave gate to open before proceeding
```

---

## 📋 Wave Overview

### Wave 0: Foundation (Solo)
**Agent:** foundation-agent
**Duration:** 2-3 hours
**Goal:** Project scaffolding, build system, routing

**Key Deliverables:**
- ✅ Vite + React project initialized
- ✅ Dependencies installed
- ✅ Proxy configured
- ✅ Routes set up
- ✅ Dev server running

---

### Wave 1: Infrastructure & Layout (Parallel: 3 agents)
**Agents:** infrastructure-agent, layout-agent, foundation-agent
**Duration:** 1 day
**Goal:** Cross-cutting concerns (API, state, layout)

**Key Deliverables:**
- ✅ API services (api.js, websocket.js, research.js)
- ✅ State stores (connection, theme, documents)
- ✅ Custom hooks (useDocuments, useWebSocket, etc.)
- ✅ Layout shell (Header, Footer, Layout)
- ✅ Theme/style components
- ✅ Utilities and constants

---

### Wave 2: Feature Views (Parallel: 3 agents)
**Agents:** library-agent, details-agent, research-agent
**Duration:** 2 days
**Goal:** Complete all 3 main views

**Key Deliverables:**
- ✅ LibraryView (documents, filters, upload)
- ✅ DetailsView (slideshow, audio, accordion)
- ✅ ResearchView (query, answer, references)
- ✅ Real-time updates working
- ✅ Navigation between views

---

### Wave 3: Advanced Features & Quality (Parallel: 3 agents)
**Agents:** library-agent, details-agent, research-agent
**Duration:** 1-2 days
**Goal:** Advanced features, performance, testing

**Key Deliverables:**
- ✅ Bounding boxes, chunk highlighting
- ✅ Loading skeletons
- ✅ Comprehensive test coverage (>80%)
- ✅ Performance optimizations
- ✅ Accessibility enhancements

---

### Wave 4: Integration & Deployment (All agents)
**Agents:** All 6 agents
**Duration:** 1 day
**Goal:** Production readiness

**Key Deliverables:**
- ✅ E2E test suite
- ✅ Production build configuration
- ✅ Deployment scripts
- ✅ Documentation
- ✅ Lighthouse audits passing

---

## 📊 Progress Tracking

### Overall Progress
```
Wave 0: ⬜️ Not Started (0%)
Wave 1: ⬜️ Not Started (0%)
Wave 2: ⬜️ Not Started (0%)
Wave 3: ⬜️ Not Started (0%)
Wave 4: ⬜️ Not Started (0%)

Overall: 0% Complete
```

### Agent Status
```
foundation-agent:      ⬜️ Not Started
infrastructure-agent:  ⬜️ Not Started
layout-agent:          ⬜️ Not Started
library-agent:         ⬜️ Not Started
details-agent:         ⬜️ Not Started
research-agent:        ⬜️ Not Started
```

---

## 🔗 Integration Contracts

### Core Infrastructure Contracts

1. **API Service Contract** (`api-service.contract.md`)
   - Provider: infrastructure-agent
   - Consumers: library-agent, details-agent, research-agent
   - Defines: REST API client interface, error handling, timeouts

2. **Stores Contract** (`stores.contract.md`)
   - Provider: infrastructure-agent
   - Consumers: All agents
   - Defines: Connection store, theme store, documents store (Zustand)

3. **Hooks Contract** (`hooks.contract.md`)
   - Provider: infrastructure-agent
   - Consumers: library-agent, details-agent, research-agent
   - Defines: Custom React hooks (useDocuments, useWebSocket, etc.)

### Component Contracts

4. **Layout Components Contract** (`layout-components.contract.md`)
   - Provider: layout-agent
   - Consumers: All view agents
   - Defines: Header, Footer, Layout, ThemeToggle, StyleSelector

5. **Document Components Contract** (`document-components.contract.md`)
   - Provider: library-agent
   - Consumers: library-agent (internal)
   - Defines: DocumentCard, DocumentGrid, DocumentBadge

6. **Media Components Contract** (`media-components.contract.md`)
   - Provider: details-agent
   - Consumers: details-agent (internal)
   - Defines: Slideshow, AudioPlayer, AlbumArt, Accordion

7. **Research Components Contract** (`research-components.contract.md`)
   - Provider: research-agent
   - Consumers: research-agent (internal)
   - Defines: AnswerDisplay, ReferenceCard, CitationLink

### View Contracts

8. **Library View Contract** (`library-view.contract.md`)
   - Provider: library-agent
   - Defines: LibraryView props, events, state management

9. **Details View Contract** (`details-view.contract.md`)
   - Provider: details-agent
   - Defines: DetailsView props, URL params, content rendering

10. **Research View Contract** (`research-view.contract.md`)
    - Provider: research-agent
    - Defines: ResearchView props, query flow, citation handling

---

## ✅ Validation Gates

### Wave 0 Gate
- [ ] Dev server runs on :3000
- [ ] All 3 routes render
- [ ] API proxy works
- [ ] No console errors

### Wave 1 Gate
- [ ] All contract compliance tests pass
- [ ] All unit tests pass (>80% coverage)
- [ ] Layout renders with Header + Footer
- [ ] Theme toggle works
- [ ] No console errors

### Wave 2 Gate
- [ ] All 3 views fully functional
- [ ] All integration tests pass
- [ ] Navigation works
- [ ] Real-time updates working
- [ ] Lighthouse accessibility 100

### Wave 3 Gate
- [ ] All advanced features working
- [ ] Test coverage >80%
- [ ] Lighthouse performance >90
- [ ] Bundle size <500KB gzipped

### Wave 4 Gate
- [ ] All E2E tests pass
- [ ] Production build succeeds
- [ ] Manual QA complete
- [ ] Documentation complete
- [ ] READY FOR PRODUCTION

---

## 🚨 Common Issues & Solutions

### Issue: Agent blocked on dependency

**Solution:**
1. Check `integration-contracts/` for the interface specification
2. Create a mock implementation temporarily
3. Continue development with mock
4. Swap in real implementation when available

**Example:**
```javascript
// Temporary mock while waiting for infrastructure-agent
const useDocuments = (filters) => ({
  documents: [],
  isLoading: false,
  deleteDocument: async () => console.log('Mock delete')
});
```

---

### Issue: Integration test failing

**Solution:**
1. Check which contract is violated
2. Read contract specification
3. Update implementation to match contract
4. If contract is ambiguous, file clarification request

---

### Issue: Merge conflict

**Solution:**
This should NOT happen (territorial ownership). If it does:
1. Identify which agent violated boundaries
2. Review `agent-assignments.md`
3. Reassign file to correct agent
4. Rollback conflicting changes

---

## 📞 Communication

### Async Communication (Default)

- **Status updates:** Every 15 minutes → `status/{agent-name}.json`
- **Daily standup:** End of day → `standup/{date}-{agent}.md`
- **Blockers:** Immediately → `blockers/{blocker-id}.md`

### Sync Communication (Optional)

- **Checkpoint meetings:** Scheduled in advance
- **Emergency sync:** For critical blockers only

---

## 📚 Reference Documentation

### External Resources

- [React Documentation](https://react.dev)
- [Vite Documentation](https://vitejs.dev)
- [React Router Documentation](https://reactrouter.com)
- [React Query Documentation](https://tanstack.com/query/latest)
- [Zustand Documentation](https://docs.pmnd.rs/zustand)

### Project Documentation

- [Main README](../../../README.md) - Project overview
- [Architecture](../../../docs/ARCHITECTURE.md) - System architecture
- [API Reference](../../../docs/API_REFERENCE.md) - Backend API docs

---

## 🎉 Success Criteria

### Functional
- ✅ All 3 views fully functional
- ✅ Feature parity with vanilla JS app
- ✅ Real-time updates working
- ✅ Upload → process → view → research flow works

### Quality
- ✅ Test coverage >80%
- ✅ Lighthouse accessibility 100
- ✅ Lighthouse performance >90
- ✅ Zero console errors
- ✅ WCAG 2.1 AA compliance

### Performance
- ✅ First Contentful Paint <1s
- ✅ Time to Interactive <2s
- ✅ Bundle size <500KB gzipped

---

## 🚀 Execution Commands

### Start Wave 0 (Foundation)

```bash
# Solo execution by foundation-agent
claude-code --agent=foundation-agent \
            --task="Wave 0 Foundation" \
            --spec=".context-kit/orchestration/react-migration/agent-assignments.md#wave-0"
```

### Start Wave 1 (Infrastructure & Layout)

```bash
# Parallel execution by 3 agents
claude-code --parallel \
  --agent=infrastructure-agent --task="Wave 1 Infrastructure" \
  --agent=layout-agent --task="Wave 1 Layout" \
  --agent=foundation-agent --task="Wave 1 Utilities"
```

### Start Wave 2 (Feature Views)

```bash
# Parallel execution by 3 agents
claude-code --parallel \
  --agent=library-agent --task="Wave 2 Library View" \
  --agent=details-agent --task="Wave 2 Details View" \
  --agent=research-agent --task="Wave 2 Research View"
```

### Start Wave 3 (Advanced Features)

```bash
# Parallel execution by 3 agents
claude-code --parallel \
  --agent=library-agent --task="Wave 3 Library Advanced" \
  --agent=details-agent --task="Wave 3 Details Advanced" \
  --agent=research-agent --task="Wave 3 Research Advanced"
```

### Start Wave 4 (Final Integration)

```bash
# All agents work together
claude-code --parallel --all-agents \
            --task="Wave 4 Final Integration"
```

---

## 📝 Notes

- **Zero backend changes** - Python API remains unchanged
- **Interface-first development** - Read contracts before implementing
- **Progressive validation** - Test after each wave
- **Territorial ownership** - No file conflicts
- **Continuous communication** - Status updates every 15 minutes

---

## 📅 Timeline Estimate

| Wave | Duration | Agents | Key Milestone |
|------|----------|--------|---------------|
| Wave 0 | 2-3 hours | 1 | Dev server running |
| Wave 1 | 1 day | 3 | Infrastructure ready |
| Wave 2 | 2 days | 3 | All views functional |
| Wave 3 | 1-2 days | 3 | Performance optimized |
| Wave 4 | 1 day | 6 | Production ready |
| **Total** | **10-12 days** | **6** | **SPA deployed** |

---

## 🏁 Ready to Execute

All orchestration artifacts are complete:
- ✅ Orchestration plan defined
- ✅ Agent assignments mapped
- ✅ Integration contracts written
- ✅ Validation strategy documented
- ✅ Coordination protocol established

**Next Step:** Begin Wave 0 with foundation-agent
