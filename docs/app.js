/**
 * Enterprise Intelligence Gateway (EIG) — Interactive Web Portal Logic
 * Implements client-side simulations of Multi-Tenant RAG, Two-Phase Human-in-the-Loop Approvals,
 * Cryptographic Hash Chain Audit Ledger, Telemetry, and REST API Client.
 */

document.addEventListener('DOMContentLoaded', () => {
  initThemeToggle();
  initNavigationTabs();
  initRagSimulator();
  initAgentWorkflow();
  initApiExplorer();
});

/* =========================================================================
   1. Theme Management (Light / Dark Mode)
   ========================================================================= */
function initThemeToggle() {
  const toggleBtn = document.getElementById('themeToggleBtn');
  const body = document.body;
  
  const savedTheme = localStorage.getItem('eig_theme') || 'theme-light';
  body.className = savedTheme;

  toggleBtn.addEventListener('click', () => {
    if (body.classList.contains('theme-light')) {
      body.classList.remove('theme-light');
      body.classList.add('theme-dark');
      localStorage.setItem('eig_theme', 'theme-dark');
    } else {
      body.classList.remove('theme-dark');
      body.classList.add('theme-light');
      localStorage.setItem('eig_theme', 'theme-light');
    }
  });
}

/* =========================================================================
   2. Sticky Navigation Tabs
   ========================================================================= */
function initNavigationTabs() {
  const tabs = document.querySelectorAll('.nav-tab');
  const panes = document.querySelectorAll('.tab-pane');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetId = tab.getAttribute('data-tab');
      
      tabs.forEach(t => t.classList.remove('active'));
      panes.forEach(p => p.classList.remove('active'));

      tab.classList.add('active');
      const targetPane = document.getElementById(targetId);
      if (targetPane) {
        targetPane.classList.add('active');
      }

      // Smooth scroll if clicked from lower on page
      const navBar = document.getElementById('stickyNav');
      if (window.scrollY > navBar.offsetTop) {
        window.scrollTo({
          top: navBar.offsetTop - 75,
          behavior: 'smooth'
        });
      }
    });
  });

  // Hero CTA buttons routing to tabs
  const btnExplore = document.getElementById('btnExploreDemo');
  const btnViewArch = document.getElementById('btnViewArch');

  if (btnExplore) {
    btnExplore.addEventListener('click', (e) => {
      e.preventDefault();
      document.getElementById('navTabRag').click();
    });
  }

  if (btnViewArch) {
    btnViewArch.addEventListener('click', (e) => {
      e.preventDefault();
      document.getElementById('navTabArchitecture').click();
    });
  }
}

/* =========================================================================
   3. Multi-Tenant Hybrid RAG Simulator (Module 2)
   ========================================================================= */
function initRagSimulator() {
  const personaRadios = document.querySelectorAll('input[name="persona"]');
  const queryInput = document.getElementById('queryPromptInput');
  const btnExecute = document.getElementById('btnExecuteRagQuery');
  const chipButtons = document.querySelectorAll('.quick-prompts .chip');

  // Persona radio box active class toggling
  personaRadios.forEach(radio => {
    radio.addEventListener('change', () => {
      document.querySelectorAll('.persona-radio').forEach(p => p.classList.remove('active'));
      radio.closest('.persona-radio').classList.add('active');
    });
  });

  // Quick prompt chips
  chipButtons.forEach(chip => {
    chip.addEventListener('click', () => {
      const promptText = chip.getAttribute('data-prompt');
      const targetPersona = chip.getAttribute('data-persona');

      if (promptText) queryInput.value = promptText;
      if (targetPersona) {
        const radio = document.querySelector(`input[name="persona"][value="${targetPersona}"]`);
        if (radio) {
          radio.checked = true;
          document.querySelectorAll('.persona-radio').forEach(p => p.classList.remove('active'));
          radio.closest('.persona-radio').classList.add('active');
        }
      }
      executeRagSimulation();
    });
  });

  btnExecute.addEventListener('click', () => {
    executeRagSimulation();
  });
}

function getActivePersona() {
  const checked = document.querySelector('input[name="persona"]:checked');
  const val = checked ? checked.value : 'alice';

  const personas = {
    alice: { name: 'Alice Smith', role: 'user', tenant: 'healthcare_corp' },
    bob: { name: 'Bob Vance', role: 'admin', tenant: 'healthcare_corp' },
    charlie: { name: 'Charlie Chen', role: 'user', tenant: 'fintech_ltd' },
    mallory: { name: 'Mallory', role: 'user', tenant: 'untrusted_guest' }
  };
  return personas[val] || personas.alice;
}

