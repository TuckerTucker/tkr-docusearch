# Document Details Page - Orchestration

**Status**: Specification Complete
**Wave 0**: COMPLETE - Ready for execution
**Next Step**: Launch Wave 1 agents

---

## Quick Start

### For Implementation

1. **Review Plan**: Read `orchestration-plan.md` for complete wave structure
2. **Review Contracts**: See `integration-contracts/` for detailed specifications
3. **Check Status**: View `status/` directory for agent progress
4. **Launch Wave 1**: Start `data-layer-agent` and `vtt-agent` in parallel

### Key Files

| File | Purpose |
|------|---------|
| `orchestration-plan.md` | Complete execution plan with 5 waves |
| `integration-contracts/01-textchunk-extension.md` | TextChunk timestamp specification |
| `integration-contracts/02-vtt-generation.md` | VTT generation specification |
| `agent-assignments.md` | Agent territories and responsibilities |
| `validation-strategy.md` | Quality gates and testing approach |
| `coordination-protocol.md` | Communication and status management |

---

## Orchestration Summary

### Architecture

**Wave Model**: 5 waves with progressive validation
**Agents**: 6 specialized agents (3 backend, 3 frontend)
**Conflict Prevention**: Territorial file ownership
**Integration Method**: Interface-first contracts

### Wave Breakdown

| Wave | Agents | Duration | Deliverable |
|------|--------|----------|-------------|
| 0 | orchestrator | Immediate | Specifications |
| 1 | data-layer, vtt | 0.5 days | Timestamps & VTT generation |
| 2 | api | 0.5 days | Backend APIs |
| 3 | slideshow, audio, accordion | 1 day | Frontend components |
| 4 | orchestrator | 0.25 days | Integration & sync |
| 5 | test, polish | 0.25 days | Testing & production ready |

**Total**: 2.5 days with parallelization

---

## Integration Contracts Created

### Wave 1 Contracts
- [✅] IC-001: TextChunk Extension (timestamp fields)
- [✅] IC-002: VTT Generation (WebVTT format & pipeline)

### Remaining Contracts (to be generated)
- [ ] IC-003: API Endpoints (markdown, VTT, enhanced GET)
- [ ] IC-004: Slideshow Component (interface & events)
- [ ] IC-005: Audio Player Component (interface & events)
- [ ] IC-006: Accordion Component (interface & events)
- [ ] IC-007: Component Coordination (sync protocol)

---

## Agent Territories

### Backend (No Overlaps)

**data-layer-agent**:
- `src/processing/types.py` (edit)
- `src/processing/docling_parser.py` (edit)
- `src/processing/processor.py` (edit - timestamp storage)

**vtt-agent**:
- `src/processing/vtt_generator.py` (new)
- `src/processing/vtt_utils.py` (new)
- `src/processing/processor.py` (edit - VTT integration)
- `data/vtt/` (create & manage)

**api-agent**:
- `src/processing/documents_api.py` (extend only)
- `src/processing/markdown_utils.py` (new)

### Frontend (Sectional Ownership)

**slideshow-agent**:
- `src/frontend/slideshow.js` (new)
- `src/frontend/slideshow.css` (new)
- `src/frontend/details.html` (left column section)

**audio-agent**:
- `src/frontend/audio-player.js` (new)
- `src/frontend/audio-player.css` (new)
- `src/frontend/details.html` (left column section)

**accordion-agent**:
- `src/frontend/accordion.js` (new)
- `src/frontend/accordion.css` (new)
- `src/frontend/clipboard-utils.js` (new)
- `src/frontend/download-utils.js` (new)
- `src/frontend/details.html` (right column section)

---

## Quality Gates

### Wave 1 ✅ Criteria
```bash
# All unit tests pass
pytest src/processing/test_types.py -v
pytest src/processing/test_vtt_generator.py -v

# Timestamp extraction works
python -c "from src.processing.docling_parser import DoclingParser; \
  parser = DoclingParser(); \
  pages, meta, doc = parser.parse_document('test_audio.mp3'); \
  assert meta.get('has_word_timestamps') == True"

# VTT files generated
ls data/vtt/*.vtt | wc -l  # Should be > 0
```

### Wave 2 ✅ Criteria
```bash
# API endpoints functional
curl http://localhost:8002/documents/{test_doc}/markdown  # 200 OK
curl http://localhost:8002/documents/{test_doc}/vtt       # 200 OK
curl http://localhost:8002/documents/{test_doc}           # Has timestamps
```

### Wave 3 ✅ Criteria
```javascript
// Each component works in isolation
new Slideshow('#container', docId, pages).goToPage(3);
new AudioPlayer('#container', docId, metadata).seek(10);
new Accordion('#container', docId, data).openSection('chunk-0001');
```

### Wave 4 ✅ Criteria
```javascript
// All synchronization paths work
accordion.openSection('chunk-page3');
assert(slideshow.currentPage === 3);

audioPlayer.seek(15.0);
assert(accordion.activeSection === 'chunk-0002');
```

### Wave 5 ✅ Criteria
- All E2E tests pass
- No console errors
- Accessibility score > 90
- Mobile responsive

---

## Current Status

**Wave 0**: ✅ COMPLETE
- Orchestration plan created
- Integration contracts (2/7) generated
- Agent assignments defined
- Ready to launch Wave 1

**Next Actions**:
1. Generate remaining integration contracts (IC-003 to IC-007)
2. Create agent assignment documents
3. Launch Wave 1: data-layer-agent + vtt-agent in parallel
4. Monitor progress via status files

---

## Risk Mitigation

### Known Risks

1. **Timestamp Extraction** (Wave 1)
   - Risk: Provenance structure unknown
   - Mitigation: Mock data for testing, document actual structure
   - Fallback: Boolean flag if timestamps unavailable

2. **VTT Browser Compatibility** (Wave 1)
   - Risk: Malformed VTT rejected by browser
   - Mitigation: Validation library, browser testing
   - Fallback: Plain text transcript

3. **Synchronization Performance** (Wave 4)
   - Risk: Frequent timeupdate events cause lag
   - Mitigation: Throttle to 250ms, binary search
   - Fallback: Manual navigation only

---

## Success Metrics

### Technical
- ✅ 0 merge conflicts (territorial boundaries)
- ✅ 100% contract compliance
- ✅ All quality gates pass
- ✅ <2 integration bugs

### Delivery
- ✅ Backend complete: 1 day (Wave 1-2)
- ✅ Frontend complete: 1 day (Wave 3)
- ✅ Integration complete: 0.5 days (Wave 4-5)
- ✅ **Total: 2.5 days**

---

## References

- Wireframes: `.context-kit/_ref/details_page/`
- Document schema: `.context-kit/_ref/document_information_schema.md`
- Existing frontend: `src/frontend/`
- Existing APIs: `src/processing/documents_api.py`

---

*Generated: 2025-10-14 | Wave 0 Orchestrator*