function resetTraceSteps() {
  const steps = ['stepAuth', 'stepHybrid', 'stepRerank', 'stepGen'];
  steps.forEach(s => {
    const el = document.getElementById(s);
    el.className = 'trace-step';
    const statusEl = document.getElementById(`${s}Status`);
    if (statusEl) statusEl.textContent = '⏸️';
  });
}

function executeRagSimulation() {
  const persona = getActivePersona();
  const query = document.getElementById('queryPromptInput').value.trim();
  const badge = document.getElementById('ragStatusBadge');
  const latencyEl = document.getElementById('ragLatency');
  const responseText = document.getElementById('ragResponseText');
  const citationsBox = document.getElementById('citationsBox');
  const citationsList = document.getElementById('citationsList');

  resetTraceSteps();
  badge.className = 'badge-pill bg-purple';
  badge.textContent = 'Processing Pipeline...';
  responseText.innerHTML = '<span class="status-indicator">●</span> Evaluating query through cryptographic tenant boundary...';
  citationsBox.style.display = 'none';
  citationsList.innerHTML = '';

  const startTime = performance.now();

  // Step 1: Auth & RBAC
  setTimeout(() => {
    const stepAuth = document.getElementById('stepAuth');
    const authText = document.getElementById('traceAuthText');
    const authStatus = document.getElementById('stepAuthStatus');

    if (persona.tenant === 'untrusted_guest') {
      stepAuth.className = 'trace-step denied';
      authText.textContent = `FORBIDDEN: Tenant '${persona.tenant}' has untrusted signature.`;
      authStatus.textContent = '❌';

      badge.className = 'badge-pill highlight-red';
      badge.textContent = 'Tenant Auth Blocked';
      latencyEl.textContent = `Latency: ${(performance.now() - startTime).toFixed(1)} ms`;
      responseText.innerHTML = `
        <div style="color: var(--accent-rose); font-weight: 600;">
          [403 FORBIDDEN] Tenant Access Denied
        </div>
        <p style="margin-top: 0.5rem; font-size: 0.875rem;">
          The gateway verified cryptographic claims for user <code>${persona.name}</code>. Tenant <code>${persona.tenant}</code> does not have an active enterprise subscription or valid decryption keys. Access completely severed.
        </p>
      `;
      return;
    }

    stepAuth.className = 'trace-step success';
    authText.textContent = `Verified JWT: Tenant='${persona.tenant}' | Role='${persona.role}'`;
    authStatus.textContent = '✅';

    // Step 2: Hybrid Retrieval
    setTimeout(() => {
      const stepHybrid = document.getElementById('stepHybrid');
      const hybridText = document.getElementById('traceHybridText');
      const hybridStatus = document.getElementById('stepHybridStatus');

      // Cross-Tenant Detection Check
      const queryLower = query.toLowerCase();
      const isFintechQuery = queryLower.includes('fintech') || queryLower.includes('financial') || queryLower.includes('forecast') || queryLower.includes('revenue');
      const isHealthcareQuery = queryLower.includes('sterilisation') || queryLower.includes('surgical') || queryLower.includes('patient') || queryLower.includes('device');

      if (persona.tenant === 'healthcare_corp' && isFintechQuery) {
        stepHybrid.className = 'trace-step denied';
        hybridText.textContent = `FILTER APPLIED: Isolated to tenant='healthcare_corp'. 0 documents matched.`;
        hybridStatus.textContent = '🛡️';

        const stepRerank = document.getElementById('stepRerank');
        stepRerank.className = 'trace-step denied';
        document.getElementById('traceRerankText').textContent = 'Re-ranker score 0.000 (No cross-tenant chunks allowed)';
        document.getElementById('stepRerankStatus').textContent = '🛡️';

        const stepGen = document.getElementById('stepGen');
        stepGen.className = 'trace-step denied';
        document.getElementById('traceGenText').textContent = 'Strict Abstention Protocol Triggered';
        document.getElementById('stepGenStatus').textContent = '🛑';

        badge.className = 'badge-pill highlight-red';
        badge.textContent = 'Zero-Leakage Active';
        latencyEl.textContent = `Latency: ${(performance.now() - startTime).toFixed(1)} ms`;
        responseText.innerHTML = `
          <div style="color: var(--accent-rose); font-weight: 600;">
            [STRICT ABSTENTION] Cross-Tenant Boundary Enforced
          </div>
          <p style="margin-top: 0.5rem; font-size: 0.875rem;">
            User <code>${persona.name}</code> (Tenant: <code>${persona.tenant}</code>) attempted to query financial data belonging to another enterprise partition. 
            Cryptographic tenant partitioning in vector storage prevented any cross-tenant vector chunks from leaking.
          </p>
          <div style="margin-top: 0.5rem; font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-muted);">
            Metrics Incremented: <code>eig_tenant_access_denied_total{attempted="fintech_ltd", source="healthcare_corp"}</code>
          </div>
        `;
        return;
      }

      stepHybrid.className = 'trace-step success';
      hybridText.textContent = `Retrieved 15 candidates: BM25 (top 10) + Qdrant Dense (top 10) fused via RRF`;
      hybridStatus.textContent = '✅';

      // Step 3: Cross-Encoder Rerank
      setTimeout(() => {
        const stepRerank = document.getElementById('stepRerank');
        const rerankText = document.getElementById('traceRerankText');
        const rerankStatus = document.getElementById('stepRerankStatus');

        stepRerank.className = 'trace-step success';
        rerankText.textContent = `Cross-Encoder top chunk relevance: 0.948 (threshold > 0.65 passed)`;
        rerankStatus.textContent = '✅';

        // Step 4: Grounded Generation
        setTimeout(() => {
          const stepGen = document.getElementById('stepGen');
          const genText = document.getElementById('traceGenText');
          const genStatus = document.getElementById('stepGenStatus');

          stepGen.className = 'trace-step success';
          genText.textContent = `100% grounded against retrieved citations`;
          genStatus.textContent = '✅';

          badge.className = 'badge-pill bg-green';
          badge.textContent = 'Query Grounded & Verified';
          latencyEl.textContent = `Latency: ${(performance.now() - startTime).toFixed(1)} ms`;

          if (persona.tenant === 'healthcare_corp' && isHealthcareQuery) {
            responseText.innerHTML = `
              <p>According to the verified enterprise sterilisation manual, <strong>surgical devices must undergo high-pressure steam autoclaving at 134°C for a minimum duration of 18 minutes</strong>, followed by a vacuum drying phase of 12 minutes before entering the sterile barrier packaging cycle.</p>
            `;
            citationsBox.style.display = 'block';
            citationsList.innerHTML = `
              <div class="citation-badge">📄 doc_hc_device_sterilisation_v2.pdf &bull; Page 4 &bull; §4.2 (Score: 0.948)</div>
              <div class="citation-badge">📄 doc_hc_regulatory_compliance_2026.pdf &bull; Page 11 &bull; §2.1 (Score: 0.882)</div>
            `;
          } else if (persona.tenant === 'fintech_ltd' && isFintechQuery) {
            responseText.innerHTML = `
              <p>For <strong>Fintech Ltd</strong>, the Q3 financial growth forecast targets an annualized revenue expansion of <strong>28.4% YoY</strong>, driven primarily by enterprise cross-border payment gateway API adoption and increased liquidity volumes in tier-1 markets.</p>
            `;
            citationsBox.style.display = 'block';
            citationsList.innerHTML = `
              <div class="citation-badge">📄 doc_fintech_q3_financial_outlook.pdf &bull; Page 2 &bull; Table 3 (Score: 0.952)</div>
            `;
          } else {
            responseText.innerHTML = `
              <p>Retrieved enterprise context verified for <strong>${persona.tenant}</strong>. The query was successfully evaluated against authorized tenant knowledge documents with deterministic traceability.</p>
            `;
            citationsBox.style.display = 'block';
            citationsList.innerHTML = `
              <div class="citation-badge">📄 general_policy_${persona.tenant}.md &bull; Section 1 &bull; (Score: 0.865)</div>
            `;
          }
        }, 220);
      }, 200);
    }, 180);
  }, 150);
}

/* =========================================================================
   4. Autonomous Agent & Two-Phase Approval Workflow (Module 3)
   ========================================================================= */
const auditLedger = [
  {
    block: 1,
    time: '2026-10-25 15:42:10 UTC',
    tool: 'ERP_Query',
    action: 'Check supply inventory for Part #4029',
    risk: '0.15 (LOW)',
    prevHash: '0000000000000000000000000000000000000000000000000000000000000000',
    hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    status: 'AUTO_APPROVED'
  },
  {
    block: 2,
    time: '2026-10-25 15:58:34 UTC',
    tool: 'CRM_Update',
    action: 'Update corporate phone number for Account #89',
    risk: '0.40 (LOW)',
    prevHash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    hash: 'a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0',
    status: 'AUTO_APPROVED'
  },
  {
    block: 3,
    time: '2026-10-25 16:12:05 UTC',
    tool: 'ERP_Query',
    action: 'Retrieve supplier billing invoices Q3',
    risk: '0.22 (LOW)',
    prevHash: 'a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0',
    hash: '7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f90123456789abcdef012',
    status: 'AUTO_APPROVED'
  },
  {
    block: 4,
    time: '2026-10-25 16:25:40 UTC',
    tool: 'CRM_Update',
    action: 'Issue $1,200.00 store credit voucher',
    risk: '0.62 (MEDIUM)',
    prevHash: '7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f90123456789abcdef012',
    hash: 'f0e1d2c3b4a5968778695a4b3c2d1e0f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d',
    status: 'AUTO_APPROVED'
  }
];

let pendingActionData = null;
let timerInterval = null;

function initAgentWorkflow() {
  const select = document.getElementById('agentActionSelect');
  const btnDispatch = document.getElementById('btnDispatchAgentAction');
  const btnApprove = document.getElementById('btnApproveAction');
  const btnReject = document.getElementById('btnRejectAction');

  renderAuditLedger();

  select.addEventListener('change', () => {
    updateActionDetailsCard(select.value);
  });

  btnDispatch.addEventListener('click', () => {
    dispatchSelectedAction(select.value);
  });

  btnApprove.addEventListener('click', () => {
    resolvePendingApproval(true);
  });

  btnReject.addEventListener('click', () => {
    resolvePendingApproval(false);
  });
}

function updateActionDetailsCard(actionKey) {
  const toolNameEl = document.getElementById('actionToolName');
  const riskScoreEl = document.getElementById('actionRiskScore');
  const financialEl = document.getElementById('actionFinancialImpact');
  const policyEl = document.getElementById('actionPolicyRule');

  if (actionKey === 'erp_read_inventory') {
    toolNameEl.textContent = 'erp_read_inventory';
    riskScoreEl.className = 'risk-badge risk-low';
    riskScoreEl.textContent = '0.15 (LOW)';
    financialEl.textContent = '$0.00 (Read Only)';
    policyEl.className = 'detail-value highlight-green';
    policyEl.textContent = 'Standard Autonomous Execution (Pre-Authorized)';
  } else if (actionKey === 'crm_update_contact') {
    toolNameEl.textContent = 'crm_update_contact';
    riskScoreEl.className = 'risk-badge risk-low';
    riskScoreEl.textContent = '0.40 (LOW)';
    financialEl.textContent = '$0.00 (Contact Record)';
    policyEl.className = 'detail-value highlight-green';
    policyEl.textContent = 'Standard Autonomous Execution (Audit Logged)';
  } else if (actionKey === 'crm_issue_refund') {
    toolNameEl.textContent = 'crm_issue_refund';
    riskScoreEl.className = 'risk-badge risk-high';
    riskScoreEl.textContent = '0.95 (HIGH)';
    financialEl.textContent = '$45,000.00 USD';
    policyEl.className = 'detail-value highlight-red';
    policyEl.textContent = 'Mandatory 2FA HMAC-SHA256 Approval Required (> $10,000)';
  } else if (actionKey === 'erp_deprecate_db') {
    toolNameEl.textContent = 'erp_deprecate_database';
    riskScoreEl.className = 'risk-badge risk-high';
    riskScoreEl.textContent = '0.99 (CRITICAL)';
    financialEl.textContent = 'Infrastructure Impact: Critical High';
    policyEl.className = 'detail-value highlight-red';
    policyEl.textContent = 'Mandatory Dual-Admin 2FA Approval Required (Destructive)';
  }
}

function dispatchSelectedAction(actionKey) {
  const approvalCard = document.getElementById('approvalCard');

  if (actionKey === 'erp_read_inventory' || actionKey === 'crm_update_contact') {
    approvalCard.style.display = 'none';
    const isInventory = actionKey === 'erp_read_inventory';
    appendBlockToLedger({
      tool: isInventory ? 'ERP_Query' : 'CRM_Update',
      action: isInventory ? 'Check supply inventory for Part #4029' : 'Update phone number for Account #89',
      risk: isInventory ? '0.15 (LOW)' : '0.40 (LOW)',
      status: 'AUTO_APPROVED'
    });
  } else {
    // High Risk: triggers 2-Phase Approval
    approvalCard.style.display = 'block';
    const actionId = 'act_' + Math.random().toString(36).substring(2, 10);
    const nonce = '0x' + Array.from({length: 16}, () => Math.floor(Math.random()*16).toString(16)).join('');
    const signature = Array.from({length: 32}, () => Math.floor(Math.random()*16).toString(16)).join('');

    document.getElementById('cryptoActionId').textContent = actionId;
    document.getElementById('cryptoNonce').textContent = nonce;
    document.getElementById('cryptoSignature').textContent = signature.substring(0, 16) + '...' + signature.substring(24);

    pendingActionData = {
      actionId,
      nonce,
      signature,
      tool: actionKey === 'crm_issue_refund' ? 'CRM_Update' : 'ERP_Write',
      action: actionKey === 'crm_issue_refund' ? 'Issue $45,000.00 Customer Credit Refund' : 'Deprecate Legacy Billing Database Cluster',
      risk: actionKey === 'crm_issue_refund' ? '0.95 (HIGH)' : '0.99 (CRITICAL)'
    };

    startApprovalCountdown();
  }
}

function startApprovalCountdown() {
  if (timerInterval) clearInterval(timerInterval);
  let secondsRemaining = 299; // 5 minutes TTL

  const timerEl = document.getElementById('approvalTimer');
  timerInterval = setInterval(() => {
    const mins = Math.floor(secondsRemaining / 60);
    const secs = secondsRemaining % 60;
    timerEl.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    
    if (secondsRemaining <= 0) {
      clearInterval(timerInterval);
      resolvePendingApproval(false, true); // Expired rejection
    }
    secondsRemaining--;
  }, 1000);
}

function resolvePendingApproval(isApproved, isExpired = false) {
  if (timerInterval) clearInterval(timerInterval);
  document.getElementById('approvalCard').style.display = 'none';

  if (!pendingActionData) return;

  appendBlockToLedger({
    tool: pendingActionData.tool,
    action: pendingActionData.action,
    risk: pendingActionData.risk,
    status: isApproved ? '2FA_APPROVED_HMAC' : (isExpired ? 'REJECTED_EXPIRED' : 'REJECTED_BY_ADMIN'),
    nonce: pendingActionData.nonce
  });

  pendingActionData = null;
}

function appendBlockToLedger(data) {
  const prevBlock = auditLedger[auditLedger.length - 1];
  const newIndex = auditLedger.length + 1;
  const prevHash = prevBlock.hash;
  
  // Deterministic-like SHA-256 simulation
  const newHash = Array.from({length: 64}, () => Math.floor(Math.random()*16).toString(16)).join('');
  const now = new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC';

  auditLedger.unshift({
    block: newIndex,
    time: now,
    tool: data.tool,
    action: data.action,
    risk: data.risk,
    prevHash: prevHash,
    hash: newHash,
    status: data.status,
    nonce: data.nonce
  });

  renderAuditLedger();

  const countBadge = document.getElementById('blockCountBadge');
  if (countBadge) {
    countBadge.textContent = `${auditLedger.length} Blocks Sealed`;
  }
}

function renderAuditLedger() {
  const container = document.getElementById('hashChainContainer');
  if (!container) return;

  container.innerHTML = auditLedger.map((b, i) => {
    const isApproved = b.status.includes('APPROVED');
    const badgeColor = isApproved ? 'bg-green' : 'highlight-red';

    return `
      <div class="hash-block" style="animation: fadeIn 0.3s ease;">
        <div class="hash-block-header">
          <span class="block-index">Block #${b.block} &bull; ${b.tool}</span>
          <span class="block-time">${b.time}</span>
        </div>
        <div class="block-payload">
          <strong>Action:</strong> ${b.action} &bull; 
          <span class="badge-pill ${badgeColor}">${b.status}</span>
        </div>
        <div class="block-hashes">
          <div class="hash-row">
            <span class="hash-lbl">Prev Hash:</span>
            <span class="hash-str">${b.prevHash.substring(0, 32)}...</span>
          </div>
          <div class="hash-row">
            <span class="hash-lbl">Block Hash:</span>
            <span class="hash-str" style="color: var(--accent-purple); font-weight: 600;">${b.hash.substring(0, 32)}...</span>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

/* =========================================================================
   5. OpenAPI REST API Explorer & Mock Console (Module 4)
   ========================================================================= */
const endpointConfigs = {
  'post-query': {
    method: 'POST',
    path: '/api/v1/query',
    status: 'HTTP 200 OK',
    time: '8.1 ms',
    payload: `{\n  "tenant_id": "healthcare_corp",\n  "user_role": "user",\n  "query": "What is the surgical device sterilisation protocol?",\n  "top_k": 3\n}`,
    curl: `curl -X POST "https://api.eig.internal/api/v1/query" \\\n  -H "Content-Type: application/json" \\\n  -H "Authorization: Bearer <JWT_TOKEN>" \\\n  -d '{"tenant_id":"healthcare_corp","query":"What is the surgical device sterilisation protocol?","top_k":3}'`,
    response: `{\n  "status": "success",\n  "tenant_id": "healthcare_corp",\n  "answer": "Surgical devices must undergo high-pressure steam autoclaving at 134°C for a minimum duration of 18 minutes, followed by vacuum drying.",\n  "citations": [\n    {\n      "document_id": "doc_hc_sterilisation_v2.pdf",\n      "page": 4,\n      "paragraph": 2,\n      "relevance_score": 0.948\n    }\n  ],\n  "hybrid_scores": {\n    "bm25_lexical": 0.891,\n    "dense_vector": 0.915,\n    "cross_encoder_rerank": 0.948\n  },\n  "execution_time_ms": 8.1\n}`
  },
  'post-action': {
    method: 'POST',
    path: '/api/v1/agent/action',
    status: 'HTTP 202 Accepted',
    time: '12.4 ms',
    payload: `{\n  "agent_id": "agent_react_01",\n  "tool_name": "crm_issue_refund",\n  "parameters": {\n    "customer_id": "cust_4892",\n    "amount_usd": 45000.00\n  }\n}`,
    curl: `curl -X POST "https://api.eig.internal/api/v1/agent/action" \\\n  -H "Content-Type: application/json" \\\n  -H "Authorization: Bearer <JWT_TOKEN>" \\\n  -d '{"tool_name":"crm_issue_refund","parameters":{"customer_id":"cust_4892","amount_usd":45000}}'`,
    response: `{\n  "action_id": "act_8f7b3a9c",\n  "status": "PENDING_APPROVAL",\n  "risk_score": 0.95,\n  "nonce": "0x9a8b7c6d5e4f3a2b",\n  "hmac_signature": "f47a8c3d9b0e1f2a4c5e6f7a8b9c0d1e2f3a4b5c6d7e8f90123456789a2b3c4d",\n  "expires_at": "2026-10-25T16:50:00Z",\n  "message": "Risk threshold exceeded (> 0.70). Two-phase cryptographic approval required."\n}`
  },
  'post-approve': {
    method: 'POST',
    path: '/api/v1/agent/approve',
    status: 'HTTP 200 OK',
    time: '9.2 ms',
    payload: `{\n  "action_id": "act_8f7b3a9c",\n  "approved": true,\n  "approver_role": "admin",\n  "hmac_token": "f47a8c3d9b0e1f2a4c5e6f7a8b9c0d1e2f3a4b5c6d7e8f90123456789a2b3c4d"\n}`,
    curl: `curl -X POST "https://api.eig.internal/api/v1/agent/approve" \\\n  -H "Content-Type: application/json" \\\n  -H "Authorization: Bearer <ADMIN_JWT_TOKEN>" \\\n  -d '{"action_id":"act_8f7b3a9c","approved":true,"approver_role":"admin"}'`,
    response: `{\n  "action_id": "act_8f7b3a9c",\n  "status": "EXECUTED",\n  "decision": "APPROVED",\n  "audit_block_index": 5,\n  "audit_block_hash": "b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef012",\n  "execution_result": "Refund voucher #RF-45000 successfully dispatched."\n}`
  },
  'post-ingest': {
    method: 'POST',
    path: '/api/v1/ingest',
    status: 'HTTP 201 Created',
    time: '42.6 ms',
    payload: `{\n  "tenant_id": "healthcare_corp",\n  "file_name": "device_manual_v3.pdf",\n  "content_type": "application/pdf",\n  "vector_store": "qdrant"\n}`,
    curl: `curl -X POST "https://api.eig.internal/api/v1/ingest" \\\n  -F "file=@device_manual_v3.pdf" \\\n  -F "tenant_id=healthcare_corp"`,
    response: `{\n  "status": "ingested",\n  "document_id": "doc_a982f1bc",\n  "tenant_id": "healthcare_corp",\n  "chunks_created": 34,\n  "vector_store": "qdrant",\n  "sha256_hash": "3f79bb7b435b05321651daefd374cd681b61935c13e0e77ec0ec23f886429c3d",\n  "elapsed_ms": 42.6\n}`
  },
  'get-metrics': {
    method: 'GET',
    path: '/metrics',
    status: 'HTTP 200 OK',
    time: '1.4 ms',
    payload: `// No body required for GET /metrics`,
    curl: `curl -X GET "https://api.eig.internal/metrics"`,
    response: `# HELP eig_query_latency_seconds Latency of RAG queries\n# TYPE eig_query_latency_seconds histogram\neig_query_latency_seconds_bucket{le="0.005"} 14\neig_query_latency_seconds_bucket{le="0.010"} 68\neig_query_latency_seconds_sum 0.739\neig_query_latency_seconds_count 100\n\n# HELP eig_tenant_access_denied_total Unauthorized cross-tenant queries\n# TYPE eig_tenant_access_denied_total counter\neig_tenant_access_denied_total{attempted_tenant="fintech_ltd",source_tenant="healthcare_corp"} 12`
  },
  'get-health': {
    method: 'GET',
    path: '/health/ready',
    status: 'HTTP 200 OK',
    time: '0.8 ms',
    payload: `// No body required for GET /health/ready`,
    curl: `curl -X GET "https://api.eig.internal/health/ready"`,
    response: `{\n  "status": "ready",\n  "version": "1.0.0",\n  "vector_stores": {\n    "chromadb": "online",\n    "qdrant": "online"\n  },\n  "audit_ledger": {\n    "integrity": "verified",\n    "blocks": 4\n  }\n}`
  }
};

function initApiExplorer() {
  const endpointBtns = document.querySelectorAll('.endpoint-btn');
  const payloadEditor = document.getElementById('apiPayloadEditor');
  const btnSend = document.getElementById('btnSendApiRequest');
  const statusBadge = document.getElementById('apiResponseStatus');
  const timeLbl = document.getElementById('apiResponseTime');
  const curlCode = document.getElementById('apiCurlCode');
  const jsonCode = document.getElementById('apiResponseJson');
  const btnCopyCurl = document.getElementById('btnCopyCurl');

  let activeEndpointKey = 'post-query';

  endpointBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      endpointBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      activeEndpointKey = btn.getAttribute('data-endpoint');
      const cfg = endpointConfigs[activeEndpointKey];
      if (cfg) {
        payloadEditor.value = cfg.payload;
        curlCode.textContent = cfg.curl;
        jsonCode.textContent = cfg.response;
        statusBadge.textContent = cfg.status;
        timeLbl.textContent = `Latency: ${cfg.time}`;
      }
    });
  });

  btnSend.addEventListener('click', () => {
    const cfg = endpointConfigs[activeEndpointKey];
    if (!cfg) return;

    statusBadge.textContent = 'Executing...';
    jsonCode.textContent = '// Sending HTTP payload to gateway...';

    setTimeout(() => {
      statusBadge.textContent = cfg.status;
      jsonCode.textContent = cfg.response;
      timeLbl.textContent = `Latency: ${(parseFloat(cfg.time) + (Math.random() * 2 - 1)).toFixed(1)} ms`;
    }, 200);
  });

  btnCopyCurl.addEventListener('click', () => {
    const textToCopy = curlCode.textContent;
    navigator.clipboard.writeText(textToCopy).then(() => {
      const originalText = btnCopyCurl.textContent;
      btnCopyCurl.textContent = 'Copied!';
      setTimeout(() => {
        btnCopyCurl.textContent = originalText;
      }, 1500);
    });
  });
}
